# Validation

Version 0.9.0, October 23, 2026. Windows, Python 3.11.5, Playwright 1.64.1 and installed Microsoft Edge.

All 61 tests passed with none skipped in 85 seconds. The suite includes original collector coverage, HTTP/privacy checks, coded and named download tests, and end-to-end browser workflows using invented records and temporary files/profiles. No live Canvas account, existing browser profile, real student record or name key is used by the tests.

Coded-mode tests verify original event text and elapsed times, start/finish date and clock omission, limited identifier substitutions, random IDs, the separate private key, archive allowlisting, matching capture hashes and preservation of partial downloads.

Named-mode tests verify student names, original start/finish dates and times, original event text, named filenames, named-logs.zip, no random student IDs, no name_key.csv, and no ID/key confirmation. Invalid modes are rejected before the browser starts. Export mode is fixed during a run.

UI tests cover the revised Build → Moderate instructions, the private-key button at the first-log check, the hidden internal readiness setting, About content, modal close/Escape and focus return, and narrow-screen layouts. Native file opening is mocked while verifying the requested key path.

HTTP tests cover loopback binding, authentication, hostile Origin/Host rejection, POST Origin checks, malformed requests, no-store/framing protections and refusal to serve arbitrary filesystem paths. Small rejected POST bodies are discarded with a bounded timeout so Windows clients can receive the 403 response before connection close.

The real Windows folder chooser, native file associations and double-click launchers are not exercised end to end. A folder path can also be pasted. Live institutional layouts still need the first-download check. Student and event pagination, hidden/virtual rows and collapsed details remain unsupported. Coded free text needs local privacy review; no test certifies FERPA compliance or a data classification change.
