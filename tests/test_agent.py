import json
import unittest
from types import SimpleNamespace

from agent import SYSTEM_PROMPT, SupportAgent


class FakeResponses:
    """A deterministic model double; the real tool loop remains unchanged."""

    def __init__(self):
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            call = SimpleNamespace(
                type="function_call",
                name="lookup_booking",
                arguments=json.dumps({"booking_id": "BK-1001"}),
                call_id="call_demo_1",
            )
            return SimpleNamespace(output=[call], output_text="")

        tool_outputs = [item for item in kwargs["input"] if isinstance(item, dict) and item.get("type") == "function_call_output"]
        assert tool_outputs
        lookup_result = json.loads(tool_outputs[-1]["output"])
        assert lookup_result["booking"]["accessibility_notes"]
        final = {
            "category": "accessibility assistance",
            "urgency": "medium",
            "escalation_required": False,
            "final_response": "Your wheelchair-accessible vehicle request is confirmed on booking BK-1001.",
        }
        return SimpleNamespace(output=[], output_text=json.dumps(final))


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


class AgentLoopTests(unittest.TestCase):
    def test_prompt_documents_observed_decision_boundaries(self):
        self.assertIn("Classify by the operational topic", SYSTEM_PROMPT)
        self.assertIn("within-24-hour booking changes", SYSTEM_PROMPT)
        self.assertIn("Never invent or infer a booking ID", SYSTEM_PROMPT)

    def test_end_to_end_tool_loop(self):
        result = SupportAgent(client=FakeClient(), model="test-model").handle_ticket(
            "T-DEMO", "Please confirm wheelchair assistance for booking BK-1001."
        )
        self.assertEqual(result.category, "accessibility assistance")
        self.assertEqual(result.tools_used, ["lookup_booking"])
        self.assertEqual(result.escalation_status, "not_needed")
        print("\nEnd-to-end demo result:")
        print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    unittest.main()
