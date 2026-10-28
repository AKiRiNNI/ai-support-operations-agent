# External Holdout v1 Analysis

The first complete external run used `gpt-5.4-mini`, prompt `v2-decision-boundaries`, and all 60 cases in `tests/external_holdout_cases.json`.

## Results

| Slice | Correct | Accuracy |
|---|---:|---:|
| Overall | 37/60 | 61.7% |
| ABCD v1.1 | 35/40 | 87.5% |
| MultiWOZ 2.2 | 2/20 | 10.0% |
| General information | 20/20 | 100.0% |
| Refund/payment | 15/20 | 75.0% |
| Booking issue | 2/20 | 10.0% |

All 60 cases completed successfully, so the runtime failure rate was 0%.

## Confusion pattern

Every category error became `general information`:

| Expected | Predicted correctly | Predicted as general information |
|---|---:|---:|
| Booking issue | 2 | 18 |
| Refund/payment | 15 | 5 |
| General information | 20 | 0 |

This is a systematic fallback pattern rather than random label noise.

## Root-cause analysis

### New reservations versus booking issues

Eighteen of twenty MultiWOZ reservation requests were classified as `general information`. The v2 prompt explicitly assigns booking changes, cancellations, status, and missing records to `booking issue`, but it does not state where a request to create a new reservation belongs.

The external mapping labels new train, taxi, hotel, restaurant, and attraction reservations as `booking issue`. Four of those cases are also outside the mock transportation operation's obvious service domain. The 10% score therefore combines a real prompt boundary gap with a dataset-to-project ontology mismatch.

### Refund and payment boundaries

Five of twenty ABCD refund/payment cases were classified as `general information`:

- three return-policy questions;
- one explicit refund request;
- one rejected-credit-card case.

The prompt names payment methods and refunds but does not explicitly cover return policy, refund initiation, or card rejection. These examples expose another decision boundary that was rare in the synthetic development set.

## Unscored operational behavior

The agent made 28 knowledge-base searches and four escalations. The four escalations corresponded to two duplicate charges and two unrecognized purchases, which is directionally consistent with the escalation rubric. No booking lookup occurred because the public examples contain no local `BK-...` IDs.

These observations are useful for audit but are not accuracy claims because the upstream datasets do not provide this project's tool or escalation ground truth.

## Interpretation

The 61.7% result should be retained as an honest external baseline. It does not replace the synthetic development metrics because the two benchmarks measure different things:

- the synthetic benchmark tests the complete local workflow, including tool and escalation decisions;
- the external benchmark tests category transfer across different wording and domains.

Because these results have now been inspected, this v1 external set is no longer a blind holdout for future prompt changes. A v3 prompt may use the identified failure patterns for development, but its generalization claim requires a second, untouched external set.

## Recommended next experiment

1. Clarify whether new reservations belong to `booking issue` and whether unsupported domains should be rejected or classified separately.
2. Explicitly assign return policy, refund initiation, and card rejection to `refund/payment`.
3. Measure the same 60 cases again only as a controlled before/after development comparison.
4. Evaluate the revised prompt on a new external holdout drawn from different ABCD records and the untouched second MultiWOZ test file.

## v3 controlled development rerun

Prompt `v3-external-boundaries` was evaluated on the same 60 cases after the v1 errors were inspected. This is a before/after development comparison, not an independent generalization result.

| Metric | v2 external baseline | v3 same-set rerun | Change |
|---|---:|---:|---:|
| Category accuracy | 61.7% (37/60) | 90.0% (54/60) | +28.3 pp |
| ABCD accuracy | 87.5% | 97.5% | +10.0 pp |
| MultiWOZ accuracy | 10.0% | 75.0% | +65.0 pp |
| Runtime failure rate | 0.0% | 1.7% (1/60) | +1 failure |

Seventeen previously incorrect cases became correct, and no previously correct case became a classification error. The six non-passing cases were:

- four expected ontology mismatches where hotel, restaurant, or attraction reservations remain labeled `booking issue` by the dataset mapping but are intentionally treated as unsupported-domain `general information` by v3;
- one explicit refund request still classified as `general information`;
- one train-booking case that returned invalid final JSON instead of a parseable result.

The invalid-JSON failure motivated a single automatic format-repair retry in the agent loop. The retry is an operational reliability change and must be verified separately; it does not retroactively change the saved 90.0% report.
