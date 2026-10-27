import unittest
from types import SimpleNamespace

from evaluate import score_case, summarize


class EvaluationTests(unittest.TestCase):
    def test_scores_exact_tool_match(self):
        case = {
            "ticket_id": "T-1",
            "expected_category": "booking issue",
            "expected_escalation": False,
            "expected_tools": ["lookup_booking"],
        }
        result = SimpleNamespace(
            category="booking issue",
            escalation_status="not_needed",
            tools_used=["lookup_booking"],
        )
        row = score_case(case, result)
        self.assertTrue(row["tool_exact_match"])
        self.assertEqual(row["tool_f1"], 1.0)

    def test_summary_counts_end_to_end_pass(self):
        rows = [
            {
                "expected_category": "booking issue",
                "category_correct": True,
                "escalation_correct": True,
                "tool_exact_match": True,
                "tool_precision": 1.0,
                "tool_recall": 1.0,
                "tool_f1": 1.0,
            },
            {
                "expected_category": "booking issue",
                "category_correct": True,
                "escalation_correct": True,
                "tool_exact_match": False,
                "tool_precision": 0.5,
                "tool_recall": 1.0,
                "tool_f1": 2 / 3,
            },
        ]
        summary = summarize(rows)
        self.assertEqual(summary["end_to_end_pass_rate"], 0.5)
        self.assertEqual(summary["tool_exact_match_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
