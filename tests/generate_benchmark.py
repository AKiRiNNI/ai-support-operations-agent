"""Generate a balanced, auditable 60-case support benchmark."""

from __future__ import annotations

import json
from pathlib import Path


GROUPS = {
    "accessibility assistance": [
        ("Please confirm the wheelchair-accessible vehicle on BK-1001.", False, ["lookup_booking"]),
        ("Do you allow trained service animals?", False, ["search_knowledge_base"]),
        ("I need mobility assistance for BK-1001 next month.", False, ["lookup_booking", "search_knowledge_base"]),
        ("My wheelchair assistance is missing and BK-1001 leaves in two hours.", True, ["lookup_booking", "create_escalation"]),
        ("Is accessibility assistance free?", False, ["search_knowledge_base"]),
        ("The accessible vehicle for BK-1001 has not arrived and I am waiting now.", True, ["lookup_booking", "create_escalation"]),
        ("Can I bring a folding mobility scooter?", False, ["search_knowledge_base"]),
        ("I requested accessibility help for BK-9999 but travel is today.", True, ["lookup_booking", "create_escalation"]),
        ("Does BK-1001 show my wheelchair request?", False, ["lookup_booking"]),
        ("I need assistance boarding but my trip is three weeks away.", False, ["search_knowledge_base"]),
        ("A driver refused my service animal and I am stranded on BK-1003.", True, ["lookup_booking", "create_escalation"]),
        ("How early should I request an accessible vehicle?", False, ["search_knowledge_base"]),
    ],
    "booking issue": [
        ("Can I move BK-1001 to another date next month?", False, ["lookup_booking", "search_knowledge_base"]),
        ("I typed the wrong passenger name on BK-1001 and leave tomorrow.", True, ["lookup_booking", "search_knowledge_base", "create_escalation"]),
        ("What is the policy for changing a booking?", False, ["search_knowledge_base"]),
        ("Why does BK-9999 not exist? I travel in three weeks.", False, ["lookup_booking"]),
        ("Please tell me whether BK-1001 is confirmed.", False, ["lookup_booking"]),
        ("BK-1002 was cancelled. Can you confirm its status?", False, ["lookup_booking"]),
        ("I need a same-day change for BK-1001.", True, ["lookup_booking", "search_knowledge_base", "create_escalation"]),
        ("Can I cancel a booking more than 24 hours ahead?", False, ["search_knowledge_base"]),
        ("My booking ID BK-9998 is missing and departure is in one hour.", True, ["lookup_booking", "create_escalation"]),
        ("I want to check the travel date on BK-1003.", False, ["lookup_booking"]),
        ("Can another person use my booking?", False, ["search_knowledge_base"]),
        ("BK-1001 has the wrong date and the shuttle arrives today.", True, ["lookup_booking", "create_escalation"]),
    ],
    "refund/payment": [
        ("When should an approved card refund arrive?", False, ["search_knowledge_base"]),
        ("The refund for BK-1002 was approved 14 business days ago.", True, ["lookup_booking", "search_knowledge_base", "create_escalation"]),
        ("My card was charged twice for BK-1004.", True, ["lookup_booking", "create_escalation"]),
        ("Why did payment fail on BK-1004?", False, ["lookup_booking"]),
        ("How do card refunds work?", False, ["search_knowledge_base"]),
        ("There is a charge I do not recognize for BK-1001.", True, ["lookup_booking", "create_escalation"]),
        ("Has the refund for BK-1002 been marked pending?", False, ["lookup_booking"]),
        ("I was charged the wrong amount and travel is next month.", True, ["create_escalation"]),
        ("Can I pay the driver in cash?", False, ["search_knowledge_base"]),
        ("BK-9999 charged my card but cannot be found.", True, ["lookup_booking", "create_escalation"]),
        ("My refund was approved yesterday. When will it arrive?", False, ["search_knowledge_base"]),
        ("Payment on BK-1004 failed and departure is today.", True, ["lookup_booking", "create_escalation"]),
    ],
    "general information": [
        ("How much luggage can I bring?", False, ["search_knowledge_base"]),
        ("Are oversized suitcases allowed?", False, ["search_knowledge_base"]),
        ("What services do you offer?", False, ["search_knowledge_base"]),
        ("Can I bring one suitcase and a backpack?", False, ["search_knowledge_base"]),
        ("Where can I read your baggage rules?", False, ["search_knowledge_base"]),
        ("Do I need to arrange oversized items ahead of time?", False, ["search_knowledge_base"]),
        ("Tell me about airport shuttle baggage limits.", False, ["search_knowledge_base"]),
        ("What support information is available?", False, ["search_knowledge_base"]),
        ("Can you explain your general luggage policy?", False, ["search_knowledge_base"]),
        ("Is a small personal item included?", False, ["search_knowledge_base"]),
        ("How many bags may each passenger carry?", False, ["search_knowledge_base"]),
        ("I have an oversized sports bag. What should I do?", False, ["search_knowledge_base"]),
    ],
    "service disruption": [
        ("BK-1003 is disrupted and I am stranded right now.", True, ["lookup_booking", "create_escalation"]),
        ("What is your policy for service disruptions?", False, ["search_knowledge_base"]),
        ("Please check the current status of BK-1003.", False, ["lookup_booking"]),
        ("My coach is 20 minutes late on BK-1003.", False, ["lookup_booking"]),
        ("A cancellation will make me miss a critical connection on BK-1003.", True, ["lookup_booking", "create_escalation"]),
        ("What should passengers do after a cancellation?", False, ["search_knowledge_base"]),
        ("BK-1001 is confirmed but the vehicle is not here and I am stranded.", True, ["lookup_booking", "create_escalation"]),
        ("Is BK-1001 still confirmed for next month?", False, ["lookup_booking"]),
        ("My service was cancelled but the trip is three weeks away.", False, ["search_knowledge_base"]),
        ("BK-9999 was cancelled and departure is today.", True, ["lookup_booking", "create_escalation"]),
        ("There is a minor delay and I have no connection to catch.", False, ["search_knowledge_base"]),
        ("The coach broke down and passengers are stranded on BK-1003.", True, ["lookup_booking", "create_escalation"]),
    ],
}


def main() -> None:
    cases = []
    number = 1
    for category, examples in GROUPS.items():
        for message, escalation, tools in examples:
            cases.append(
                {
                    "ticket_id": f"B-{number:03d}",
                    "message": message,
                    "expected_category": category,
                    "expected_escalation": escalation,
                    "expected_tools": tools,
                }
            )
            number += 1
    output = Path(__file__).with_name("benchmark_cases.json")
    output.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(cases)} cases to {output}")


if __name__ == "__main__":
    main()
