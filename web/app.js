"use strict";
(() => {
  const token = location.hash.slice(1);
  const $ = id => document.getElementById(id);
  let state = {phase: "idle", run_id: ""};
  let renderedReview = "";
  let renderedCheck = "";
  let polling = true;
  let busy = false;
  let modeRestored = false;
  let browserRestored = false;
  $("about-open").addEventListener("click", () => $("about-dialog").showModal());
  $("about-close").addEventListener("click", () => $("about-dialog").close());
  const terminal = new Set(["idle", "complete", "stopped", "error"]);
  const descriptions = {
    idle: ["Ready when you are", "Choose your Canvas address and output folder, then open Canvas to begin.", "Not started"],
    opening: ["Opening your Canvas browser", "A dedicated window will open. Your sign-in stays in that browser.", "Opening"],
    navigate: ["Open your quiz’s Moderate page", "Use the separate Canvas window, then return here to find the logs.", "Your turn"],
    finding: ["Finding the displayed logs", "Waiting for the Moderate list to load and stay stable.", "Finding logs"],
    review: ["Review the student names", "Confirm who each View Log belongs to before collection begins.", "Your turn"],
    capturing: ["Collecting your logs", "The app is opening logs in their displayed order and saving each one locally.", "Collecting"],
    checking: ["Check the first downloaded log", "Collection is paused while you check the private name key and downloaded text.", "Your turn"],
    finishing: ["Finishing your local export", "Preserving the text files and creating the export ZIP.", "Finishing"],
    stopping: ["Stopping collection", "Waiting for the current browser operation to end. Completed files will be preserved.", "Stopping"],
    complete: ["Collection finished", "The displayed View Log controls have been processed.", "Finished"],
    stopped: ["Collection stopped", "Any completed files remain in your output folder. A new run starts from the first student.", "Stopped"],
    error: ["Collection needs attention", "Any completed files are preserved. Check the message below before starting a new run.", "Needs attention"]
  };
  async function api(path, body) {
    const options = {cache: "no-store", headers: {Authorization: `Bearer ${token}`}};
    if (body !== undefined) {
      options.method = "POST";
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);
    if (!response.ok) {
      if (response.status === 403) throw new Error("This session is not authorized. Reopen the app using its Start App launcher.");
      let result;
      try { result = await response.json(); } catch (_) {}
      throw new Error(result?.error || "The local app could not complete that action.");
    }
    return response.json();
  }
  function localError(message) {
    $("local-error").textContent = message;
    $("local-error").hidden = !message;
  }
  function show(id, visible) { $(id).hidden = !visible; }
  function render(next) {
    state = next;
    if (!browserRestored) {
      $("browser").value = state.default_browser || "msedge";
      browserRestored = true;
    }
    const phase = state.phase;
    const active = !terminal.has(phase);
    if (!modeRestored || active) {
      $(state.export_mode === "named" ? "mode-named" : "mode-coded").checked = true;
      modeRestored = true;
    }
    for (const id of ["mode-coded", "mode-named"]) $(id).disabled = active || busy;
    updateModeNote();
    const named = state.export_mode === "named";
    const [title, description, status] = descriptions[phase] || descriptions.error;
    $("stage-title").textContent = title;
    $("stage-description").textContent = description;
    $("status").textContent = status;
    $("error").textContent = state.error || "";
    show("error", !!state.error);
    for (const id of ["canvas-url", "output", "browse", "browser", "launch"]) $(id).disabled = active || busy;
    $("launch").textContent = phase === "idle" ? "Open Canvas" : "Open Canvas for a new run";
    show("welcome", phase === "idle");
    show("navigate", phase === "navigate");
    show("review", phase === "review");
    show("first-check", phase === "checking");
    show("open-key-check", !named && !!state.key_ready);
    $("open-first").textContent = named ? "Open first named log" : "Open first coded log";
    $("first-check-help").textContent = named
      ? "Compare the student name and downloaded text with Canvas. Original dates and times are retained. This mode has no coded ID or name key."
      : "Use the private name key to confirm the ID belongs to the correct student. Compare the downloaded event text and elapsed times with Canvas. Start and finish dates and clock times are omitted.";
    $("first-check-label").textContent = named ? "I checked the student name and downloaded text against Canvas." : "I checked the ID in the private key and the downloaded text against Canvas.";
    show("stop", active);
    $("stop").disabled = ["stopping", "finishing"].includes(phase) || busy;
    show("progress-section", state.total > 0 && phase !== "review");
    show("output-section", state.total > 0 || state.saved > 0);
    show("result", ["complete", "stopped", "error"].includes(phase) && state.total > 0);
    const step = ["idle", "opening", "navigate", "finding"].includes(phase) ? 1 :
      phase === "review" ? 2 : phase === "checking" || (phase === "capturing" && state.saved === 0) ? 3 : 4;
    for (let i = 1; i <= 4; i++) {
      $("step" + i).classList.toggle("active", i === step);
      $("step" + i).classList.toggle("done", i < step);
      if (i === step) $("step" + i).setAttribute("aria-current", "step");
      else $("step" + i).removeAttribute("aria-current");
    }
    if (phase === "review" && renderedReview !== state.run_id) {
      renderedReview = state.run_id;
      $("names-reviewed").checked = false;
      $("name-rows").replaceChildren();
      for (const row of state.names) {
        const tr = document.createElement("tr");
        const position = document.createElement("td");
        position.textContent = row.position;
        const cell = document.createElement("td");
        const input = document.createElement("input");
        input.type = "text"; input.value = row.name; input.maxLength = 200;
        input.autocomplete = "off";
        input.dataset.position = row.position;
        input.setAttribute("aria-label", `Student name at position ${row.position}`);
        cell.append(input); tr.append(position, cell); $("name-rows").append(tr);
      }
      $("count-label").textContent = `${state.total} View Log controls found on this Moderate page`;
    }
    if (phase === "checking" && renderedCheck !== state.run_id) {
      renderedCheck = state.run_id;
      $("first-reviewed").checked = false;
    }
    $("start").disabled = !$("names-reviewed").checked || busy;
    $("checked").disabled = !$("first-reviewed").checked || busy;
    const percent = state.total ? Math.round(state.saved / state.total * 100) : 0;
    $("progress-text").textContent = `${state.saved} of ${state.total} logs saved`;
    $("percent").textContent = `${percent}%`;
    $("progress").max = state.total || 1;
    $("progress").value = state.saved;
    $("progress-note").textContent = active ? "Please leave the dedicated Canvas window alone while collection runs." : "Files remain in the output folder below.";
    $("output-path").textContent = state.output;
    $("archive-note").textContent = named
      ? (state.archive_ready ? "named-logs.zip contains student names and original dates, times and event text. No key was created." : "Named downloads are in logs/. No student coding or name key is used.")
      : (state.archive_ready ? "coded-logs.zip contains the downloaded text files. The private name key is excluded." : "Downloaded text is in logs/. The name key and full captures stay in private/.");
    $("output-privacy").textContent = named ? "These downloads contain identified student records. Use only storage and services authorized for their required classification and follow institutional privacy and FERPA rules." : "Keep private/ and name_key.csv private. Review coded files before sharing: identifying details can remain. This app does not certify FERPA compliance.";
    $("result-description").textContent = `${state.saved} of ${state.total} displayed logs saved. ${state.archive_ready ? "Your download ZIP is ready." : "Check the output folder for completed files."}`;
    show("open-key", !!state.key_ready);
    show("duplicates", state.warning_count > 0);
    $("activity").textContent = active ? (phase === "checking" || phase === "review" || phase === "navigate" ? "Waiting for your next step." : "Local collection is running.") : "No collection is running.";
  }
  async function refresh() {
    render(await api("/api/state"));
  }
  function updateModeNote() {
    $("mode-note").textContent = $("mode-named").checked
      ? "Names and original dates and times are retained. Use only an environment authorized for identified student records."
      : "Review coded files before sharing. The private folder still contains identifying records.";
  }
  for (const id of ["mode-coded", "mode-named"]) $(id).addEventListener("change", updateModeNote);
  async function action(name, extra = {}) {
    if (busy) return;
    busy = true; localError(""); render(state);
    try {
      await api("/api/action", {action: name, run_id: state.run_id, ...extra});
      await refresh();
    } catch (error) { localError(error.message); }
    finally { busy = false; render(state); }
  }
  $("setup").addEventListener("submit", event => {
    event.preventDefault();
    action("launch", {url: $("canvas-url").value.trim(), output: $("output").value.trim(), browser: $("browser").value, export_mode: $("mode-named").checked ? "named" : "coded"});
  });
  $("browse").addEventListener("click", async () => {
    $("browse").disabled = true; localError("");
    try { const result = await api("/api/browse", {}); if (result.folder) $("output").value = result.folder; }
    catch (error) { localError(error.message); }
    finally { $("browse").disabled = !terminal.has(state.phase); }
  });
  $("moderate").addEventListener("click", () => action("moderate"));
  $("start").addEventListener("click", () => {
    const names = [...$("name-rows").querySelectorAll("input")].map(input => ({position: Number(input.dataset.position), name: input.value}));
    action("start", {reviewed: $("names-reviewed").checked, names});
  });
  $("checked").addEventListener("click", () => action("checked"));
  $("stop").addEventListener("click", () => action("stop"));
  for (const id of ["names-reviewed", "first-reviewed"]) $(id).addEventListener("change", () => render(state));
  for (const [id, path] of [["open-folder", "/api/open-folder"], ["open-first", "/api/open-first"], ["open-key", "/api/open-key"], ["open-key-check", "/api/open-key"]]) {
    $(id).addEventListener("click", async () => {
      localError("");
      try { await api(path, {}); } catch (error) { localError(error.message); }
    });
  }
  $("quit").addEventListener("click", async () => {
    try {
      await api("/api/quit", {});
      polling = false;
      document.querySelectorAll("button,input,select").forEach(element => element.disabled = true);
      $("stage-title").textContent = "Local app closed";
      $("stage-description").textContent = "Any active collection is stopping and preserving completed files. You can close this tab.";
      $("status").textContent = "Closed";
      $("activity").textContent = "Use the Start App launcher to reopen.";
    } catch (error) { localError(error.message); }
  });
  async function poll() {
    if (!polling) return;
    try { await refresh(); }
    catch (_) { localError("The local app is unavailable. Reopen it with the Start App launcher if it has closed."); }
    if (polling) setTimeout(poll, 750);
  }
  if (!token) {
    localError("Open this interface using the Start App launcher. The session link is required to access local records.");
    document.querySelectorAll("button,input,select").forEach(element => element.disabled = true);
  } else { poll(); }
})();
