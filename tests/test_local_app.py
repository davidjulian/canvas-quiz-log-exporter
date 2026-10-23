"""Synthetic local UI, HTTP privacy boundary and collector integration tests."""
import http.client
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import local_app as web
import quick_capture as capture


class LocalLogicTests(unittest.TestCase):
    def test_invalid_export_mode_is_rejected_before_starting_browser(self):
        app = web.LocalApp()
        with tempfile.TemporaryDirectory() as temp, self.assertRaisesRegex(web.UIError, "coded logs or named logs"):
            app.command("launch", {"url": web.DEFAULT_URL, "output": temp, "export_mode": "unsupported"})
        self.assertIsNone(app.worker)
    def test_only_https_home_addresses(self):
        self.assertEqual(web.validate_url(web.DEFAULT_URL), web.DEFAULT_URL)
        for address in ("http://canvas.invalid", "https://user:secret@canvas.invalid/",
                        "https://canvas.invalid/?token=secret", "https://canvas.invalid/#token",
                        "https://canvas.invalid:broken", "https://canvas.invalid/\nsecret", None):
            with self.subTest(address=address), self.assertRaises(web.UIError):
                web.validate_url(address)

    def test_began_cleanup_keeps_all_following_events(self):
        text = "=== Visible document 1 ===\nDashboard\nInbox\nSkip To Quiz Content\nBegan Tuesday, September 29 at 11:46 AM\nElapsed time\n00:00 Started\n00:10 Stopped viewing\n00:30 Resumed\n"
        self.assertEqual(capture.log_from_began(text), "Began Tuesday, September 29 at 11:46 AM\nElapsed time\n00:00 Started\n00:10 Stopped viewing\n00:30 Resumed")
        for bad in ("Dashboard\nNo log yet", "Began first\nBegan another"):
            with self.assertRaisesRegex(capture.CaptureError, "log_start_began"):
                capture.log_from_began(bad)

    def test_output_never_overwrites_and_excludes_profile_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            profile = base / "private" / "profile"
            profile.mkdir(parents=True)
            approved = base / "approved"
            approved.mkdir()
            first = web.output_folder(str(approved), profile)
            second = web.output_folder(str(approved), profile)
            self.assertNotEqual(first, second)
            self.assertEqual(first.parent, approved)
            self.assertFalse(first.exists())
            for forbidden in (base, profile, profile.parent):
                with self.assertRaises(web.UIError):
                    web.output_folder(str(forbidden), profile)

    def test_names_and_stale_run_validated_before_start(self):
        app = web.LocalApp()
        app.update(phase="review", total=2, run_id="current")
        for payload in ({"run_id": "old", "reviewed": True, "names": []},
                        {"run_id": "current", "reviewed": False, "names": []},
                        {"run_id": "current", "reviewed": True, "names": [{"position": 1, "name": "Only one"}]},
                        {"run_id": "current", "reviewed": True, "names": [{"position": 1, "name": ""}, {"position": 2, "name": "Other"}]}):
            with self.assertRaises(web.UIError):
                app.command("start", payload)
        self.assertEqual(app.snapshot()["phase"], "review")
        app.command("start", {"run_id": "current", "reviewed": True, "names": [
            {"position": 1, "name": "Synthetic Student"}, {"position": 2, "name": "=Synthetic Example"}]})
        self.assertEqual(app.pending[1]["names"][1]["name"], "=Synthetic Example")
        with self.assertRaises(web.UIError):
            app.command("start", {})

    def test_stop_releases_waiting_worker(self):
        app = web.LocalApp()
        seen = []
        def wait():
            try:
                app.await_action("checking")
            except capture.CaptureError as error:
                seen.append(str(error))
        thread = threading.Thread(target=wait)
        thread.start()
        for _ in range(100):
            if app.snapshot()["phase"] == "checking":
                break
            time.sleep(.01)
        app.command("stop", {})
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(seen, ["stopped_by_user"])

    def test_cancel_reaches_loading_waits(self):
        def cancelled():
            raise capture.CaptureError("stopped_by_user")
        for call in (lambda: capture.wait_log(None, "Elapsed time", "", check_cancel=cancelled),
                     lambda: capture.wait_list(None, (), check_cancel=cancelled),
                     lambda: capture.choose_moderate_page(None, check_cancel=cancelled)):
            with self.assertRaisesRegex(capture.CaptureError, "stopped_by_user"):
                call()


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.app = web.LocalApp()
        self.server = web.LocalServer(self.app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def authorization(self):
        return {"Authorization": "Bearer " + self.server.token, "Origin": self.server.origin,
                "Content-Type": "application/json"}

    def test_only_loopback_and_authenticated_state(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        self.app.update(names=[{"name": "SYNTHETIC_PRIVATE_MARKER"}])
        status, headers, body = self.request("GET", "/api/state")
        self.assertEqual(status, 403)
        self.assertNotIn(b"SYNTHETIC_PRIVATE_MARKER", body)
        status, headers, body = self.request("GET", "/api/state", headers=self.authorization())
        self.assertEqual(status, 200)
        self.assertIn(b"SYNTHETIC_PRIVATE_MARKER", body)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Frame-Options"], "DENY")

    def test_foreign_origin_host_missing_origin_and_wrong_token_rejected(self):
        cases = [dict(self.authorization(), Origin="https://foreign.invalid"),
                 dict(self.authorization(), Host="foreign.invalid"),
                 dict(self.authorization(), Authorization="Bearer wrong"),
                 {k: v for k, v in self.authorization().items() if k != "Origin"}]
        for headers in cases:
            with self.subTest(headers=headers):
                self.assertEqual(self.request("POST", "/api/action", '{"action":"stop"}', headers)[0], 403)

    def test_no_filesystem_serving_or_request_reflection(self):
        for path in ("/quick_capture.py", "/manifest.json", "/../README.md", "/api/state?secret=test", "/web/index.html"):
            status, _, body = self.request("GET", path, headers=self.authorization())
            self.assertEqual(status, 404)
            self.assertNotIn(path.encode(), body)
        status, headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Canvas Quiz Log Exporter", body)
        self.assertIn("connect-src 'self'", headers["Content-Security-Policy"])

    def test_malformed_and_non_json_posts_rejected(self):
        for body in ("[]", "broken json", ""):
            self.assertEqual(self.request("POST", "/api/action", body, self.authorization())[0], 400)
        headers = dict(self.authorization(), **{"Content-Type": "text/plain"})
        self.assertEqual(self.request("POST", "/api/action", "{}", headers)[0], 415)


FIXTURE = '''<!doctype html><html><body><nav>Dashboard Inbox Courses</nav><main></main><script>
function draw(){
 const n=Number(location.hash.replace('#log-',''));
 if(n){document.querySelector('main').innerHTML=`<p>Back to Moderate</p><h1>Log of student taking events</h1><p>Began Tuesday, September 29, 2026 at 11:46 AM</p><p>Finished Tuesday, September 29, 2026 at 12:20 PM</p><h2>Elapsed time</h2><p>00:00 Session started.</p><p>00:10 Stopped viewing the Canvas quiz-taking page...</p><p>00:30 Resumed.</p><p>00:40 Quiz submitted.</p><p>00:50 Synthetic private final event ${n}</p>`;}
 else{document.querySelector('main').innerHTML='<h1>Moderate synthetic quiz</h1><table>'+[1,2,3].map(n=>`<tr><td>Synthetic student ${n}</td><td><a href="#log-${n}" onclick="event.preventDefault();history.pushState({},\'\',this.href);draw()">View Log</a></td></tr>`).join('')+'</table>';}
}window.addEventListener('popstate',draw);draw();</script></body></html>'''


@unittest.skipUnless(os.environ.get("CANVAS_RUN_BROWSER_TESTS") == "1", "optional synthetic local browser tests")
class BrowserUITests(HTTPTests):
    # HTTP boundary tests are inherited and also run with this fixture server.
    def setUp(self):
        super().setUp()
        from playwright.sync_api import sync_playwright
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True, channel=os.environ.get("CANVAS_TEST_BROWSER", "msedge" if sys.platform == "win32" else "chrome"))
        self.context = self.browser.new_context()
        self.context.route("**/*", lambda route: route.continue_()
                           if route.request.url.startswith(self.server.origin + "/") else route.abort())
        self.page = self.context.new_page()
        self.page.goto(self.server.url)
        self.temp = tempfile.TemporaryDirectory()
        self.app.profile = Path(self.temp.name) / "profile"
        self.output = Path(self.temp.name) / "approved-output"
        self.output.mkdir()

    def tearDown(self):
        self.app.command("stop", {})
        if self.app.worker:
            self.app.worker.join(30)
        self.context.close()
        self.browser.close()
        self.playwright.stop()
        super().tearDown()
        self.temp.cleanup()

    def assert_phase(self, phase, timeout=30000):
        self.page.wait_for_function("phase => document.getElementById('status').textContent === phase", arg={
            "navigate": "Your turn", "review": "Your turn", "checking": "Your turn",
            "complete": "Finished", "stopped": "Stopped"}[phase], timeout=timeout)
        deadline = time.monotonic() + timeout / 1000
        while self.app.snapshot()["phase"] != phase and time.monotonic() < deadline:
            self.page.wait_for_timeout(50)
        self.assertEqual(self.app.snapshot()["phase"], phase)

    def launch_synthetic(self, mode="coded"):
        from playwright.sync_api import BrowserType
        original = BrowserType.launch_persistent_context
        def launch(browser_type, user_data_dir, **kwargs):
            context = original(browser_type, user_data_dir, channel=os.environ.get("CANVAS_TEST_BROWSER", "msedge" if sys.platform == "win32" else "chrome"), headless=True, accept_downloads=False)
            context.route("**/*", lambda route: route.fulfill(status=200, content_type="text/html", body=FIXTURE)
                          if route.request.url.split('#')[0] == "https://canvas-fixture.invalid/" else route.abort())
            return context
        self.launch_patch = patch.object(BrowserType, "launch_persistent_context", launch)
        self.launch_patch.start()
        self.addCleanup(self.launch_patch.stop)
        self.page.locator("#canvas-url").fill("https://canvas-fixture.invalid/")
        self.page.locator("#output").fill(str(self.output))
        self.assertTrue(self.page.locator("#mode-coded").is_checked())
        if mode == "named":
            self.page.locator("#mode-named").check()
        self.page.locator("#launch").click()
        self.page.locator("#moderate").wait_for(state="visible")
        self.assert_phase("navigate")
        self.assertIn("then go to Build → Moderate", self.page.locator("#navigate").inner_text())
        self.assertTrue(self.page.locator("#mode-named").is_disabled())
        self.page.locator("#moderate").click()
        self.page.locator("#name-rows input").nth(2).wait_for()
        self.assert_phase("review")

    def test_entire_web_workflow_coded_files_and_private_key(self):
        self.launch_synthetic()
        self.assertEqual(self.page.locator("#name-rows input").count(), 3)
        self.assertTrue(self.page.locator("#start").is_disabled())
        # Edited formula-leading names must survive CSV and be displayed as text.
        self.page.locator("#name-rows input").first.fill("=Synthetic corrected name")
        self.page.locator("#names-reviewed").check()
        self.page.locator("#start").click()
        self.page.locator("#open-first").wait_for(state="visible", timeout=30000)
        self.assert_phase("checking")
        self.assertEqual(self.app.snapshot()["saved"], 1)
        self.assertTrue(self.page.locator("#open-key-check").is_visible())
        with patch.object(web, "open_path") as open_file:
            self.page.locator("#open-key-check").click()
            deadline = time.monotonic() + 5
            while not open_file.called and time.monotonic() < deadline:
                self.page.wait_for_timeout(50)
            expected_key = Path(self.app.snapshot()["output"]) / "private" / "name_key.csv"
            open_file.assert_called_once_with(expected_key)
        self.assertTrue(self.page.locator("#checked").is_disabled())
        self.page.locator("#first-reviewed").check()
        self.page.locator("#checked").click()
        self.assert_phase("complete", timeout=45000)
        state = self.app.snapshot()
        self.assertEqual(state["saved"], 3)
        self.assertTrue(state["archive_ready"])
        out = Path(state["output"])
        manifest = json.loads((out / "private" / "manifest.json").read_text())
        self.assertTrue(manifest["page_loop_completed"])
        self.assertFalse(manifest["all_students_verified"])
        for index, record in enumerate(manifest["saved_logs"], 1):
            data = (out / "private" / record["file"]).read_text(encoding="utf-8")
            self.assertTrue(data.startswith("Began Tuesday"))
            self.assertNotIn("Dashboard", data)
            self.assertNotIn("Visible document", data)
            self.assertIn(f"Synthetic private final event {index}", data)
            self.assertNotIn("Student:", data)
            self.assertNotIn(record["student_name"], record["file"])
            self.assertRegex(record["record_id"], r"^R-[0-9a-f]{16}$")
            self.assertEqual(capture.digest(data), record["sha256"])
        self.assertEqual(manifest["saved_logs"][0]["student_name"], "=Synthetic corrected name")
        self.assertEqual(manifest["saved_logs"][0]["name_source"], "locally_edited")
        with (out / "private" / "name_key.csv").open(encoding="utf-8-sig", newline="") as handle:
            key = list(capture.csv.DictReader(handle))
        self.assertEqual(key[0]["record_id"], manifest["saved_logs"][0]["record_id"])
        self.assertEqual(key[0]["student_name"], "'=Synthetic corrected name")
        self.assertEqual(len({row["record_id"] for row in key}), 3)
        self.assertTrue((out / state["first_file"]).is_file())
        self.assertTrue(state["key_ready"])
        self.assertNotIn("analysis_issues", state)
        self.assertTrue(self.page.locator("#open-key").is_visible())
        with zipfile.ZipFile(out / "coded-logs.zip") as archive:
            all_text = "\n".join(archive.read(name).decode("utf-8") for name in archive.namelist())
            for private in ("Synthetic corrected name", "Synthetic student", "September", "2026", "11:46", "12:20", "student_name", "control_position"):
                self.assertNotIn(private, all_text)
            self.assertIn("Finished [calendar date and clock time omitted]", all_text)
            for original in ("00:10 Stopped viewing the Canvas quiz-taking page...", "00:30 Resumed.", "Synthetic private final event"):
                self.assertIn(original, all_text)
            for generated in ("Parser status:", "other_unclassified", "elapsed_order_valid", "page_focused"):
                self.assertNotIn(generated, all_text)
            self.assertFalse(any("private/" in name or "name_key" in name for name in archive.namelist()))
            self.assertFalse(any(name.endswith(".csv") or name.endswith(".json") for name in archive.namelist()))
        self.assertFalse((out / "captured-logs.zip").exists())
        self.assertFalse((out / "analysis").exists())
        # Refresh keeps the local session and completed output details.
        self.page.reload()
        self.assert_phase("complete")

    def test_stop_after_first_retains_partial_archive(self):
        self.launch_synthetic()
        self.page.locator("#names-reviewed").check()
        self.page.locator("#start").click()
        self.page.locator("#open-first").wait_for(state="visible", timeout=30000)
        self.page.locator("#stop").click()
        self.assert_phase("stopped")
        state = self.app.snapshot()
        self.assertEqual(state["saved"], 1)
        manifest = json.loads((Path(state["output"]) / "private" / "manifest.json").read_text())
        self.assertFalse(manifest["page_loop_completed"])
        self.assertEqual(manifest["error"], "stopped_by_user")
        self.assertTrue(state["archive_ready"])
        self.assertTrue((Path(state["output"]) / "coded-logs.zip").is_file())

    def test_named_workflow_has_no_key_or_id_confirmation(self):
        self.launch_synthetic(mode="named")
        self.page.locator("#names-reviewed").check()
        self.page.locator("#start").click()
        self.page.locator("#open-first").wait_for(state="visible", timeout=30000)
        self.assert_phase("checking")
        self.assertFalse(self.page.locator("#open-key-check").is_visible())
        self.assertFalse(self.page.locator("#open-key").is_visible())
        self.assertFalse(self.app.snapshot()["key_ready"])
        self.assertEqual(self.page.locator("#first-check-label").inner_text(), "I checked the student name and downloaded text against Canvas.")
        self.page.locator("#first-reviewed").check()
        self.page.locator("#checked").click()
        self.assert_phase("complete", timeout=45000)
        state = self.app.snapshot()
        self.assertEqual(state["export_mode"], "named")
        out = Path(state["output"])
        self.assertFalse((out / "private" / "name_key.csv").exists())
        self.assertFalse((out / "coded-logs.zip").exists())
        manifest = json.loads((out / "private" / "manifest.json").read_text())
        self.assertEqual(len(manifest["saved_logs"]), 3)
        with zipfile.ZipFile(out / "named-logs.zip") as archive:
            for index, record in enumerate(manifest["saved_logs"], 1):
                self.assertNotIn("record_id", record)
                self.assertIn(f"Synthetic_student_{index}", record["file"])
                text = archive.read(record["file"]).decode()
                self.assertIn(f"Student: Synthetic student {index}", text)
                self.assertIn("Began Tuesday, September 29, 2026 at 11:46 AM", text)
                self.assertIn("Finished Tuesday, September 29, 2026 at 12:20 PM", text)
                self.assertNotIn("Record ID:", text)
                self.assertNotIn("[calendar date", text)

    def test_mobile_layout_and_names_rendered_as_text(self):
        self.assertNotIn("UF approved OneDrive is fine.", self.page.locator("body").inner_text())
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.app.update(phase="review", total=1, run_id="synthetic", names=[{
            "position": 1, "name": '<img src="https://private.invalid/" onerror="alert(1)">'}])
        self.page.locator("#name-rows input").wait_for()
        self.assertEqual(self.page.locator("#name-rows img").count(), 0)
        self.assertFalse(self.page.evaluate("document.documentElement.scrollWidth > innerWidth"))

    def test_about_dialog_privacy_workflow_and_hidden_readiness_setting(self):
        self.assertNotIn("Log readiness phrase", self.page.locator("body").inner_text())
        self.page.locator("#about-open").click()
        dialog = self.page.get_by_role("dialog", name="Canvas Quiz Log Exporter")
        self.assertTrue(dialog.is_visible())
        text = dialog.inner_text()
        self.assertIn("Sensitive rather than Restricted data", text)
        self.assertIn("does not automatically change the classification", text)
        self.assertIn("private/name_key.csv", text)
        self.assertIn("Build → Moderate", text)
        self.assertIn("FERPA rules", text)
        self.page.locator("#about-close").click()
        self.assertFalse(dialog.is_visible())
        self.assertTrue(self.page.locator("#about-open").evaluate("element => element === document.activeElement"))
        self.page.locator("#about-open").click()
        self.page.keyboard.press("Escape")
        self.assertFalse(dialog.is_visible())
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.page.locator("#about-open").click()
        self.assertFalse(self.page.evaluate("document.documentElement.scrollWidth > innerWidth"))
        self.page.locator("#about-close").click()


if __name__ == "__main__":
    unittest.main()
