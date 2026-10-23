# Canvas Quiz Log Exporter

A local Windows app for downloading the displayed event text from Canvas **New Quizzes**. It opens each **View Log** on one Moderate page, saves the text, and returns to the student list. It performs **no analysis**.

[Download the latest release](https://github.com/davidjulian/canvas-quiz-log-exporter/releases/latest)

Version 0.9.0. Requires **Windows, Python 3.10 or newer, and installed Microsoft Edge or Google Chrome**. This is a local Python app, not a standalone executable or a hosted Canvas service. It uses your own authorized instructor browser session; no Canvas API token is requested.

## Install and open

1. Download **canvas-quick-capture.zip** from the release and extract it completely.
2. Open the extracted canvas-quick-capture folder and double-click **Install.cmd** once. Setup installs the dependency from requirements.txt into a local Python environment. Internet access is needed for setup.
3. Double-click **Start App.cmd**. The app opens a local page in your default browser. Windows may hide the .cmd extensions. No terminal commands are needed for normal use.

If you already have a working installation, close the old app with **Quit local app**, copy in the updated source files, then use **Start App.cmd** again. No new dependency is needed for version 0.9.0. Do not run the launchers from inside the ZIP.

## Choose an export mode

| Mode | Downloaded files | Student names and dates | Private name key |
| --- | --- | --- | --- |
| **Coded logs** (default) | logs/log_R-....txt and coded-logs.zip | Reviewed names and recognizable email/web/IPv4 addresses are replaced; Began and Finished calendar dates and clock times are omitted | Created separately at private/name_key.csv; excluded from ZIP |
| **Named logs** | logs/log_001_Student_Name.txt and named-logs.zip | Student names and original dates, times and event text are retained | No coding, name key or ID/key confirmation |

Choosing a mode controls the file contents. It does not encrypt files, authorize storage or services, change a data classification, or certify FERPA compliance. Use named mode only in an environment authorized for identified student records and their required classification.

## Download logs

1. Confirm the **Canvas URL**, defaulting to https://ufl.instructure.com/. Choose an existing output folder with **Browse** or paste a folder path. Select the export mode. Each run creates a new folder inside the selected location.
2. Click **Open Canvas**. In the separate dedicated browser, sign in to Canvas and open your completed New Quiz, then go to **Build → Moderate**. Set any desired filters and students per page setting and wait for the student list to load. Keep only one Moderate list open in this browser.
3. Return to the app and click **I'm on Moderate — find logs**. Check the displayed count and proposed student names against Moderate, correct names on screen, check the review box and click **Start collection**.
4. Check the first downloaded log against Canvas, including the final event and any need for more event pages, scrolling or expansion. In **coded mode**, the **Open private name key** button is available at this step so you can check the ID-to-name association. In **named mode**, check the student's name directly in the downloaded file; no key or ID confirmation is required.
5. If the first download is adequate, check the review box and click **Checked — collect remaining logs**. Otherwise use **Stop**. Leave the dedicated Canvas window alone while downloads run.
6. Click **Open output folder** to see logs/ and the selected mode's ZIP. **Stop** preserves completed files and creates a partial ZIP where possible. It may wait for the current browser operation to finish. Every new run starts at the first displayed control; there is no skip or resume mode.
7. Use **Quit local app** when finished. Closing or refreshing the web tab alone does not stop a run.

The **About** button explains both modes, the workflow and privacy responsibilities. The internal page-loading check runs automatically and is not a user setting.

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

The dedicated browser profile stays in `%LOCALAPPDATA%\CanvasQuizExporter\BrowserProfile`. It contains session state and is never included in exports or the software distribution. No API token is requested or extracted. Keep the profile private.

## Scope

One run processes **only the View Log controls currently displayed on one Moderate page**. It does not advance student pagination, reveal hidden attempts, scroll virtual lists, expand details or load additional event pages. A first-file check does not prove every later capture is complete. The private manifest leaves whole-student and whole-event completeness unverified. Only rendered text from the single Began line onward is downloaded; surrounding Canvas navigation is removed.

Original event wording and relative elapsed times are retained. There is no event recognition, classification, scoring, outlier detection or analysis. Page focus events alone cannot establish LLM use or misconduct. The app targets English New Quizzes layouts and same-tab View Log navigation. Other layouts may need adaptation.

## Troubleshooting and safe reports

- If **Browse** cannot open, paste an existing folder path.
- If the dedicated browser cannot open, close earlier exporter/Inspector browser windows using the same profile and confirm Edge or Chrome is installed.
- If Start App opens no page, run `.\.venv\Scripts\python.exe local_app.py --no-open` from this folder and open the printed local session link. Do not share the link.
- Earlier downloads are not automatically rewritten by an update. The earlier quick_capture.py command line workflow is retained for compatibility and uses its original named-file behavior.
- Share the clean software release ZIP with colleagues. Do not share your working folder, records, key, profile or environment.

Never post student records, identifying screenshots, name keys or session links in GitHub issues. Use invented examples and counts or fixed error categories. See [SECURITY.md](SECURITY.md).

## Tests

With Playwright installed and Edge available, set `CANVAS_RUN_BROWSER_TESTS=1` and run `.\.venv\Scripts\python.exe -m unittest discover -s tests -q`. Browser tests use invented local pages, temporary profiles and temporary output files. Non-fixture browser requests are blocked. Without that environment variable, only the non-browser tests run. See [VALIDATION.md](VALIDATION.md).
