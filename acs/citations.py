"""
Loads SHIELD Policy Records from ../records/*.yaml and indexes them by
reason_code, so a denial's citation evidence is drawn from the reviewed
record at run time (per spec Stage 7), never hardcoded in agent.py.
"""

import pathlib
import yaml

RECORDS_DIR = pathlib.Path(__file__).parent.parent / "records"


def load_citation_index() -> dict:
    index = {}
    for path in RECORDS_DIR.glob("*.yaml"):
        with open(path) as f:
            record = yaml.safe_load(f)
        reason_code = record.get("reason_code")
        if reason_code:
            index[reason_code] = record
    return index


def format_citation(record: dict) -> str:
    obligation = record["obligation"]
    return (
        f"{record['record_id']} -- {obligation['regulation']} "
        f"{obligation['article']} (source: {obligation['source']}, "
        f"gold standard: {obligation['gold_standard_ref']})"
    )