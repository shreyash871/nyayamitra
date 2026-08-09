"""Semantic search over judgment chunks using pgvector cosine distance."""

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.services.embedder import embed_one

SEARCH_SQL = sql_text("""
    SELECT c.id,
           c.judgment_id,
           c.chunk_idx,
           j.year,
           j.case_no,
           j.jsonb_meta->>'outcome' AS outcome,
           1 - (c.embedding <=> CAST(:qvec AS vector)) AS similarity,
           LEFT(c.text, :preview) AS snippet
    FROM judgment_chunks c
    JOIN judgments j ON j.id = c.judgment_id
    WHERE c.embedding IS NOT NULL
    ORDER BY c.embedding <=> CAST(:qvec AS vector)
    LIMIT :k
""")


def search(db: Session, query: str, k: int = 5, preview: int = 300) -> list[dict]:
    qvec = embed_one(query)
    rows = (
        db.execute(
            SEARCH_SQL,
            {"qvec": str(qvec), "k": k, "preview": preview},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]
