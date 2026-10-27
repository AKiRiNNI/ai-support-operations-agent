"""Run a reproducible benchmark against the live OpenAI-powered agent."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent import SupportAgent


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CASES = PROJECT_DIR / "tests" / "benchmark_cases.json"


def score_case(case: dict[str, Any], result: Any) -> dict[str, Any]:
    predicted_escalation = result.escalation_status == "created"
    expected_tools = set(case["expected_tools"])
    actual_tools = set(result.tools_used)
    intersection = expected_tools & actual_tools
    precision = len(intersection) / len(actual_tools) if actual_tools else float(not expected_tools)
    recall = len(intersection) / len(expected_tools) if expected_tools else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "ticket_id": case["ticket_id"],
        "expected_category": case["expected_category"],
        "actual_category": result.category,
        "category_correct": result.category == case["expected_category"],
        "expected_escalation": case["expected_escalation"],
        "actual_escalation": predicted_escalation,
        "escalation_correct": predicted_escalation == case["expected_escalation"],
        "expected_tools": sorted(expected_tools),
        "tools_used": result.tools_used,
        "tool_exact_match": actual_tools == expected_tools,
        "tool_precision": precision,
        "tool_recall": recall,
        "tool_f1": f1,
        "missing_tools": sorted(expected_tools - actual_tools),
        "unexpected_tools": sorted(actual_tools - expected_tools),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    successful = [row for row in rows if "error" not in row]
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_category[row["expected_category"]].append(row)

    def average(field: str) -> float:
        return sum(float(row.get(field, 0)) for row in rows) / total

    return {
        "cases": total,
        "completed_cases": len(successful),
        "runtime_failure_rate": 1 - len(successful) / total,
        "category_accuracy": average("category_correct"),
        "escalation_accuracy": average("escalation_correct"),
        "tool_exact_match_rate": average("tool_exact_match"),
        "tool_precision": average("tool_precision"),
        "tool_recall": average("tool_recall"),
        "tool_f1": average("tool_f1"),
        "end_to_end_pass_rate": sum(
            bool(row.get("category_correct"))
            and bool(row.get("escalation_correct"))
            and bool(row.get("tool_exact_match"))
            for row in rows
        ) / total,
        "by_category": {
            category: {
                "cases": len(category_rows),
                "category_accuracy": sum(bool(row.get("category_correct")) for row in category_rows)
                / len(category_rows),
                "escalation_accuracy": sum(bool(row.get("escalation_correct")) for row in category_rows)
                / len(category_rows),
                "tool_exact_match_rate": sum(bool(row.get("tool_exact_match")) for row in category_rows)
                / len(category_rows),
            }
            for category, category_rows in sorted(by_category.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate category, escalation, and tool selection.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="Benchmark JSON file")
    parser.add_argument("--limit", type=int, help="Run only the first N cases")
    parser.add_argument("--output", type=Path, help="Where to save the JSON report")
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        raise SystemExit("No test cases selected")

    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["ESCALATIONS_FILE"] = str(Path(temp_dir) / "escalations.json")
        agent = SupportAgent()
        for index, case in enumerate(cases, start=1):
            print(f"[{index}/{len(cases)}] {case['ticket_id']}", flush=True)
            try:
                result = agent.handle_ticket(case["ticket_id"], case["message"])
                rows.append(score_case(case, result))
            except Exception as exc:
                rows.append(
                    {
                        "ticket_id": case["ticket_id"],
                        "expected_category": case["expected_category"],
                        "error": str(exc),
                    }
                )

    report = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": agent.model,
            "dataset": str(args.cases),
        },
        "summary": summarize(rows),
        "details": rows,
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Saved report to {args.output}")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
