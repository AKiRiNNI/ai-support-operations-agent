"""Build a provenance-tracked external category holdout from public datasets."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import urllib.request
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_DIR / "tests" / "external_holdout_cases.json"
DEFAULT_CACHE = PROJECT_DIR / ".cache" / "external_datasets"

SOURCES = {
    "abcd": {
        "filename": "abcd_v1.1.json.gz",
        "url": (
            "https://raw.githubusercontent.com/asappresearch/abcd/"
            "6b8700ce67c6b37b062dd7a60abc76d7ef832a97/data/abcd_v1.1.json.gz"
        ),
        "sha256": "2bdf53ac359543dcdc38d55bc6513e78df120363f8f44870716e909f4606de15",
        "commit": "6b8700ce67c6b37b062dd7a60abc76d7ef832a97",
        "license": "MIT",
    },
    "multiwoz": {
        "filename": "multiwoz_test_001.json",
        "url": (
            "https://raw.githubusercontent.com/budzianowski/multiwoz/"
            "fe0c8e65cfcd8462bd33c86e35f21addc84ca82b/"
            "data/MultiWOZ_2.2/test/dialogues_001.json"
        ),
        "sha256": "d6f43876cf130fdb2dfa8f96bc056b0995354137f02122e004925d01264ed386",
        "commit": "fe0c8e65cfcd8462bd33c86e35f21addc84ca82b",
        "license": "MIT",
    },
}

ABCD_REFUND_SUBFLOWS = {
    ("manage_account", "manage_payment_method"),
    ("product_defect", "refund_initiate"),
    ("product_defect", "refund_status"),
    ("product_defect", "refund_update"),
    ("purchase_dispute", "mistimed_billing_already_returned"),
    ("purchase_dispute", "mistimed_billing_never_bought"),
    ("storewide_query", "policy_1"),
    ("storewide_query", "policy_2"),
    ("subscription_inquiry", "manage_dispute_bill"),
    ("troubleshoot_site", "credit_card"),
}
ABCD_GENERAL_FLOWS = {"membership", "pricing", "timing"}
REFUND_WORDS = re.compile(
    r"\b(refund|return|charge|charged|billing|bill|credit card|payment|purchase)\b",
    re.IGNORECASE,
)
GENERAL_WORDS = re.compile(
    r"\b(price|cost|when|hours?|benefits?|membership|shipping|promo|collection|store)\b",
    re.IGNORECASE,
)
BOOKING_WORDS = re.compile(r"\b(book|booking|reservation|reserve)\w*\b", re.IGNORECASE)
GREETING = re.compile(
    r"^(hi|hi!|hello|hello!|hey|good (morning|afternoon|evening)[!.]?)$",
    re.IGNORECASE,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def obtain_source(cache_dir: Path, source: dict[str, str], offline: bool) -> Path:
    path = cache_dir / source["filename"]
    if not path.exists():
        if offline:
            raise FileNotFoundError(f"Offline source not found: {path}")
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {source['url']}")
        urllib.request.urlretrieve(source["url"], path)
    actual = sha256(path)
    if actual != source["sha256"]:
        raise ValueError(f"Checksum mismatch for {path}: expected {source['sha256']}, got {actual}")
    return path


def redact_scenario_values(text: str, scenario: dict[str, Any]) -> str:
    replacements: list[tuple[str, str]] = []
    for section_name in ("personal", "order"):
        for key, value in scenario.get(section_name, {}).items():
            if isinstance(value, str) and len(value.strip()) >= 4:
                replacements.append((value.strip(), f"<{key}>"))
    for value, placeholder in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        text = re.sub(re.escape(value), placeholder, text, flags=re.IGNORECASE)
    return text


def abcd_message(row: dict[str, Any]) -> str:
    for turn in row["delexed"]:
        if turn["speaker"] != "customer":
            continue
        text = " ".join(turn["text"].split())
        if not text or GREETING.fullmatch(text):
            continue
        return redact_scenario_values(text, row["scenario"])[:500].strip()
    return ""


def round_robin(rows: Iterable[dict[str, Any]], count: int, label_key: str) -> list[dict[str, Any]]:
    groups: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for row in rows:
        groups[row[label_key]].append(row)
    selected = []
    labels = sorted(groups)
    while labels and len(selected) < count:
        remaining = []
        for label in labels:
            if groups[label] and len(selected) < count:
                selected.append(groups[label].popleft())
            if groups[label]:
                remaining.append(label)
        labels = remaining
    if len(selected) != count:
        raise ValueError(f"Needed {count} cases but found {len(selected)}")
    return selected


def build_abcd_cases(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        rows = json.load(handle)["test"]

    candidates: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        scenario = row["scenario"]
        flow = scenario["flow"]
        subflow = scenario["subflow"]
        source_label = f"{flow}/{subflow}"
        message = abcd_message(row)
        base = {"row": row, "message": message, "source_label": source_label}
        if (flow, subflow) in ABCD_REFUND_SUBFLOWS and REFUND_WORDS.search(message):
            candidates["refund/payment"].append(base)
        if flow == "storewide_query" and subflow.split("_", 1)[0] in ABCD_GENERAL_FLOWS:
            if GENERAL_WORDS.search(message):
                candidates["general information"].append(base)

    cases = []
    for category in ("refund/payment", "general information"):
        ordered = sorted(candidates[category], key=lambda item: int(item["row"]["convo_id"]))
        selected = round_robin(ordered, 20, "source_label")
        for item in selected:
            row = item["row"]
            cases.append(
                {
                    "ticket_id": f"EXT-ABCD-{row['convo_id']}",
                    "message": item["message"],
                    "expected_category": category,
                    "evaluation_scope": ["category"],
                    "source": {
                        "dataset": "ABCD v1.1",
                        "split": "test",
                        "record_id": str(row["convo_id"]),
                        "source_label": item["source_label"],
                        "upstream_commit": SOURCES["abcd"]["commit"],
                        "license": SOURCES["abcd"]["license"],
                        "transformation": "First non-greeting delexed customer turn; profile values replaced.",
                    },
                }
            )
    return cases


def active_intent(turn: dict[str, Any]) -> str:
    for frame in turn["frames"]:
        intent = frame.get("state", {}).get("active_intent")
        if intent and intent != "NONE":
            return intent
    return "unknown"


def build_multiwoz_cases(path: Path) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    candidates = []
    for dialogue in rows:
        first_user = next(turn for turn in dialogue["turns"] if turn["speaker"] == "USER")
        message = " ".join(first_user["utterance"].split())
        if not BOOKING_WORDS.search(message):
            continue
        if not set(dialogue["services"]) & {"train", "taxi", "hotel"}:
            continue
        candidates.append((dialogue, first_user, message))

    cases = []
    for dialogue, turn, message in sorted(candidates, key=lambda item: item[0]["dialogue_id"])[:20]:
        dialogue_id = dialogue["dialogue_id"]
        cases.append(
            {
                "ticket_id": f"EXT-MWOZ-{dialogue_id.removesuffix('.json')}",
                "message": message,
                "expected_category": "booking issue",
                "evaluation_scope": ["category"],
                "source": {
                    "dataset": "MultiWOZ 2.2",
                    "split": "test",
                    "record_id": dialogue_id,
                    "source_turn_id": turn["turn_id"],
                    "source_label": active_intent(turn),
                    "upstream_commit": SOURCES["multiwoz"]["commit"],
                    "license": SOURCES["multiwoz"]["license"],
                    "transformation": "Whitespace normalized; wording unchanged.",
                },
            }
        )
    if len(cases) != 20:
        raise ValueError(f"Needed 20 MultiWOZ cases but found {len(cases)}")
    return cases


def validate(cases: list[dict[str, Any]]) -> None:
    if len(cases) != 60:
        raise ValueError(f"Expected 60 cases, got {len(cases)}")
    ids = [case["ticket_id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Ticket IDs must be unique")
    counts: dict[str, int] = defaultdict(int)
    for case in cases:
        counts[case["expected_category"]] += 1
    expected = {"booking issue": 20, "refund/payment": 20, "general information": 20}
    if dict(counts) != expected:
        raise ValueError(f"Unexpected category counts: {dict(counts)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--offline", action="store_true", help="Require already-cached source files")
    args = parser.parse_args()

    abcd_path = obtain_source(args.cache_dir, SOURCES["abcd"], args.offline)
    multiwoz_path = obtain_source(args.cache_dir, SOURCES["multiwoz"], args.offline)
    cases = build_abcd_cases(abcd_path) + build_multiwoz_cases(multiwoz_path)
    cases.sort(key=lambda case: case["ticket_id"])
    validate(cases)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(cases, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(cases)} external holdout cases to {args.output}")


if __name__ == "__main__":
    main()
