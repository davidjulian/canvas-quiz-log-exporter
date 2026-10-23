"""Loopback-only web interface for the local Canvas New Quizzes collector.

No web hosting, AI service, API token, analytics or third-party web assets.
Playwright and its browser context are owned by one dedicated worker thread.
"""
import argparse
import csv
import hmac
import json
import os
import secrets
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import quick_capture as capture
from coded_export import CodedExport, NamedExport

ROOT = Path(__file__).resolve().parent
DEFAULT_URL = "https://ufl.instructure.com/"
READINESS = "Elapsed time"
TERMINAL = {"idle", "complete", "stopped", "error"}
ERRORS = {
    "no_unambiguous_moderate_tab_found": "No single Moderate list was found. Open Moderate in the dedicated Canvas window, wait for it to load, and try again.",
    "multiple_moderate_tabs": "More than one tab has a Moderate list. Keep just the tab you want open in the dedicated Canvas window, then try again.",
    "moderate_list_changed": "The Moderate list changed after your review. Saved files are preserved. Begin a new run and review the current list.",
    "back_did_not_restore_the_same_moderate_page": "Back did not restore the same Moderate list. Saved files are preserved; check them before beginning a new run.",
    "log_did_not_become_ready_and_stable": "The log did not finish loading with ‘Elapsed time’ visible. Check the Canvas page and begin a new run.",
    "readiness_phrase_is_empty_or_already_on_moderate": "‘Elapsed time’ was already on Moderate. This page needs a different readiness check; no further logs were collected.",
    "log_start_began_not_found_or_ambiguous": "A single ‘Began …’ line could not be found. Collection stopped instead of guessing where the log starts.",
    "new_tab_navigation_not_supported": "This version requires View Log to open in the same tab. Saved files are preserved.",
    "duplicate_log_text_needs_local_review": "A repeated capture for the same control needs local review. Collection stopped.",
    "browser_or_tab_closed": "The Canvas browser or tab was closed. Any completed files are preserved.",
    "required_student_name_missing_or_too_long": "Every student name must contain 1 to 200 characters. Correct the name review before starting.",
    "PermissionError": "The app could not access a local folder or file. Check folder permissions and whether another program has the file open.",
    "browser_launch_failed": "The dedicated browser could not open. Close any earlier exporter window using this profile. Check that your selected browser is installed.",
    "archive_failed": "Text files were preserved, but the ZIP could not be completed. Check the output folder and available space.",
}


class UIError(Exception):
    """Fixed, safe messages suitable for the local interface."""


def validate_url(value):
    if not isinstance(value, str) or len(value) > 2048 or any(ord(c) < 33 for c in value):
        raise UIError("Enter a valid HTTPS Canvas address without spaces.")
    try:
        parsed = urlsplit(value)
        parsed.port
    except ValueError:
        raise UIError("Enter a valid HTTPS Canvas address.") from None
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment):
        raise UIError("Use your HTTPS Canvas home address without sign-in tokens, query parameters or fragments.")
    return value


def profile_folder():
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "CanvasQuizExporter" / "BrowserProfile"
    base = os.environ.get("LOCALAPPDATA")
    return (Path(base) if base else Path.home() / ".local" / "share") / "CanvasQuizExporter" / "BrowserProfile"


def open_path(path):
    if sys.platform == "darwin":
        try:
            subprocess.run(["/usr/bin/open", str(path.resolve())], check=True,
                           capture_output=True, timeout=15)
        except (OSError, subprocess.SubprocessError):
            raise UIError("The file could not open. Open the displayed output path in Finder.") from None
    elif os.name == "nt":
        os.startfile(str(path))
    else:
        raise UIError("Open the displayed output path in your file manager.")


def output_folder(value, profile):
    if not isinstance(value, str) or not value.strip() or len(value) > 3000:
        raise UIError("Choose an existing output folder.")
    try:
        base = Path(value).expanduser().resolve()
        private = profile.resolve()
        if not base.is_dir():
            raise UIError("Choose an existing output folder. The app creates a new run folder inside it.")
        if base == private or base.is_relative_to(private) or private.is_relative_to(base):
            raise UIError("Choose an output folder separate from the browser profile.")
    except (OSError, ValueError):
        raise UIError("That output folder could not be opened. Choose another existing folder.") from None
    return base / ("quiz-logs-" + datetime.now().strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(3))


class LocalApp:
    def __init__(self, profile=None):
        self.profile = Path(profile) if profile else profile_folder()
        self.condition = threading.Condition(threading.RLock())
        self.stop_event = threading.Event()
        self.worker = None
        self.pending = None
        self.dialog_lock = threading.Lock()
        self.state = {"phase": "idle", "saved": 0, "total": 0, "names": [], "output": "",
                      "first_file": "", "archive_ready": False, "warning_count": 0,
                      "key_ready": False, "export_mode": "coded",
                      "default_browser": "chrome" if sys.platform == "darwin" else "msedge",
                      "error": "", "run_id": "", "version": capture.VERSION}

    def snapshot(self):
        with self.condition:
            # Copies prevent an HTTP request modifying shared worker state.
            return json.loads(json.dumps(self.state))

    def update(self, **values):
        with self.condition:
            self.state.update(values)

    def check_cancel(self):
        if self.stop_event.is_set():
            raise capture.CaptureError("stopped_by_user")

    def await_action(self, phase, **values):
        with self.condition:
            self.pending = None
            self.state.update(phase=phase, **values)
            while self.pending is None:
                self.check_cancel()
                self.condition.wait(.25)
            action = self.pending
            self.pending = None
            self.check_cancel()
            return action

    def command(self, action, payload):
        with self.condition:
            if action == "launch":
                if self.worker and self.worker.is_alive():
                    raise UIError("A run is already active. Finish it or stop it before opening another.")
                url = validate_url(payload.get("url"))
                channel = payload.get("browser", self.state["default_browser"])
                if channel not in ("msedge", "chrome"):
                    raise UIError("Choose Microsoft Edge or Google Chrome.")
                mode = payload.get("export_mode", "coded")
                if mode not in ("coded", "named"):
                    raise UIError("Choose coded logs or named logs.")
                out = output_folder(payload.get("output"), self.profile)
                self.stop_event.clear()
                self.state.update(phase="opening", saved=0, total=0, names=[], output=str(out),
                                  first_file="", archive_ready=False, warning_count=0, error="",
                                  key_ready=False, export_mode=mode, run_id=secrets.token_hex(8))
                # A quit during a browser operation must allow cleanup and ZIP
                # preservation to finish even after the HTTP listener closes.
                self.worker = threading.Thread(target=self.run, args=(url, out, channel, mode), daemon=False)
                self.worker.start()
                return {}
            if action == "stop":
                if self.state["phase"] not in TERMINAL:
                    self.stop_event.set()
                    self.state["phase"] = "stopping"
                    self.condition.notify_all()
                return {}
            expected = {"moderate": "navigate", "start": "review", "checked": "checking"}
            if action not in expected or self.state["phase"] != expected[action] or self.pending is not None:
                raise UIError("That step is no longer waiting for input. Use the current buttons.")
            if payload.get("run_id") != self.state["run_id"]:
                raise UIError("This is an older run. Refresh the page before continuing.")
            if action == "start":
                if payload.get("reviewed") is not True:
                    raise UIError("Check the name review box before starting.")
                rows = payload.get("names")
                if not isinstance(rows, list) or len(rows) != self.state["total"]:
                    raise UIError("The name list does not match this Moderate page.")
                names = []
                for index, row in enumerate(rows):
                    if (not isinstance(row, dict) or row.get("position") != index + 1
                            or not isinstance(row.get("name"), str)):
                        raise UIError("Keep student positions in their original order.")
                    name = capture.normalize_name(row["name"])
                    if not name or len(name) > 200:
                        raise UIError("Every student name must contain 1 to 200 characters.")
                    names.append({"position": index + 1, "name": name})
                payload = {"names": names}
            self.pending = (action, payload)
            self.state["phase"] = {"moderate": "finding", "start": "capturing", "checked": "capturing"}[action]
            self.condition.notify_all()
            return {}

    def run(self, url, out, channel, mode="coded"):
        collector, context = None, None
        final_phase, error_message = "complete", ""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as playwright:
                try:
                    try:
                        context = playwright.chromium.launch_persistent_context(
                            str(self.profile), channel=channel, headless=False, accept_downloads=False)
                    except Exception:
                        raise capture.CaptureError("browser_launch_failed") from None
                    context.set_default_timeout(10000)
                    page = context.pages[0] if context.pages else context.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    self.await_action("navigate")
                    def one_tab_only(_):
                        raise capture.CaptureError("multiple_moderate_tabs")
                    page = capture.choose_moderate_page(context, prompt=one_tab_only, check_cancel=self.check_cancel)
                    collector = WebCapture(page, out, self, mode=mode)
                    collector.run()
                    self.check_cancel()
                finally:
                    if context:
                        try:
                            context.close()
                        except Exception:
                            pass
        except Exception as error:
            category = str(error) if isinstance(error, capture.CaptureError) else (
                "PermissionError" if isinstance(error, PermissionError) else capture.safe_error_category(error))
            if category == "stopped_by_user" or self.stop_event.is_set():
                final_phase = "stopped"
            else:
                final_phase = "error"
                error_message = ERRORS.get(category, "Collection stopped. Check the dedicated browser and your output folder. Any completed files are preserved.")
        finally:
            self.update(phase="finishing")
            if collector:
                try:
                    collector.bundle()
                    self.update(archive_ready=True)
                except Exception:
                    final_phase, error_message = "error", ERRORS["archive_failed"]
            self.update(phase=final_phase, error=error_message)

    def browse(self):
        if not self.dialog_lock.acquire(blocking=False):
            raise UIError("A folder chooser is already open. Check your desktop.")
        try:
            if sys.platform == "darwin":
                # AppKit/Tk dialogs cannot run on an HTTP worker thread on macOS.
                # A separate native process owns the dialog; no student text is
                # interpolated into AppleScript or passed to a shell.
                result = subprocess.run(["/usr/bin/osascript", "-e", '''try
return POSIX path of (choose folder with prompt "Choose approved storage for quiz log exports")
on error number -128
return ""
end try'''], capture_output=True, text=True, check=True, timeout=300)
                return {"folder": result.stdout.rstrip("\r\n")}
            import tkinter
            from tkinter import filedialog
            root = tkinter.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            try:
                selected = filedialog.askdirectory(parent=root, title="Choose approved storage for quiz log exports", mustexist=True)
            finally:
                root.destroy()
            return {"folder": selected or ""}
        except Exception:
            raise UIError("The folder chooser could not open. Paste an existing folder path into the output field.") from None
        finally:
            self.dialog_lock.release()

    def open_local(self, first=False, key=False):
        state = self.snapshot()
        out = Path(state["output"])
        if not state["output"] or not out.is_dir():
            raise UIError("The output folder will be available after the Moderate list is found.")
        path = out / state["first_file"] if first and state["first_file"] else out
        if key:
            if not state["key_ready"]:
                raise UIError("The private name key will be available after you review the names and start.")
            path = out / "private" / "name_key.csv"
        if not path.exists():
            raise UIError("That local file is no longer available.")
        open_path(path)
        return {}


class WebCapture(capture.QuickCapture):
    def __init__(self, page, out, app, settle=3, mode="coded"):
        if mode not in ("coded", "named"):
            raise ValueError("invalid_export_mode")
        self.app = app
        self.mode = mode
        self.run_out = Path(out)
        self.run_out.mkdir(parents=True, exist_ok=False)
        self.record_ids = {}
        self.downloads = CodedExport(self.run_out) if mode == "coded" else NamedExport(self.run_out)
        super().__init__(page, self.run_out / "private", settle=settle, check_cancel=app.check_cancel, trim_menu=True)
        self.manifest["interface"] = "local_web_app"
        self.manifest["export_mode"] = mode
        self.manifest["text_cleanup"] = "Starts at Began; " + ("coded copies omit identifiers." if mode == "coded" else "names and original dates/times are retained.")
        self.manifest["privacy"] = ("Private records and name key are excluded from the coded downloads ZIP." if mode == "coded"
                                    else "Named downloads contain identified education records; no name key is created.")
        self.checkpoint()

    def prepare_names(self, controls, positions=None):
        super().prepare_names(controls, positions)
        for index in self.proposed_names if self.mode == "coded" else ():
            while True:
                record_id = "R-" + secrets.token_hex(8)
                if record_id not in self.record_ids.values():
                    self.record_ids[index] = record_id
                    break
        self.app.update(total=len(controls), names=[{"position": i + 1, "name": name}
                        for i, (name, _) in self.proposed_names.items()])

    def confirm_start(self):
        _, payload = self.app.await_action("review")
        with (self.out / "names.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("control_position", "student_name", "proposed_source"))
            writer.writeheader()
            for row in payload["names"]:
                index, value = row["position"] - 1, row["name"]
                original, source = self.proposed_names[index]
                # Preserve edited formula-leading names exactly; the leading
                # apostrophe protects CSV readers and is unwrapped on load.
                self.proposed_names[index] = (value, source if value == original else "locally_edited")
                writer.writerow({"control_position": index + 1, "student_name": capture.csv_name(value),
                                 "proposed_source": self.proposed_names[index][1]})
        return True

    def load_reviewed_names(self, required_positions=None):
        super().load_reviewed_names(required_positions)
        if self.mode == "coded":
            self.write_name_key()

    def write_name_key(self):
        temporary = self.out / "name_key.csv.tmp"
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("record_id", "control_position", "student_name", "name_source"))
            writer.writeheader()
            for index, (name, source) in sorted(self.names.items()):
                writer.writerow({"record_id": self.record_ids[index], "control_position": index + 1,
                                 "student_name": capture.csv_name(name), "name_source": source})
        temporary.replace(self.out / "name_key.csv")
        self.app.update(key_ready=True)

    def file_content(self, index, text, student):
        if self.mode == "named":
            return super().file_content(index, text, student)
        first, _, rest = capture.log_from_began(text).partition("\n")
        record_id = self.record_ids[index]
        # Full captured text can still contain identifiers: keep it private.
        return f"log_{record_id}.txt", f"{first}\nRecord ID: {record_id}\n\n{rest}"

    def get_readiness_phrase(self):
        return READINESS

    def confirm_first_capture(self):
        self.app.await_action("checking")
        return True

    def save(self, index, text, signature):
        self.app.check_cancel()
        super().save(index, text, signature)
        records = self.manifest["saved_logs"]
        if self.mode == "coded":
            record_id = self.record_ids[index]
            records[-1]["record_id"] = record_id
            self.downloads.add_record(record_id, text, names=[name for name, _ in self.names.values()])
        else:
            record = records[-1]
            self.downloads.add_named_record(record["file"], (self.out / record["file"]).read_text(encoding="utf-8"))
        self.checkpoint()
        first_file = "logs/" + records[0]["file"]
        self.app.update(saved=len(records), first_file=first_file,
                        warning_count=sum(r["same_page_text_as_another_control"] for r in records))

    def bundle(self):
        self.downloads.bundle()


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, app, port=0):
        self.app = app
        self.token = secrets.token_urlsafe(32)
        super().__init__(("127.0.0.1", port), Handler)
        self.origin = f"http://127.0.0.1:{self.server_port}"
        self.host = f"127.0.0.1:{self.server_port}"

    @property
    def url(self):
        return self.origin + "/#" + self.token


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Never log paths, names, tokens, request bodies or page text.

    def send_error(self, code, message=None, explain=None):
        self.reply(code, b"Request could not be completed.", "text/plain; charset=utf-8")

    def reply(self, code, data, content_type="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def json_reply(self, value, status=200):
        self.reply(status, json.dumps(value, ensure_ascii=True).encode("utf-8"))

    def reject(self):
        # Consume a small rejected POST body so closing the connection does not
        # reset it before Windows clients receive the 403 response. Never parse
        # or log rejected data; limit both size and waiting time.
        if self.command == "POST":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if 0 < length <= 65536:
                    previous = self.connection.gettimeout()
                    try:
                        self.connection.settimeout(1)
                        self.rfile.read(length)
                    finally:
                        self.connection.settimeout(previous)
            except (OSError, ValueError):
                pass
        self.send_error(403)
        return False

    def allowed(self, api=False):
        if self.headers.get("Host") != self.server.host:
            return self.reject()
        origin = self.headers.get("Origin")
        if origin is not None and origin != self.server.origin:
            return self.reject()
        if api:
            supplied = self.headers.get("Authorization", "")
            expected = "Bearer " + self.server.token
            if not hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8")):
                return self.reject()
            if self.command == "POST" and origin != self.server.origin:
                return self.reject()
        return True

    def do_GET(self):
        if not self.allowed(api=self.path.startswith("/api/")):
            return
        assets = {"/": ("index.html", "text/html; charset=utf-8"),
                  "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                  "/style.css": ("style.css", "text/css; charset=utf-8")}
        if self.path in assets:
            name, mime = assets[self.path]
            self.reply(200, (ROOT / "web" / name).read_bytes(), mime)
        elif self.path == "/api/state":
            self.json_reply(self.server.app.snapshot())
        else:
            self.send_error(404)

    def do_POST(self):
        if not self.allowed(api=True):
            return
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            self.send_error(415)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1024 * 1024:
                raise ValueError()
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError()
        except (ValueError, UnicodeDecodeError):
            self.send_error(400)
            return
        try:
            app = self.server.app
            if self.path == "/api/action":
                result = app.command(payload.get("action"), payload)
            elif self.path == "/api/browse":
                result = app.browse()
            elif self.path == "/api/open-folder":
                result = app.open_local()
            elif self.path == "/api/open-first":
                result = app.open_local(first=True)
            elif self.path == "/api/open-key":
                result = app.open_local(key=True)
            elif self.path == "/api/quit":
                app.stop_event.set()
                with app.condition:
                    app.condition.notify_all()
                result = {}
                threading.Thread(target=self.server.shutdown, daemon=True).start()
            else:
                self.send_error(404)
                return
            self.json_reply(result)
        except UIError as error:
            self.json_reply({"error": str(error)}, 400)
        except Exception:
            self.json_reply({"error": "That action could not finish. Check your local folder and browser."}, 500)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-open", action="store_true", help="Print the local address without opening it")
    args = parser.parse_args()
    app = LocalApp()
    server = LocalServer(app)
    if args.no_open:
        print(server.url)
    else:
        webbrowser.open(server.url)
    try:
        server.serve_forever(poll_interval=.25)
    except KeyboardInterrupt:
        pass
    finally:
        app.stop_event.set()
        with app.condition:
            app.condition.notify_all()
        if app.worker:
            app.worker.join(timeout=45)
        server.server_close()


if __name__ == "__main__":
    main()
