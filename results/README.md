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

The v2 prompt was changed only after this baseline was saved. Write the next comparable run to `benchmark_60_v2.json`; do not overwrite the baseline.
