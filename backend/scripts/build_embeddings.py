"""Generate embeddings for chunks that don't have one yet.

python -m scripts.build_embeddings --limit 100
python -m scripts.build_embeddings
"""

import argparse
import time

from app.db.session import SessionLocal
from app.models import JudgmentChunk
from app.services.embedder import embed_many

BATCH = 32


def run(limit: int | None, batch: int) -> None:
    session = SessionLocal()
    done = 0
    started = time.time()

    try:
        while True:
            rows = (
                session.query(JudgmentChunk)
                .filter(JudgmentChunk.embedding.is_(None))
                .order_by(JudgmentChunk.id)
                .limit(batch)
                .all()
            )
            if not rows:
                break

            vectors = embed_many([r.text for r in rows])
            for row, vec in zip(rows, vectors):
                row.embedding = vec
            session.commit()

            done += len(rows)
            rate = done / max(time.time() - started, 0.001)
            print(f"  {done} embedded  ({rate:.1f}/sec)", end="\r")

            if limit and done >= limit:
                break

        remaining = (
            session.query(JudgmentChunk)
            .filter(JudgmentChunk.embedding.is_(None))
            .count()
        )
        embedded_total = (
            session.query(JudgmentChunk)
            .filter(JudgmentChunk.embedding.isnot(None))
            .count()
        )
        elapsed = time.time() - started
        print(
            f"\nDone. this run={done} in {elapsed:.0f}s  "
            f"total embedded={embedded_total}  remaining={remaining}"
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--batch", type=int, default=BATCH)
    a = p.parse_args()
    run(a.limit, a.batch)
