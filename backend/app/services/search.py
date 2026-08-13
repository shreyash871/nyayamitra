"""Semantic search over judgment chunks using pgvector cosine distance."""

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.services.embedder import embed_one

MIN_SIMILARITY = 0.45

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

HYBRID_SQL = sql_text("""
    SELECT c.id, c.judgment_id, c.chunk_idx,
           j.year, j.case_no,
           j.jsonb_meta->>'outcome' AS outcome,
           j.jsonb_meta->'sections' AS sections,
           1 - (c.embedding <=> CAST(:qvec AS vector)) AS similarity,
           (j.jsonb_meta->'sections_expanded' ?| CAST(:tags AS text[])) AS section_match,
           LEFT(c.text, :preview) AS snippet
    FROM judgment_chunks c
    JOIN judgments j ON j.id = c.judgment_id
    WHERE c.embedding IS NOT NULL
    ORDER BY (j.jsonb_meta->'sections_expanded' ?| CAST(:tags AS text[])) DESC,
             c.embedding <=> CAST(:qvec AS vector)
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


def hybrid_search(
    db: Session,
    query: str,
    k: int = 5,
    preview: int = 300,
    min_sim: float = MIN_SIMILARITY,
) -> list[dict]:
    """Semantic search, with judgments citing a matching statute ranked first."""
    from app.services.bns_bridge import expand_query

    tags = expand_query(db, query) or ["__none__"]
    qvec = embed_one(query)
    rows = (
        db.execute(
            HYBRID_SQL,
            {"qvec": str(qvec), "tags": tags, "k": k, "preview": preview},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows if r["similarity"] >= min_sim or r["section_match"]]
