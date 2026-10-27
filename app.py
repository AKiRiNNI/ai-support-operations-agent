"""Command-line entry point for the support operations agent."""

from __future__ import annotations

import argparse
import json
import sys

from agent import SupportAgent


def main() -> int:
    parser = argparse.ArgumentParser(description="Process one customer support ticket.")
    parser.add_argument("--ticket-id", required=True)
    parser.add_argument("--message", required=True)
    args = parser.parse_args()

    try:
        result = SupportAgent().handle_ticket(args.ticket_id, args.message)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
