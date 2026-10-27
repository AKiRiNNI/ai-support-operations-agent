"""Local operational tools exposed to the support agent."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent / "data"


def _escalations_path() -> Path:
    """Allow evaluations to isolate write-side effects from demo data."""
    override = os.getenv("ESCALATIONS_FILE")
    return Path(override) if override else DATA_DIR / "escalations.json"


def _read_json(filename: str) -> list[dict[str, Any]]:
    path = DATA_DIR / filename
    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read {filename}: {exc}") from exc
    if not isinstance(data, list):
        raise RuntimeError(f"Expected a JSON list in {filename}")
    return data


def search_knowledge_base(query: str) -> dict[str, Any]:
    """Return up to three knowledge-base articles ranked by simple keyword overlap."""
    if not query or not query.strip():
        return {"ok": False, "error": "query must not be empty", "articles": []}

    query_terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    scored: list[tuple[int, dict[str, Any]]] = []
    for article in _read_json("knowledge_base.json"):
        searchable = " ".join(
            [article["title"], article["content"], *article.get("keywords", [])]
        ).lower()
        score = sum(1 for term in query_terms if term in searchable)
        if score:
            scored.append((score, article))

    matches = [article for _, article in sorted(scored, key=lambda item: item[0], reverse=True)[:3]]
    return {"ok": True, "query": query, "articles": matches}


def lookup_booking(booking_id: str) -> dict[str, Any]:
    """Look up one booking by its case-insensitive ID."""
    normalized_id = booking_id.strip().upper()
    if not normalized_id:
        return {"ok": False, "error": "booking_id must not be empty"}

    for booking in _read_json("bookings.json"):
        if booking["booking_id"].upper() == normalized_id:
            return {"ok": True, "booking": booking}
    return {"ok": False, "error": f"Booking {normalized_id} was not found"}


def create_escalation(ticket_id: str, reason: str, priority: str) -> dict[str, Any]:
    """Persist a new escalation and return its record."""
    if not ticket_id.strip() or not reason.strip():
        return {"ok": False, "error": "ticket_id and reason are required"}
    if priority not in {"low", "medium", "high", "critical"}:
        return {"ok": False, "error": "priority must be low, medium, high, or critical"}

    path = _escalations_path()
    try:
        escalations = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        escalations = []
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read escalation store: {exc}") from exc
    record = {
        "escalation_id": f"ESC-{len(escalations) + 1:04d}",
        "ticket_id": ticket_id,
        "reason": reason,
        "priority": priority,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    escalations.append(record)
    try:
        path.write_text(json.dumps(escalations, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Could not save escalation: {exc}") from exc
    return {"ok": True, "escalation": record}


TOOL_FUNCTIONS = {
    "search_knowledge_base": search_knowledge_base,
    "lookup_booking": lookup_booking,
    "create_escalation": create_escalation,
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "search_knowledge_base",
        "description": "Search support policies and operational guidance relevant to a ticket.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "lookup_booking",
        "description": "Look up booking status, payment state, and accessibility notes.",
        "parameters": {
            "type": "object",
            "properties": {"booking_id": {"type": "string"}},
            "required": ["booking_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "create_escalation",
        "description": "Create a human-operations escalation when the issue cannot be safely resolved automatically.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "reason": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            },
            "required": ["ticket_id", "reason", "priority"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a model-requested tool without allowing arbitrary function execution."""
    function = TOOL_FUNCTIONS.get(name)
    if function is None:
        return {"ok": False, "error": f"Unknown tool: {name}"}
    try:
        return function(**arguments)
    except TypeError as exc:
        return {"ok": False, "error": f"Invalid arguments for {name}: {exc}"}
    except Exception as exc:  # Tool failures must be returned to the model, not crash the loop.
        return {"ok": False, "error": f"{name} failed: {exc}"}
