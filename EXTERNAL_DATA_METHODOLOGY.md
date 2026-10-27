# External Holdout Methodology

This document describes the public-data holdout used to test category generalization beyond the synthetic development benchmark.

## Purpose

The 60 synthetic cases in `tests/benchmark_cases.json` were inspected during prompt refinement. They are therefore a development benchmark, not an independent test of generalization.

`tests/external_holdout_cases.json` adds 60 previously unseen public-dataset examples. It is not used for prompt writing or model training. Once its results are inspected, future prompt changes should be evaluated on a newly created holdout.

## Sources

### ABCD v1.1

- Upstream: [ASAPP Research Action-Based Conversations Dataset](https://github.com/asappresearch/abcd)
- Pinned commit: `6b8700ce67c6b37b062dd7a60abc76d7ef832a97`
- Upstream split: `test`
- License: MIT
- Use here: 20 refund/payment cases and 20 general-information cases

ABCD contains human-to-human customer-service dialogues collected around simulated e-commerce scenarios and explicit policies. It is more realistic than template-generated tickets, but it is not production customer data.

### MultiWOZ 2.2

- Upstream: [MultiWOZ](https://github.com/budzianowski/multiwoz)
- Pinned commit: `fe0c8e65cfcd8462bd33c86e35f21addc84ca82b`
- Upstream split/file: `test/dialogues_001.json`
- License: MIT
- Use here: 20 booking cases involving trains, taxis, or hotels

MultiWOZ contains human-human Wizard-of-Oz task-oriented dialogues. It includes realistic booking language, but it is not a customer-support production log.

Full license notices are retained in `data/external/licenses/`.

## Reproducible construction

Run:

```bash
python scripts/build_external_holdout.py
```

The script downloads files from commit-pinned URLs, verifies SHA-256 checksums, uses only official test splits, and selects cases deterministically. Downloads are cached under `.cache/external_datasets/` and are not committed.

ABCD messages use the first non-greeting delexed customer turn. Scenario profile values are replaced with placeholders, and later identity-verification turns are excluded. MultiWOZ wording is unchanged except for whitespace normalization. Every output case stores its source dataset, record ID, original label or intent, upstream commit, license, and transformation.

## Project label mapping

The original datasets do not use this project's five-category ontology. The project adds a mapping layer:

- ABCD refund, disputed-charge, payment-failure, and return-policy flows map to `refund/payment`.
- ABCD store-wide membership, pricing, and timing questions map to `general information`.
- MultiWOZ train, taxi, and hotel reservation requests map to `booking issue`.

These are project-authored labels, not original dataset ground truth. Source labels are preserved separately so the mapping can be audited.

## Evaluation scope

Only category accuracy is scored. Tool calls, urgency, and escalation decisions are recorded for exploratory review but are not marked correct or incorrect because:

- the upstream datasets do not supply this project's tool or escalation labels;
- public cases do not reference the local mock booking database;
- creating those labels after seeing model output would contaminate the holdout.

Run a three-case smoke test before the complete paid API run:

```bash
python evaluate_external.py --limit 3 --output results/external_holdout_smoke_3.json
python evaluate_external.py --output results/external_holdout_v1.json
```

## Coverage and limitations

- The first external holdout covers three categories only: booking issue, refund/payment, and general information.
- Accessibility assistance and service disruption still rely on synthetic cases until suitable licensed sources are added.
- The domains differ: ABCD is e-commerce, MultiWOZ is travel planning, and the project mock operation is transportation support.
- Dataset authors created the conversations under research protocols; they are not private company logs.
- The mapping was written by one project author and has not undergone inter-annotator review.
- This dataset is suitable for external robustness evaluation, not for claiming production accuracy.
