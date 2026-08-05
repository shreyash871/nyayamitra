"""Chunk judgments and populate judgment_chunks.

python -m scripts.build_chunks --limit 10
python -m scripts.build_chunks --source ildc
"""

import argparse

from app.db.session import SessionLocal
from app.models import Judgment, JudgmentChunk
from app.services.text_clean import clean
from app.services.chunker import chunk


def build(source: str, limit: int | None, rebuild: bool) -> None:
    session = SessionLocal()
    judgments_done = chunks_made = skipped = 0

    try:
        query = session.query(Judgment).filter(Judgment.source == source)
        if limit:
            query = query.limit(limit)

        for judgment in query.all():
            existing = (
                session.query(JudgmentChunk.id)
                .filter(JudgmentChunk.judgment_id == judgment.id)
                .first()
            )
            if existing and not rebuild:
                skipped += 1
                continue
            if existing and rebuild:
                session.query(JudgmentChunk).filter(
                    JudgmentChunk.judgment_id == judgment.id
                ).delete()

            if not judgment.full_text:
                continue

            cleaned = clean(judgment.full_text)
            ratio = len(cleaned) / max(len(judgment.full_text), 1)
            if ratio < 0.5:
                print(f"  SKIP judgment {judgment.id}: cleaning kept only {ratio:.1%}")
                skipped += 1
                continue

            pieces = chunk(cleaned)
            for idx, piece in enumerate(pieces):
                session.add(
                    JudgmentChunk(
                        judgment_id=judgment.id,
                        chunk_idx=idx,
                        text=piece,
                        embedding=None,  # filled on D7
                    )
                )

            judgments_done += 1
            chunks_made += len(pieces)
            session.commit()  # commit per judgment = resumable

        print(
            f"Done. judgments={judgments_done} chunks={chunks_made} skipped={skipped}"
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
    p.add_argument(
        "--rebuild",
        action="store_true",
        help="delete and regenerate chunks for judgments already done",
    )
    a = p.parse_args()
    build(a.source, a.limit, a.rebuild)
