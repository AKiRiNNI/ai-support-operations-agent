# Benchmark Results

`benchmark_60.json` is the v1 baseline run on October 27, 2026 using `gpt-5.4-mini`.

Baseline summary:

- 60/60 cases completed; 0% runtime failure rate
- 90.0% category accuracy (54/60)
- 93.3% escalation accuracy (56/60)
- 75.0% exact tool-selection accuracy (45/60)
- 92.9% tool F1
- 65.0% end-to-end pass rate (39/60)

Observed failure patterns:

- Six category errors concentrated in booking-policy, payment-method, and service-disruption boundary cases.
- Three missed urgent booking escalations and one unnecessary future-disruption escalation.
- Extra knowledge-base searches in urgent accessibility and disruption cases.
- Missing policy searches in a small number of booking/accessibility requests.

The v2 prompt was changed only after this baseline was saved. Its result is stored in `benchmark_60_v2.json`.

| Metric | Baseline | v2 |
|---|---:|---:|
| Category accuracy | 90.0% | 93.3% |
| Escalation accuracy | 93.3% | 98.3% |
| Tool exact match | 75.0% | 81.7% |
| Tool F1 | 92.9% | 87.9% |
| End-to-end pass rate | 65.0% | 75.0% |

See [`BENCHMARK_METHODOLOGY.md`](../BENCHMARK_METHODOLOGY.md) for data provenance, labeling rules, metric definitions, and validity limitations.

The public-data external baseline is stored in `external_holdout_v1.json`. It completed 60/60 cases with 0% runtime failures and 61.7% category accuracy: 87.5% on ABCD and 10.0% on MultiWOZ. Its only scored metric is category accuracy; tool and escalation behavior are audit-only because the upstream datasets do not contain this project's operational ground truth.

The low MultiWOZ score exposed an ontology boundary: the v2 prompt covers existing booking problems but not requests to create a new reservation. See [`EXTERNAL_HOLDOUT_ANALYSIS.md`](EXTERNAL_HOLDOUT_ANALYSIS.md) and [`EXTERNAL_DATA_METHODOLOGY.md`](../EXTERNAL_DATA_METHODOLOGY.md).

Prompt `v3-external-boundaries` now assigns new transportation reservations to `booking issue`, unsupported-domain reservations to `general information`, and return/refund policy, refund initiation, rejected cards, and payment failures to `refund/payment`. Save the controlled same-set rerun as `external_development_v3.json`; never overwrite the v1 baseline.

The v3 same-set rerun is stored in `external_development_v3.json`. Category accuracy improved from 61.7% to 90.0% (+28.3 percentage points): ABCD improved from 87.5% to 97.5%, and MultiWOZ improved from 10.0% to 75.0%. One case failed because the model returned invalid final JSON; the agent now retries one malformed final result. See `EXTERNAL_HOLDOUT_ANALYSIS.md` for the six remaining non-passing cases and validity caveats.
