"""Load the BNS<->IPC mapping table from JSON into Postgres.

Idempotent: safe to run repeatedly. Existing rows are updated, not duplicated.
Run from the backend/ directory:  python -m scripts.seed_bns_mapping
"""

import json
from pathlib import Path

from app.db.session import SessionLocal  # adjust if your session lives elsewhere
from app.models import BnsMapping

DATA_FILE = (
    Path(__file__).resolve().parent.parent / "app" / "data" / "bns_ipc_mapping.json"
)


def normalise(section: str | None, prefix: str) -> str | None:
    """'318(4)' -> 'BNS_318_4'   |   '420' -> 'IPC_420'   |   None -> None"""
    if section is None:
        return None
    cleaned = section.replace("(", "_").replace(")", "").strip()
    return f"{prefix}_{cleaned}"


def seed() -> None:
    rows = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    session = SessionLocal()
    inserted = updated = 0

    try:
        for row in rows:
            ipc_tag = normalise(row.get("ipc"), "IPC")
            bns_tag = normalise(row.get("bns"), "BNS")

            existing = (
                session.query(BnsMapping)
                .filter(
                    BnsMapping.ipc_section == ipc_tag,
                    BnsMapping.bns_section == bns_tag,
                )
                .first()
            )

            if existing:
                existing.offence = row["offence"]
                existing.category = row.get("category")
                existing.change_type = row.get("status", "renumbered")
                updated += 1
            else:
                session.add(
                    BnsMapping(
                        ipc_section=ipc_tag,
                        bns_section=bns_tag,
                        offence=row["offence"],
                        category=row.get("category"),
                        change_type=row.get("status", "renumbered"),
                    )
                )
                inserted += 1

        session.commit()
        print(f"Seed complete. inserted={inserted} updated={updated} total={len(rows)}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
