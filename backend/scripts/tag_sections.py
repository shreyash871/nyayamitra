"""Extract statutory section references from each judgment into jsonb_meta.

python -m scripts.tag_sections
"""

import argparse

from sqlalchemy.orm.attributes import flag_modified

from app.db.session import SessionLocal
from app.models import Judgment
from app.services.bns_bridge import extract_sections, expand
from app.services.text_clean import clean


def run(source: str, limit: int | None, retag: bool) -> None:
    session = SessionLocal()
    tagged = skipped = 0
    total_tags = 0

    try:
        query = session.query(Judgment).filter(Judgment.source == source)
        if limit:
            query = query.limit(limit)

        for judgment in query.all():
            meta = judgment.jsonb_meta or {}
            if "sections" in meta and not retag:
                skipped += 1
                continue
            if not judgment.full_text:
                continue

            found = extract_sections(clean(judgment.full_text))

            # Expand each tag across both statutory eras
            expanded: list[str] = []
            for tag in found:
                expanded.extend(expand(session, tag))
            expanded = list(dict.fromkeys(expanded))

            meta["sections"] = found
            meta["sections_expanded"] = expanded
            judgment.jsonb_meta = meta
            flag_modified(judgment, "jsonb_meta")

            tagged += 1
            total_tags += len(found)
            session.commit()

        print(
            f"Done. tagged={tagged} skipped={skipped} "
            f"avg_sections={total_tags / max(tagged, 1):.1f}"
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="ildc")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--retag", action="store_true")
    a = p.parse_args()
    run(a.source, a.limit, a.retag)
