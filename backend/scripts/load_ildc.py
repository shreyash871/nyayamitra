"""Load ILDC judgments into the judgments table.

Smoke test:  python -m scripts.load_ildc --limit 10
Full ingest: python -m scripts.load_ildc --split multi_train
"""

import argparse
import re

from datasets import load_dataset

from app.db.session import SessionLocal
from app.models import Judgment

DATASET = "Exploration-Lab/IL-TUR"
CONFIG = "cjpe"
COURT = "Supreme Court of India"  # ILDC is Supreme Court only
LABEL_NAMES = {0: "REJECTED", 1: "ACCEPTED"}

# "Civil Appeal No. 57 of 1950", "Criminal Appeal No. 12 of 1998"
CASE_NO_PATTERN = re.compile(
    r"((?:Civil|Criminal)\s+Appeal\s+No\.?\s*\d+\s+of\s+\d{4})",
    re.IGNORECASE,
)


def parse_year(ildc_id: str) -> int | None:
    """'1951_10' -> 1951"""
    head = ildc_id.split("_")[0]
    return int(head) if head.isdigit() and len(head) == 4 else None


def parse_case_no(text: str) -> str | None:
    """Best-effort: the case number sits in the prose, not a field."""
    match = CASE_NO_PATTERN.search(text[:1000])
    return match.group(1).strip() if match else None


def load(split: str, limit: int | None) -> None:
    spec = f"{split}[:{limit}]" if limit else split
    print(f"Loading {DATASET} / {CONFIG} / {spec} ...")
    rows = load_dataset(DATASET, CONFIG, split=spec)

    session = SessionLocal()
    inserted = skipped = 0

    try:
        for row in rows:
            ildc_id = row["id"]

            exists = (
                session.query(Judgment.id)
                .filter(Judgment.source == "ildc", Judgment.source_id == ildc_id)
                .first()
            )
            if exists:
                skipped += 1
                continue

            text = row["text"]
            session.add(
                Judgment(
                    court=COURT,
                    case_no=parse_case_no(text),
                    title=None,  # ILDC has no title field
                    judgment_date=None,  # year only, see jsonb_meta
                    full_text=text,
                    source="ildc",
                    source_id=ildc_id,
                    year=parse_year(ildc_id),
                    jsonb_meta={
                        "ildc_split": split,
                        "outcome": LABEL_NAMES.get(row["label"]),
                        "char_len": len(text),
                    },
                )
            )
            inserted += 1

        session.commit()
        print(f"Done. inserted={inserted} skipped={skipped} total={len(rows)}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="multi_train")
    parser.add_argument("--limit", type=int, default=None)
    load(*vars(parser.parse_args()).values())
