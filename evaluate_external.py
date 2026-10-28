"""Evaluate category generalization on the public-data external holdout."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent import PROMPT_VERSION, SupportAgent


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CASES = PROJECT_DIR / "tests" / "external_holdout_cases.json"


def score_case(case: dict[str, Any], result: Any) -> dict[str, Any]:
    return {
        "ticket_id": case["ticket_id"],
        "source_dataset": case["source"]["dataset"],
        "source_record_id": case["source"]["record_id"],
        "expected_category": case["expected_category"],
        "actual_category": result.category,
        "category_correct": result.category == case["expected_category"],
        "observed_urgency": result.urgency,
        "observed_tools": result.tools_used,
        "observed_escalation_status": result.escalation_status,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    completed = [row for row in rows if "error" not in row]
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    tool_counts: Counter[str] = Counter()
    escalation_count = 0
    for row in rows:
        by_category[row["expected_category"]].append(row)
        by_source[row["source_dataset"]].append(row)
        if "error" not in row:
            tool_counts.update(row["observed_tools"])
            escalation_count += row["observed_escalation_status"] == "created"

    def category_accuracy(group: list[dict[str, Any]]) -> float:
        return sum(bool(row.get("category_correct")) for row in group) / len(group)

    return {
        "cases": total,
        "completed_cases": len(completed),
        "runtime_failure_rate": 1 - len(completed) / total,
        "category_accuracy": category_accuracy(rows),
        "by_category": {
            name: {"cases": len(group), "category_accuracy": category_accuracy(group)}
            for name, group in sorted(by_category.items())
        },
        "by_source": {
            name: {"cases": len(group), "category_accuracy": category_accuracy(group)}
            for name, group in sorted(by_source.items())
        },
        "unscored_decision_audit": {
            "tool_call_counts": dict(sorted(tool_counts.items())),
            "escalations_created": escalation_count,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--ticket-id",
        action="append",
        help="Run only a specific ticket ID; repeat the option for multiple tickets",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if args.ticket_id:
        selected_ids = set(args.ticket_id)
        cases = [case for case in cases if case["ticket_id"] in selected_ids]
        missing_ids = selected_ids - {case["ticket_id"] for case in cases}
        if missing_ids:
            raise SystemExit(f"Unknown ticket IDs: {sorted(missing_ids)}")
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        raise SystemExit("No external cases selected")

    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["ESCALATIONS_FILE"] = str(Path(temp_dir) / "escalations.json")
        agent = SupportAgent()
        for index, case in enumerate(cases, start=1):
            print(f"[{index}/{len(cases)}] {case['ticket_id']}", flush=True)
            try:
                rows.append(score_case(case, agent.handle_ticket(case["ticket_id"], case["message"])))
            except Exception as exc:
                rows.append(
                    {
                        "ticket_id": case["ticket_id"],
                        "source_dataset": case["source"]["dataset"],
                        "expected_category": case["expected_category"],
                        "error": str(exc),
                    }
                )

    report = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": agent.model,
            "prompt_version": PROMPT_VERSION,
            "dataset": str(args.cases),
            "scored_dimensions": ["category"],
            "note": "Tools and escalations are recorded for audit but not scored.",
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
