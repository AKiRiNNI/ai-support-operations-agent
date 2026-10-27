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

The separate public-data holdout has not been run yet. When it is run, save the first complete report as `external_holdout_v1.json`. Its only scored metric is category accuracy; tool and escalation behavior are audit-only because the upstream datasets do not contain this project's operational ground truth. See [`EXTERNAL_DATA_METHODOLOGY.md`](../EXTERNAL_DATA_METHODOLOGY.md).
