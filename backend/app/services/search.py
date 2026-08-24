"""Semantic search over judgment chunks using pgvector cosine distance."""

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.services.embedder import embed_one

# Provisional floor, calibrated on 875 chunks: good matches scored 0.47-0.73,
# a query with no valid answer in the corpus scored 0.32-0.34.
# Recalibrate against known-good / known-absent queries as the corpus grows.
MIN_SIMILARITY = 0.45

SEARCH_SQL = sql_text("""
    SELECT c.id,
           c.judgment_id,
           c.chunk_idx,
           j.year,
           j.case_no,
           j.jsonb_meta->>'outcome' AS outcome,
           j.jsonb_meta->'sections' AS sections,
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


def search(
    db: Session,
    query: str,
    k: int = 5,
    preview: int = 300,
    min_sim: float = MIN_SIMILARITY,
) -> list[dict]:
    """Pure semantic search. Retained as the baseline for hybrid comparison."""
    qvec = embed_one(query)
    rows = (
        db.execute(
            SEARCH_SQL,
            {"qvec": str(qvec), "k": k, "preview": preview},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows if r["similarity"] >= min_sim]


def hybrid_search(
    db: Session,
    query: str,
    k: int = 5,
    preview: int = 300,
    min_sim: float = MIN_SIMILARITY,
) -> list[dict]:
    """Semantic search, with judgments citing a matching statute ranked first.

    A row survives if it clears the similarity floor OR cites a matching
    statute - a judgment explicitly citing IPC 420 is relevant to a BNS 318
    query even when its prose embeds poorly.
    """
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


def rag_answer(
    db: Session,
    question: str,
    k: int = 5,
    min_sim: float = MIN_SIMILARITY,
) -> dict:
    """Retrieve, then generate - but only if retrieval found something.

    Vector search always returns k rows. Without this gate the LLM would
    generate a fluent answer over irrelevant excerpts, which in a legal
    tool is worse than no answer. This is a hard code path, not a prompt
    instruction, because an LLM only sometimes obeys "say you don't know".

    k and preview are capped: prompt processing dominates CPU latency,
    so fewer, tighter excerpts cut generation time substantially.
    """
    from app.services.llm import answer as llm_answer

    hits = hybrid_search(db, question, k=min(k, 3), preview=500, min_sim=min_sim)

    if not hits:
        return {
            "question": question,
            "answer": None,
            "grounded": False,
            "reason": "No sufficiently relevant judgments found in the corpus.",
            "sources": [],
        }

    return {
        "question": question,
        "answer": llm_answer(question, hits),
        "grounded": True,
        "reason": None,
        "sources": [
            {
                "judgment_id": h["judgment_id"],
                "year": h["year"],
                "case_no": h["case_no"],
                "similarity": round(h["similarity"], 4),
            }
            for h in hits
        ],
    }
