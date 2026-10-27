import json
import re
import unittest
from pathlib import Path
from types import SimpleNamespace

from evaluate_external import score_case, summarize


PROJECT_DIR = Path(__file__).resolve().parents[1]


class ExternalEvaluationTests(unittest.TestCase):
    def test_external_dataset_is_balanced_and_auditable(self):
        cases = json.loads(
            (PROJECT_DIR / "tests" / "external_holdout_cases.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(cases), 60)
        self.assertEqual(len({case["ticket_id"] for case in cases}), 60)
        counts = {
            category: sum(case["expected_category"] == category for case in cases)
            for category in {case["expected_category"] for case in cases}
        }
        self.assertEqual(
            counts,
            {"booking issue": 20, "refund/payment": 20, "general information": 20},
        )
        for case in cases:
            self.assertEqual(case["evaluation_scope"], ["category"])
            self.assertTrue(case["message"].strip())
            self.assertIn("record_id", case["source"])
            self.assertIn("upstream_commit", case["source"])
            self.assertIn("license", case["source"])
            self.assertIsNone(re.search(r"[\w.+-]+@[\w.-]+", case["message"]))
            self.assertIsNone(re.search(r"\b\d{7,}\b", case["message"]))

    def test_scores_only_category_as_ground_truth(self):
        case = {
            "ticket_id": "EXT-1",
            "expected_category": "booking issue",
            "source": {"dataset": "Example", "record_id": "1"},
        }
        result = SimpleNamespace(
            category="booking issue",
            urgency="low",
            tools_used=["search_knowledge_base"],
            escalation_status="not_needed",
        )
        row = score_case(case, result)
        self.assertTrue(row["category_correct"])
        self.assertNotIn("tool_correct", row)
        self.assertNotIn("escalation_correct", row)

    def test_summary_separates_scored_and_unscored_fields(self):
        rows = [
            {
                "expected_category": "booking issue",
                "source_dataset": "MultiWOZ 2.2",
                "category_correct": True,
                "observed_tools": ["search_knowledge_base"],
                "observed_escalation_status": "not_needed",
            },
            {
                "expected_category": "refund/payment",
                "source_dataset": "ABCD v1.1",
                "category_correct": False,
                "observed_tools": ["create_escalation"],
                "observed_escalation_status": "created",
            },
        ]
        summary = summarize(rows)
        self.assertEqual(summary["category_accuracy"], 0.5)
        self.assertEqual(summary["unscored_decision_audit"]["escalations_created"], 1)


if __name__ == "__main__":
    unittest.main()
