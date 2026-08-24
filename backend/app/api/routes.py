"""NyayaMitra API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Judgment, JudgmentChunk
from app.schemas import (
    AskRequest,
    AskResponse,
    BridgeResponse,
    JudgmentDetail,
    SearchRequest,
    SearchResponse,
)
from app.services.bns_bridge import expand, expand_query, lookup
from app.services.search import hybrid_search, rag_answer, search

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search_judgments(req: SearchRequest, db: Session = Depends(get_db)):
    """Semantic search over the judgment corpus.

    With hybrid=true, judgments citing a statute matching the query
    (across both IPC and BNS eras) are ranked first.
    """
    tags = expand_query(db, req.query)
    fn = hybrid_search if req.hybrid else search
    rows = fn(db, req.query, k=req.k)

    results = [
        {
            "chunk_id": r["id"],
            "judgment_id": r["judgment_id"],
            "chunk_idx": r["chunk_idx"],
            "year": r["year"],
            "case_no": r["case_no"],
            "outcome": r["outcome"],
            "sections": r.get("sections") or [],
            "similarity": round(r["similarity"], 4),
            "section_match": bool(r.get("section_match")),
            "snippet": r["snippet"],
        }
        for r in rows
    ]
    return {
        "query": req.query,
        "reformulated_tags": tags,
        "count": len(results),
        "results": results,
    }


@router.get("/judgments/{judgment_id}", response_model=JudgmentDetail)
def get_judgment(judgment_id: int, db: Session = Depends(get_db)):
    j = db.query(Judgment).filter(Judgment.id == judgment_id).first()
    if j is None:
        raise HTTPException(status_code=404, detail="Judgment not found")

    meta = j.jsonb_meta or {}
    chunk_count = (
        db.query(JudgmentChunk).filter(JudgmentChunk.judgment_id == judgment_id).count()
    )
    return {
        "id": j.id,
        "court": j.court,
        "case_no": j.case_no,
        "year": j.year,
        "outcome": meta.get("outcome"),
        "sections": meta.get("sections", []),
        "sections_expanded": meta.get("sections_expanded", []),
        "char_length": len(j.full_text or ""),
        "chunk_count": chunk_count,
    }


@router.get("/bridge/{tag}", response_model=BridgeResponse)
def bridge_lookup(tag: str, db: Session = Depends(get_db)):
    """Expand a section tag across both statutory eras. Example: IPC_420"""
    tag = tag.upper()
    expanded = expand(db, tag)
    row = lookup(db, tag)
    return {
        "input_tag": tag,
        "expanded": expanded,
        "offence": row.offence if row else None,
        "change_type": row.change_type if row else None,
    }


@router.get("/stats")
def corpus_stats(db: Session = Depends(get_db)):
    total = db.query(Judgment).count()
    chunks = db.query(JudgmentChunk).count()
    embedded = (
        db.query(JudgmentChunk).filter(JudgmentChunk.embedding.isnot(None)).count()
    )
    return {
        "judgments": total,
        "chunks": chunks,
        "chunks_embedded": embedded,
    }


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, db: Session = Depends(get_db)):
    """Grounded legal Q&A over the judgment corpus.

    The LLM is invoked only when retrieval clears the similarity floor.
    Otherwise grounded=false and no answer is generated - a hard code
    path, not a prompt instruction.

    Generation runs on CPU: expect 60-120 seconds for a grounded answer,
    under 2 seconds when the gate rejects.
    """
    return rag_answer(db, req.question, k=req.k)
