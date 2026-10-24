"""Invented event sequences with independently specified expected durations."""
import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from event_summary import summarize_text, write_summary

STOP = "Stopped viewing the quiz-taking page..."


def log(*events):
    return "Began [calendar date and clock time omitted]\nElapsed time\nEvent\n" + "\n".join(events)


class EventSummaryTests(unittest.TestCase):
    def test_two_complete_intervals_use_their_own_denominator(self):
        row = summarize_text(log("00:00 Session started.", f"00:10 {STOP}", "00:30 Resumed.",
                                 f"00:40 {STOP}", "01:10 Resumed.", "02:00 Quiz submitted."))
        self.assertEqual(row["total_elapsed_seconds"], 120)
        self.assertEqual(row["stopped_viewing_events"], 2)
        self.assertEqual(row["average_away_seconds"], 25)
        self.assertEqual(row["paired_intervals"], 2)
        self.assertEqual(row["unpaired_stop_events"], 0)
        self.assertEqual(row["notes"], [])

    def test_split_lines_blanks_canvas_word_and_hour_clock(self):
        row = summarize_text(log("00:00:00\n\nSession started", "01:00:10\n\nStopped viewing the Canvas quiz-taking page...",
                                 "01:00:30\nResumed", "01:02:00\nQuiz submitted"))
        self.assertEqual(row["total_elapsed_seconds"], 3720)
        self.assertEqual(row["average_away_seconds"], 20)

    def test_zero_duration_is_different_from_no_away_events(self):
        zero = summarize_text(log("00:00 Session started", f"00:10 {STOP}", "00:10 Resumed", "00:20 Quiz submitted"))
        none = summarize_text(log("00:00 Session started", "00:20 Quiz submitted"))
        self.assertEqual(zero["average_away_seconds"], 0)
        self.assertEqual(zero["paired_intervals"], 1)
        self.assertIsNone(none["average_away_seconds"])
        self.assertEqual(none["stopped_viewing_events"], 0)

    def test_unmatched_stop_does_not_assume_a_return_at_submission(self):
        row = summarize_text(log("00:00 Session started", f"00:10 {STOP}", "00:30 Resumed",
                                 f"00:40 {STOP}", "01:00 Quiz submitted"))
        self.assertEqual(row["stopped_viewing_events"], 2)
        self.assertEqual(row["average_away_seconds"], 20)
        self.assertEqual(row["paired_intervals"], 1)
        self.assertEqual(row["unpaired_stop_events"], 1)

    def test_consecutive_stops_exclude_ambiguous_cluster(self):
        row = summarize_text(log("00:00 Session started", f"00:10 {STOP}", f"00:12 {STOP}", "00:30 Resumed",
                                 f"00:40 {STOP}", "00:45 Resumed", "01:00 Quiz submitted"))
        self.assertEqual(row["stopped_viewing_events"], 3)
        self.assertEqual(row["paired_intervals"], 1)
        self.assertEqual(row["average_away_seconds"], 5)
        self.assertEqual(row["unpaired_stop_events"], 2)
        self.assertTrue(any("Consecutive" in note for note in row["notes"]))

    def test_duplicate_stop_is_not_silently_deduplicated(self):
        row = summarize_text(log("00:00 Session started", f"00:10 {STOP}", f"00:10 {STOP}", "00:30 Resumed", "01:00 Quiz submitted"))
        self.assertEqual(row["stopped_viewing_events"], 2)
        self.assertIsNone(row["average_away_seconds"])

    def test_orphan_return_and_unrelated_events_do_not_invent_pairs(self):
        row = summarize_text(log("00:00 Session started", "00:05 Resumed", f"00:10 {STOP}",
                                 "00:15 Answered question 2", "00:30 Resumed", "00:40 Quiz submitted"))
        self.assertEqual(row["average_away_seconds"], 20)
        self.assertTrue(any("without a preceding" in note for note in row["notes"]))

    def test_missing_submission_uses_last_observed_value_with_explicit_note(self):
        row = summarize_text(log("00:00 Session started", f"00:10 {STOP}", "00:30 Resumed", "00:50 Answered question"))
        self.assertEqual(row["total_elapsed_seconds"], 50)
        self.assertEqual(row["elapsed_basis"], "last visible event")
        self.assertTrue(any("not a verified total" in note for note in row["notes"]))

    def test_post_submission_focus_events_are_excluded(self):
        row = summarize_text(log("00:00 Session started", "01:00 Quiz submitted", f"01:10 {STOP}", "01:30 Resumed"))
        self.assertEqual(row["total_elapsed_seconds"], 60)
        self.assertEqual(row["stopped_viewing_events"], 0)
        self.assertIsNone(row["average_away_seconds"])

    def test_invalid_or_mixed_order_times_do_not_generate_durations(self):
        for events in (("00:00 Session started", f"00:20 {STOP}", "00:10 Resumed"),
                       ("00:00 Session started", f"00:99 {STOP}", "01:00 Resumed"),
                       ("00:00 Session started", "00:xx Resumed", f"00:10 {STOP}")):
            with self.subTest(events=events):
                row = summarize_text(log(*events))
                self.assertIsNone(row["total_elapsed_seconds"])
                self.assertIsNone(row["average_away_seconds"])
                self.assertTrue(any("timestamps" in note for note in row["notes"]))

    def test_descending_rows_are_reversed(self):
        row = summarize_text(log("01:00 Quiz submitted", "00:30 Resumed", f"00:10 {STOP}", "00:00 Session started"))
        self.assertEqual(row["average_away_seconds"], 20)
        self.assertEqual(row["total_elapsed_seconds"], 60)

    def test_conflicting_submission_times_leave_durations_unknown(self):
        row = summarize_text(log("00:00 Session started", "01:00 Quiz submitted", "02:00 Quiz submitted"))
        self.assertIsNone(row["total_elapsed_seconds"])
        self.assertIsNone(row["average_away_seconds"])

    def test_unrecognized_format_is_unknown_not_zero(self):
        for text in ("No event text", "Elapsed time\nNothing loaded", log("Elapsed time", "00:00 Session started")):
            row = summarize_text(text)
            self.assertIsNone(row["stopped_viewing_events"])
            self.assertIsNone(row["average_away_seconds"])
            self.assertTrue(row["notes"])

    def test_csv_keeps_names_private_and_formula_safe_and_blank_unknowns(self):
        row = summarize_text(log("00:00 Session started", "01:00 Quiz submitted"))
        row.update(student_name="=Synthetic Student", position=2, record_id="R-0123456789abcdef")
        with tempfile.TemporaryDirectory() as temp:
            write_summary(temp, [row])
            with (Path(temp) / "event_summary.csv").open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["Student name"], "'=Synthetic Student")
            self.assertEqual(rows[0]["Average away time (seconds)"], "")
            self.assertEqual(rows[0]["Total elapsed time (HH:MM:SS)"], "00:01:00")
            self.assertTrue((Path(temp) / "summary_method.txt").is_file())
