# Validation

Version 0.13.2, October 24, 2026.

Moderate detection repair: tab selection again uses the established View Log control locator independently of pagination inspection. Pagination ignores student-table navigation wrappers, navigation without page controls, empty placeholders and page-size-only controls. Static page-one and whole-list range indicators support a single-page list. Browser locators handle controls inside open shadow roots. Unsupported noninteractive multiple-page indicators remain an error; additional pages are not silently ignored.

Finding and page discovery run before a capture folder is created. A recoverable discovery failure leaves the same browser and sign-in context open for retry, even when keep-open is unchecked. Stop and Quit close it. On failure the interface exposes only count/flag/error-category diagnostics, never student names, log text, filter values or URLs. Errors in an unrelated visible frame do not discard an otherwise recognized student list. Setup values can be restored for an empty failed run without treating it as a previously collected quiz. Small rejected POST bodies are drained before returning 415, matching the existing bounded 403 handling to avoid Windows connection resets.

Invented tests cover navigation wrappers, nested paginators, unrelated-frame errors, diagnostic privacy, empty/static/page-size-only widgets, shadow roots, noninteractive multiple-page refusal, whole-list range status, same-browser retry after a failed search, ambiguous-pagination retry state, Stop closure and restored initial settings. Earlier paging, export, summary and security tests remain in the suite.

The instructor confirmed that the repaired local app reached student name review on the UF Moderate page. Only the app phase and counts-only diagnostics were inspected here; no actual roster, student name, log text or screenshot was loaded into the conversation.

Final platform results will be recorded when the release checks finish.

## Version 0.13.1 validation

Version 0.13.1, October 24, 2026.

Elapsed-time fallback repair: a readable submission event or last timed event is retained even if an earlier event timestamp is invalid. Away durations remain unavailable when timestamps cannot be trusted. The table labels last-event elapsed time as an estimate; the CSV retains the timing basis and reliability notes. An unreadable final event is not silently replaced with an earlier one. Mixed event order and conflicting submission times remain unavailable. A raw stop entry with an invalid clock is not mistaken for zero recorded stops.

Invented regression cases cover invalid earlier and final clocks, a readable submission after an invalid row, reversed rows with an unreadable latest event, a long lab-like timeline without submission, and stop-count preservation. The local interface workflow checks the estimated time label, named CSV values, blank unavailable away durations and preservation of original downloads and partial ZIPs. A user-supplied redacted lab log was checked locally using only generic layout flags and availability booleans; its event values and text were not copied into the software or test fixtures.

Folder label warning: a new run with the same label (including case/whitespace-only changes or another blank label) requires Change label or explicit Use same label. The confirmation is tied to the previous run ID, so a stale confirmation is rejected. The warning does not open, close or navigate Canvas and does not start another collection. Tests cover first-run behavior, blocking before worker/file changes, retained-browser reuse after confirmation, changing the label, Escape cancellation, literal label rendering, blank labels, mobile layout and restart notices for older app processes.

Windows: all 121 tests passed with none skipped in 279 seconds. After replacing a test expression with a standard locator assertion compatible with strict browser security, all 33 local interface and HTTP tests passed again in 158 seconds. Application security settings were not changed. Invented browser previews verified both the elapsed estimate label and the repeated-folder-label dialog.

Mac: all 121 tests passed with none skipped on both Apple silicon and Intel. Linux unit checks also passed. [Successful workflow and tested source commit](https://github.com/davidjulian/canvas-quiz-log-exporter/actions/runs/40137805544). The Mac checks include the distributed installer and invented-data browser workflows. Native dialog and institution-managed installation limitations from the earlier platform validation still apply.

## Version 0.13.0 validation

Version 0.13.0, October 24, 2026.

Student pagination: the web app discovers all recognized numbered Moderate pages before one combined name review, then captures the reviewed controls in page order. The first-log check remains once per run. The current filters and page size remain in effect. Both export modes use global positions, and coded IDs remain unique across pages. The private name key includes source page and row position; the private manifest includes per-page completion. Event pagination and hidden attempts remain unsupported.

Invented-data tests cover 150 controls across three pages, starting on a later page, empty middle pages, number-only and mirrored pagers, public InstUI current-page markers with sliding windows and omitted disabled arrows, iframe navigation, Back resetting to page 1, conflicting controls, stale/repeated rows, changed filters and reviewed lists, limits, cancellation and later-page partial ZIP preservation. Full coded and named capture cases verify one name review, one first-log check, unique IDs/global positions, the combined private CSV and sharing ZIP exclusions. No live Canvas account, existing browser profile or student record is used. Actual institutional page layouts still require local verification; passing invented fixtures cannot certify whole-class or whole-event completeness.

Windows: all 110 tests passed with none skipped in 276 seconds. All 110 tests also passed with none skipped on both Apple silicon and Intel Mac environments. Linux unit checks passed. [Successful workflow and tested source commit](https://github.com/davidjulian/canvas-quiz-log-exporter/actions/runs/40103579635). The combined name review was visually checked in the local browser with invented names from three pages. No live Canvas account or actual student list was inspected.

## Version 0.12.0 validation

Version 0.12.0, October 23, 2026.

Windows: all 90 tests passed with none skipped in 100 seconds. The summary panel was also reviewed with invented records in the local browser, including sorting an added measure and viewing unmatched-event notes. The panel spans the page; narrow screens keep table overflow inside the table wrapper.

Mac verification: all 90 tests passed with none skipped on Intel and Apple silicon. Linux unit checks also passed. [Successful workflow and tested source commit](https://github.com/davidjulian/canvas-quiz-log-exporter/actions/runs/40044880187).

New local summary: one row per new downloaded attempt, with reviewed name, elapsed time, stop count, mean and total duration of unambiguous stop/return pairs, percentage of displayed elapsed time away, and longest valid paired period. Tests independently verify totals, maxima, the percentage denominator, rounding, zero versus unavailable values, provisional percentages and the treatment of unknown periods. It supports MM:SS and HH:MM:SS, inline and split rows, blank lines, and both documented stop wording variants. Tests cover no away events versus zero-second pairs, unmatched and duplicate stops, consecutive stop clusters, orphan returns, reverse/mixed ordering, invalid clocks, missing/conflicting submission and post-submission events. Missing values remain unknown. The source and test cases are inspectable in event_summary.py and tests/test_event_summary.py.

CSV tests verify formula-safe student names and blank unavailable values. Browser workflow tests verify table values and sorting, the private named CSV in both export modes, its exclusion from sharing ZIPs, native opening of the fixed summary path, and text/ZIP preservation when both parsing and summary writing fail. Earlier extraction, privacy and browser reuse checks remain in the suite. Only newly collected text is summarized.

A user-supplied redacted file was checked locally for layout compatibility. Its actual names, timestamps and metric values were not printed into the chat or copied into source/test fixtures. All automated test records are invented.

## Earlier platform validation

Windows verification: the full 72-test suite passed with none skipped in 93 seconds. After the final settings restoration adjustment, all 25 local interface tests passed with none skipped in 61 seconds. Browser tests use invented records, temporary profiles and temporary output folders.

Folder label update: optional quiz/folder label in setup, portable child-folder naming with a bounded UTF-8 length, date/time and a random suffix. Blank labels preserve the default. Path separators cannot escape the selected output location. The label is locked during a run, restored on refresh, and editable for a subsequent run. Coded archive tests verify it is absent from ZIP contents; repeated-run tests verify earlier exports are preserved. All verification uses invented records and temporary output folders.

Browser reuse update: optional keep-open setting defaults to false. Successful retained runs use the same Playwright worker and browser context for a new run; the page is not reset when address and browser are unchanged. Integration tests verify one browser launch across successive runs, the previous export remaining intact, default closure and Stop closure. A worker test verifies Quit closes an idle retained context. No credentials, session cookies or storage are extracted to implement reuse.

Mac verification for 0.11.0: all 72 tests passed with none skipped on both Intel and Apple silicon. Linux unit checks also passed. [Successful workflow and tested source commit](https://github.com/davidjulian/canvas-quiz-log-exporter/actions/runs/40039199219). Native file dialog and Finder limitations below still apply.

## Version 0.10.0 platform baseline

Windows verification for 0.10.0: all 67 tests passed with none skipped in 86 seconds using Python 3.11 and Microsoft Edge. These include the full coded and named workflows and the new platform tests.

Platform update: added macOS setup and launcher scripts, a native macOS folder chooser, Finder/file opening, Application Support browser profile storage, and a Chrome default on Mac. Windows keeps its previous profile location and Edge default. Platform tests use invented paths and mock native dialogs/file opening, including cancellation, spaces and apostrophes, subprocess failures and safe error messages. Shell script syntax is checked with bash; Mac ZIP scripts have LF line endings and executable Unix permissions.

Mac verification for 0.10.0: all 67 tests passed with none skipped on macos-14 (Apple silicon) and macos-15-intel, including setup with the distributed Install.command and the full invented-data browser workflows. Both launchers also passed shell syntax and executable-permission checks. [Successful workflow and tested source commit](https://github.com/davidjulian/canvas-quiz-log-exporter/actions/runs/40015799393). Finder double-click launch, native folder dialog interaction, file associations, Gatekeeper and institution-managed permissions are not exercised end to end. No physical Mac or live Canvas account is available in this Windows session.

Prior Windows baseline: Windows, Python 3.11.5, Playwright 1.64.1 and installed Microsoft Edge.

For version 0.9.0, all 61 tests passed with none skipped in 85 seconds. The suite includes original collector coverage, HTTP/privacy checks, coded and named download tests, and end-to-end browser workflows using invented records and temporary files/profiles. No live Canvas account, existing browser profile, real student record or name key is used by the tests.

Coded-mode tests verify original event text and elapsed times, start/finish date and clock omission, limited identifier substitutions, random IDs, the separate private key, archive allowlisting, matching capture hashes and preservation of partial downloads.

Named-mode tests verify student names, original start/finish dates and times, original event text, named filenames, named-logs.zip, no random student IDs, no name_key.csv, and no ID/key confirmation. Invalid modes are rejected before the browser starts. Export mode is fixed during a run.

UI tests cover the revised Build → Moderate instructions, the private-key button at the first-log check, the hidden internal readiness setting, About content, modal close/Escape and focus return, and narrow-screen layouts. Native file opening is mocked while verifying the requested key path.

HTTP tests cover loopback binding, authentication, hostile Origin/Host rejection, POST Origin checks, malformed requests, no-store/framing protections and refusal to serve arbitrary filesystem paths. Small rejected POST bodies are discarded with a bounded timeout so Windows clients can receive the 403 response before connection close.

The real Windows folder chooser, native file associations and double-click launchers are not exercised end to end. A folder path can also be pasted. Live institutional layouts still need the first-download check. At that earlier baseline, student and event pagination, hidden/virtual rows and collapsed details remained unsupported; version 0.13.0 adds recognized student pagination to the web app. Coded free text needs local privacy review; no test certifies FERPA compliance or a data classification change.
