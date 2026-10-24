# Validation

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

The real Windows folder chooser, native file associations and double-click launchers are not exercised end to end. A folder path can also be pasted. Live institutional layouts still need the first-download check. Student and event pagination, hidden/virtual rows and collapsed details remain unsupported. Coded free text needs local privacy review; no test certifies FERPA compliance or a data classification change.
