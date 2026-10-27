# Benchmark Methodology

This document explains where the support data came from, how labels were assigned, what the metrics mean, and what the benchmark cannot prove.

## Data provenance

The benchmark is entirely synthetic. It contains no production customer conversations, personal information, or proprietary company policies.

The original project requirements defined:

- three tools: knowledge search, booking lookup, and escalation creation;
- five suggested support categories;
- local JSON data for bookings, knowledge articles, escalations, and test tickets;
- at least 15 labeled cases with expected category and escalation behavior.

The mock booking records, knowledge-base articles, escalation policy, and ticket wording were then authored specifically for this portfolio project. They are internally consistent examples, not representations of a real transportation company's policies.

## Dataset construction

`tests/benchmark_cases.json` contains 60 cases, balanced across five categories:

| Category | Cases |
|---|---:|
| Accessibility assistance | 12 |
| Booking issue | 12 |
| Refund/payment | 12 |
| General information | 12 |
| Service disruption | 12 |

Nineteen cases are labeled for escalation. Cases were designed from a test matrix rather than sampled randomly. The matrix varies:

- presence or absence of an explicit booking ID;
- valid versus invalid booking IDs;
- policy questions versus booking-specific requests;
- future travel versus same-day or within-24-hour travel;
- low impact versus stranded passengers or threatened critical connections;
- accessibility needs, payment failures, duplicate charges, and overdue refunds;
- whether the next step can be automated or requires a human operator.

Paired boundary cases intentionally differ by one operational factor. For example, a future cancellation without immediate impact is not escalated, while a current cancellation that strands a passenger is escalated.

## Category labeling rubric

Labels represent operational ownership, not sentence form:

- **Accessibility assistance:** wheelchair, mobility, service-animal, boarding-assistance, or accessible-vehicle needs.
- **Booking issue:** booking status, missing records, passenger/date changes, or cancellation/change policy.
- **Refund/payment:** refunds, duplicate or unauthorized charges, payment failures, or payment methods.
- **General information:** requests outside the other operational domains, primarily baggage and general service information.
- **Service disruption:** cancellations, delays, breakdowns, missing vehicles, stranded passengers, or connection risk.

A policy question about changing a booking is therefore labeled `booking issue`, not `general information`.

## Escalation labeling rubric

A case is labeled for escalation when it includes at least one of these conditions:

- a same-day or within-24-hour booking change requiring human action;
- a missing booking or incorrect booking data for travel today;
- an urgent unmet accessibility need;
- a currently stranded passenger or threatened critical connection;
- a suspected duplicate or unauthorized charge;
- a refund overdue by more than 10 business days.

Routine policy questions, confirmed future bookings, minor delays without connection risk, recently approved refunds, and future disruptions without immediate impact are not escalated.

## Expected tool labeling rubric

- `lookup_booking` is expected only when the ticket provides an explicit booking ID and booking state affects the decision.
- `search_knowledge_base` is expected when policy is necessary to answer or decide the case.
- `create_escalation` is expected whenever the escalation rubric applies.

Tool labels are stricter and more subjective than category or escalation labels. An extra knowledge-base lookup may be operationally harmless but still fails exact-match scoring. For that reason the report includes exact match, precision, recall, and F1.

## Metrics

- **Category accuracy:** exact match against the expected category.
- **Escalation accuracy:** whether an escalation was actually created when expected.
- **Tool exact-match rate:** whether the set of called tools exactly equals the expected set.
- **Tool precision/recall/F1:** partial credit for tool selection.
- **Runtime failure rate:** API, parsing, or tool-execution failures.
- **End-to-end pass rate:** category, escalation, and exact tool selection all correct for the same case.

## Experiment history

Both runs used `gpt-5.4-mini` and the same 60 cases.

| Metric | Baseline | v2 prompt | Change |
|---|---:|---:|---:|
| Category accuracy | 90.0% | 93.3% | +3.3 pp |
| Escalation accuracy | 93.3% | 98.3% | +5.0 pp |
| Tool exact match | 75.0% | 81.7% | +6.7 pp |
| Tool F1 | 92.9% | 87.9% | -5.0 pp |
| End-to-end pass rate | 65.0% | 75.0% | +10.0 pp |
| Runtime failure rate | 0.0% | 0.0% | no change |

The v2 prompt clarified operational category boundaries, mandatory urgent-booking escalations, future-disruption handling, and unnecessary policy searches. It improved the primary decision metrics but reduced average tool F1 because several policy cases skipped knowledge search entirely. This regression is retained rather than hidden.

## Validity and limitations

- The labels were created by one project author and were not reviewed by support-domain experts or multiple annotators.
- The dataset is small, synthetic, English-only, and tied to simplified mock policies.
- Model calls are nondeterministic; one run does not establish a confidence interval.
- Customer-response helpfulness, tone, latency, and cost are not scored.
- Exact tool selection is a design preference, not always the only valid operational path.
- Because baseline errors were used to write the v2 prompt, this 60-case set now functions as a development benchmark. v2 results measure iteration on known cases, not independent generalization.

The next rigorous step is a separately authored holdout set that is not inspected or used during prompt refinement, ideally followed by repeated runs and human review.
