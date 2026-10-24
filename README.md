# Canvas Quiz Log Exporter

A local Windows and macOS app for downloading the displayed event text from Canvas **New Quizzes**. It opens each **View Log** across recognized Moderate student pages, saves the text, and returns to the student list. It also creates a **local descriptive focus-event summary** for new downloads.

[Downloads and setup website](https://davidjulian.github.io/canvas-quiz-log-exporter/) · [Release files](https://github.com/davidjulian/canvas-quiz-log-exporter/releases/latest)

Version 0.13.0. Requires **Windows 11+ or macOS 14+ (Intel or Apple silicon), Python 3.10 or newer, and installed Microsoft Edge or Google Chrome**. The local interface can open in your usual browser, but the dedicated Canvas window must use Edge or Chrome; Safari is not supported for collection. This is a local Python app, not a standalone executable or a hosted Canvas service. It uses your own authorized instructor browser session; no Canvas API token is requested.

## Install and open

Install an institution-approved Python 3.10 or newer, or use [Python downloads](https://www.python.org/downloads/). Install Chrome or Edge if needed. Internet access is needed for setup. The software ZIPs contain only source files, documentation, tests and launchers. They contain no student records, local environments or browser profiles.

### Windows

1. Download **canvas-quick-capture.zip** from the release and extract it completely.
2. Open the extracted canvas-quick-capture folder and double-click **Install.cmd** once. Setup installs requirements.txt into a local Python environment.
3. Double-click **Start App.cmd**. The app opens in your default browser. Windows may hide the .cmd extensions. Edge is initially selected for the separate Canvas window.

### macOS

1. Download **canvas-quiz-log-exporter-macos.zip** and extract it completely. This source package works on Intel and Apple silicon Macs running macOS 14 or later; it is not a signed or notarized .app bundle.
2. Open the extracted canvas-quick-capture folder and double-click **Install.command** once. A Terminal window opens and installs requirements.txt into a local Python environment. No administrator access is requested. If Python cannot be found, install an approved Python 3.10+ or the [python.org macOS installer](https://www.python.org/downloads/macos/), then retry.
3. Double-click **Start App.command**. The app opens in your default browser. Chrome is initially selected for the separate Canvas window; change to Edge if that is what you have installed. Leave the launcher Terminal window open while the app runs. Use **Quit local app** when finished.

The app uses a native Mac folder chooser and opens output folders, logs and keys with the usual Finder/file associations. If Browse cannot open or storage permission is denied, paste an existing approved folder path or choose another permitted location.

If .command files lack executable permission, open Terminal in the extracted app folder and run:

```sh
chmod u+x Install.command "Start App.command"
```

If Finder opens a launcher as text, run `bash Install.command` once, then `bash "Start App.command"` from that folder. If institutional security blocks this software, consult your IT support; the installer does not disable security controls. If pip reports a certificate error with python.org Python, run **Install Certificates.command** in its Python folder under Applications, then retry setup. See [Python's Mac instructions](https://docs.python.org/3/using/mac.html).

### Updating an existing installation

Quit the old app, then extract the new software package into a new folder and run its installer once. Keep your existing exports where they are; the new version does not rewrite them. Windows and Mac virtual environments cannot be copied between operating systems. Do not run launchers from inside a ZIP. The default browser profile stays outside the software folder, so updating the software does not move it.

## Choose an export mode

| Mode | Downloaded files | Student names and dates | Private name key |
| --- | --- | --- | --- |
| **Coded logs** (default) | logs/log_R-....txt and coded-logs.zip | Reviewed names and recognizable email/web/IPv4 addresses are replaced; Began and Finished calendar dates and clock times are omitted | Created separately at private/name_key.csv; excluded from ZIP |
| **Named logs** | logs/log_001_Student_Name.txt and named-logs.zip | Student names and original dates, times and event text are retained | No coding, name key or ID/key confirmation |

Choosing a mode controls the file contents. It does not encrypt files, authorize storage or services, change a data classification, or certify FERPA compliance. Use named mode only in an environment authorized for identified student records and their required classification.

## Download logs

1. Confirm the **Canvas URL**, defaulting to https://ufl.instructure.com/. Choose an existing output folder with **Browse** or paste a folder path. Optionally enter a **Quiz name or folder label**, then select the export mode. Each run creates a new folder inside the selected location. For example, `PCB3713C Exam 2` produces `PCB3713C_Exam_2-20261023-153000-a1b2c3`. A date, time and random suffix keep runs separate. Leave the label blank to use the original `quiz-logs-...` name. The label can be edited before each new run; it is fixed during collection. Characters unsuitable for filenames are replaced and long labels shortened. The label names the local run folder only; it is not inserted into coded log text or ZIP filenames/contents.
2. Click **Open Canvas**. In the separate dedicated browser, sign in to Canvas and open your completed New Quiz, then go to **Build → Moderate**. Set any desired filters and students per page setting and wait for the student list to load. Keep only one Moderate list open in this browser.
3. Return to the app and click **I'm on Moderate — find logs**. The app scans the recognized numbered student pages, then returns to page 1. It can start from any numbered page. Review the combined count and proposed names across all discovered pages; the source page appears beside each sequential export position. Correct names on screen, check the review box and click **Start collection**. Leave Canvas alone during discovery. Do not change filters, sorting or page size after review.
4. Check the first downloaded log against Canvas, including the final event and any need for more event pages, scrolling or expansion. In **coded mode**, the **Open private name key** button is available at this step so you can check the ID-to-name association. In **named mode**, check the student's name directly in the downloaded file; no key or ID confirmation is required.
The first summary row is visible during this check. Compare its counts, paired periods and any notes with the original log before relying on later summary rows.

5. If the first download is adequate, check the review box and click **Checked — collect remaining logs**. Otherwise use **Stop**. Leave the dedicated Canvas window alone while downloads run.
6. Click **Open output folder** to see logs/ and the selected mode's ZIP. **Stop** preserves completed files and creates a partial ZIP where possible. It may wait for the current browser operation to finish. Every new web app run starts at page 1 and the first displayed log control; there is no skip or resume mode.
7. Use **Quit local app** when finished. Closing or refreshing the web tab alone does not stop a run.

### Collect another quiz in the same Canvas window

**Keep Canvas open for another quiz** is optional and off by default. When checked before starting, the separate Canvas window stays open after a successful collection. Open another completed quiz there and go to **Build → Moderate**. In the app, update the folder label and other settings, then select **Use open Canvas for a new run** and follow the normal name and first-log checks. The app reuses the same browser context and does not send it back to the Canvas home page if the Canvas address and browser selection are unchanged. Each run still gets a separate output folder and fresh coded IDs.

With the option unchecked, the Canvas window closes after collection as before. Stop, collection errors and **Quit local app** also close it. Closing Canvas is not the same as signing out; the private local profile can retain authentication state. Keeping a window open is convenient on your own secured computer, but close it or quit when leaving the computer or using a shared device. Institutional session expiry and sign-in policies still apply. Changing the browser selection opens a new dedicated browser; changing the Canvas address navigates to that address.

The **About** button explains both modes, the workflow and privacy responsibilities. The internal page-loading check runs automatically and is not a user setting.

## Local event summary (new downloads only)

The app automatically shows a sortable table for each new collection with **student name**, **total elapsed time**, **Stopped viewing events**, **average away time in seconds**, **total paired away time**, **percentage of elapsed time away**, and **longest paired away period**. Each downloaded attempt/control is a separate row; repeated names are not merged. The number of paired intervals and any unpaired stops appear with the average. Expand **Check log** for row-specific limitations.

After collection finishes or stops, **Open named summary CSV** opens **private/event_summary.csv**. Its first seven columns match the table; additional columns identify the control position, coded ID when present, pairing counts, elapsed time basis and notes. **private/summary_method.txt** documents the calculations. Both files contain or accompany identified education records and must stay on approved storage. They are excluded from both coded and named log sharing ZIPs. No summary import of earlier files is provided.

- Each unambiguous **Stopped viewing → Resumed** pair contributes one duration; the average is the sum of those durations divided by the number of valid pairs. Intervening answers do not end an away period. Zero-second pairs are kept.
- Total paired away time is the sum of valid pair durations; the longest paired away period is their maximum. Percentage away is `100 × total paired away seconds / displayed elapsed seconds`. A zero denominator has no percentage. When the displayed elapsed time is only the last visible event, the percentage is flagged as provisional. Unpaired or ambiguous periods can make total time and percentage too low, and the longest actual period may be missing.
- Stops without a return, returns without a stop, consecutive stops and timestamp problems are flagged. Unmatched or ambiguous periods do not receive an invented duration. A blank average means unavailable, not zero.
- Total elapsed time uses a recognized submission event when present. Otherwise it is the **last visible elapsed value**, explicitly flagged as not a verified full attempt duration. Calendar timestamps are not used. Instructure notes that the Moderate page's duration can be more accurate for timed quizzes.
- Summary problems never block the text downloads. Unreadable layouts produce blank/flagged summary values. A summary write failure leaves the local table available and reports that the CSV could not be saved.

Only downloaded text is summarized, so hidden or unloaded events can bias the results. A stopped run produces a partial table. Focus events do not reveal another website or application, establish ChatGPT use or prove prohibited behavior. Instructure advises against using quiz logs to validate academic integrity or identify cheating: [New Quizzes Moderate guide](https://community.instructure.com/en/kb/articles/661091-unknown).

## Coded files and private records

Coded mode assigns a fresh random ID to each displayed View Log control/attempt. IDs do not encode a name, Canvas ID or roster position. They are newly generated each run. Multiple attempts for one student have different IDs; equal display names are not automatically merged because different students can share a name.

Keep **private/** restricted to authorized users. In coded mode it contains **name_key.csv**, which maps IDs to the reviewed names and Moderate positions. It also contains full original captures, the name review mapping and a capture manifest. The key includes all intended controls, including uncaptured controls if you stop early; compare it with the logs actually present. The key is written once before downloading, and formula-leading names are CSV protected.

Named mode creates no random student IDs and no name_key.csv. It retains the local name review and capture details in private/ alongside the fully identified text downloads in logs/. All these records need the protections appropriate to identified education records.

The ZIP contains only the explicitly selected downloaded text files and brief sharing instructions. It excludes private/, the name key, browser profiles and local Python environments. Do not ZIP the entire output folder or working app folder yourself when sharing coded data.

## Privacy, classification and FERPA

Separating identifying records from reviewed coded logs **may allow the coded output to be handled as Sensitive rather than Restricted data**, where institutional classification and de-identification rules permit. It does **not** automatically change the classification or guarantee anonymity. Other names, IDs, answers, dates, addresses and distinctive details can remain in free text. Review every coded file locally before external sharing.

You are responsible for following all applicable institutional privacy, data handling and FERPA rules. Use only tools and services approved for the resulting data classification. Keep identifiable originals and the name key in an environment approved for their required classification. The app never automatically uploads records to AI or another service.

References: [UF data classification policy](https://policy.ufl.edu/policy/data-classification-policy/), [U.S. Department of Education de-identification guidance](https://studentprivacy.ed.gov/faq/what-constitutes-de-identified-records-and-information).

The local interface binds only to 127.0.0.1 on a random port and requires a random per-launch token for API access. It checks Host and Origin, blocks framing and external web assets, and sends no-store cache headers. There are no AI, analytics or telemetry calls. Canvas still uses its normal institutional SSO and LTI connections. Do not publicly host this local server or forward its port. Output files are not automatically encrypted.

The dedicated browser profile stays in `%LOCALAPPDATA%\CanvasQuizExporter\BrowserProfile` on Windows and `~/Library/Application Support/CanvasQuizExporter/BrowserProfile` on macOS. It contains session state and is never included in exports or the software distribution. No API token is requested or extracted. Keep the profile private.

## Scope

One web app run scans **all recognized numbered Moderate student pages**, keeps current filters and page size, and processes their reviewed View Log controls in page order. Discovery opens no logs. It returns to page 1 for one combined name review; the first downloaded log is checked once as before. Files, IDs and summary positions remain unique across pages in one output folder, ZIP and summary. The private manifest records each page's control count and completion state. The coded name key also records source page and position on that page.

Pagination uses accessible page numbers, current-page markers and Next/Previous controls in the same document as the Moderate list, including Canvas iframes. It waits for a stable page number and changed rows, detects repeated control identities, checks reviewed rows before every capture, and restores the reviewed page if Back resets the list to page 1. Empty recognized pages do not end traversal. Ambiguous controls, changed filters/list order or an unresponsive page stop collection and preserve completed files. The limits are 1,000 recognized pages and 5,000 log controls per run; larger lists need smaller filters. A single-page list needs no pagination controls.

This does not remove filters or load students excluded by them. It does not reveal hidden attempts, scroll virtual lists, expand details or load additional pages **inside an event log**. The legacy command line collector still processes one displayed Moderate page; automatic student pagination applies to the local web app. A first-file check does not prove every later capture is complete. The private manifest leaves whole-student and whole-event completeness unverified. Only rendered text from the single Began line onward is downloaded; surrounding Canvas navigation is removed.

Original event wording and relative elapsed times are retained in the downloaded logs. The separate summary calculates descriptive focus-event counts and paired durations. There is no misconduct scoring, automatic outlier classification or inference about another website or application. Page focus events alone cannot establish LLM use or misconduct. The app targets English New Quizzes layouts and same-tab View Log navigation. Other layouts may need adaptation.

## Troubleshooting and safe reports

- If **Browse** cannot open, paste an existing folder path.
- If the dedicated browser cannot open, close earlier exporter/Inspector browser windows using the same profile and confirm Edge or Chrome is installed.
- If the launcher opens no page, run `.\.venv\Scripts\python.exe local_app.py --no-open` (Windows) or `.venv/bin/python3 local_app.py --no-open` (Mac) from the extracted folder and open the printed local session link. Do not share the link.
- Earlier downloads are not automatically rewritten by an update. The earlier quick_capture.py command line workflow is retained for compatibility and uses its original named-file behavior.
- Share the clean software release ZIP with colleagues. Do not share your working folder, records, key, profile or environment.

Never post student records, identifying screenshots, name keys or session links in GitHub issues. Use invented examples and counts or fixed error categories. See [SECURITY.md](SECURITY.md).

## Tests

With Playwright installed and Edge (Windows) or Chrome (Mac) available, set `CANVAS_RUN_BROWSER_TESTS=1` and run `.\.venv\Scripts\python.exe -m unittest discover -s tests -q` (Windows) or `.venv/bin/python3 -m unittest discover -s tests -q` (Mac). `CANVAS_TEST_BROWSER=chrome` or `msedge` can override the browser used by synthetic tests. Browser tests use invented local pages, temporary profiles and temporary output files. Non-fixture browser requests are blocked. Without that environment variable, only the non-browser tests run. See [VALIDATION.md](VALIDATION.md).
