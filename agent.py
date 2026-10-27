"""A small, explicit OpenAI Responses API tool-calling loop."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Any

from tools import TOOL_DEFINITIONS, execute_tool


CATEGORIES = [
    "accessibility assistance",
    "booking issue",
    "refund/payment",
    "general information",
    "service disruption",
]
URGENCIES = ["low", "medium", "high", "critical"]
PROMPT_VERSION = "v3-external-boundaries"

SYSTEM_PROMPT = f"""You are an AI support operations agent.
Classify each ticket, decide which tools are needed, use their results, and write a concise customer-facing response.

Categories: {', '.join(CATEGORIES)}.
Urgencies: {', '.join(URGENCIES)}.

Rules:
- Tool choice must depend on the ticket. Do not call tools that add no value.
- Classify by the operational topic, not by whether the customer asks a general question. Booking change/cancellation policy is "booking issue"; disruption policy/status is "service disruption".
- A request to create or reserve a transportation booking (such as a train, taxi, shuttle, or coach) is "booking issue" even when no booking ID exists yet. A hotel, restaurant, attraction, or other unsupported-domain reservation is "general information"; explain that it is outside this operation's supported services.
- Return/refund policy, starting or checking a refund, rejected cards, payment failures, payment methods, duplicate charges, and unrecognized charges are all "refund/payment".
- Call lookup_booking only when the customer provides an explicit booking ID and booking state matters. Never invent or infer a booking ID.
- Search the knowledge base when policy is required. Do not search it merely to justify an escalation when booking facts and the escalation rules are already sufficient.
- You MUST create an escalation for same-day or within-24-hour booking changes, a missing/invalid booking for travel today, incorrect booking data for travel today, urgent unmet accessibility needs, a currently stranded passenger, a threatened critical connection, suspected duplicate/fraudulent charges, or refunds overdue by more than 10 business days.
- A future service cancellation without current stranding, imminent travel, or a critical connection is not an escalation. Use policy guidance only.
- Never claim an escalation exists unless create_escalation succeeded.
- If a tool fails, explain the safe next step and escalate only when warranted.
- After all tools are complete, return ONLY valid JSON with exactly these fields:
  category, urgency, escalation_required, final_response.
- escalation_required is a boolean. final_response is addressed to the customer.
"""


@dataclass
class AgentResult:
    ticket_id: str
    category: str
    urgency: str
    tools_used: list[str]
    escalation_status: str
    final_response: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SupportAgent:
    def __init__(self, client: Any | None = None, model: str | None = None, max_turns: int = 8):
        if client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "The openai package is required. Run: pip install -r requirements.txt"
                ) from exc
            client = OpenAI()
        self.client = client
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
        self.max_turns = max_turns

    def handle_ticket(self, ticket_id: str, message: str) -> AgentResult:
        if not ticket_id.strip() or not message.strip():
            raise ValueError("ticket_id and message are required")

        input_items: list[Any] = [
            {"role": "user", "content": f"Ticket ID: {ticket_id}\nCustomer message: {message}"}
        ]
        tools_used: list[str] = []
        escalation_created = False

        for _ in range(self.max_turns):
            response = self.client.responses.create(
                model=self.model,
                instructions=SYSTEM_PROMPT,
                input=input_items,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )

            # Preserve all model output items before adding tool results.
            input_items.extend(response.output)
            tool_calls = [item for item in response.output if item.type == "function_call"]

            if not tool_calls:
                return self._build_result(
                    ticket_id, response.output_text, tools_used, escalation_created
                )

            for call in tool_calls:
                try:
                    arguments = json.loads(call.arguments)
                except json.JSONDecodeError as exc:
                    tool_result = {"ok": False, "error": f"Invalid JSON arguments: {exc}"}
                else:
                    tool_result = execute_tool(call.name, arguments)

                tools_used.append(call.name)
                if call.name == "create_escalation" and tool_result.get("ok"):
                    escalation_created = True
                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(tool_result),
                    }
                )

        raise RuntimeError(f"Agent exceeded the {self.max_turns}-turn safety limit")

    @staticmethod
    def _build_result(
        ticket_id: str, output_text: str, tools_used: list[str], escalation_created: bool
    ) -> AgentResult:
        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Model returned invalid final JSON: {exc}") from exc

        missing = {"category", "urgency", "escalation_required", "final_response"} - payload.keys()
        if missing:
            raise RuntimeError(f"Model result is missing fields: {sorted(missing)}")
        if payload["category"] not in CATEGORIES:
            raise RuntimeError(f"Model returned unsupported category: {payload['category']}")
        if payload["urgency"] not in URGENCIES:
            raise RuntimeError(f"Model returned unsupported urgency: {payload['urgency']}")

        requested = bool(payload["escalation_required"])
        if escalation_created:
            escalation_status = "created"
        elif requested:
            escalation_status = "recommended_but_not_created"
        else:
            escalation_status = "not_needed"

        return AgentResult(
            ticket_id=ticket_id,
            category=payload["category"],
            urgency=payload["urgency"],
            tools_used=tools_used,
            escalation_status=escalation_status,
            final_response=payload["final_response"],
        )
