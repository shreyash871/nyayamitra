from app.clients.indian_kanoon import IndianKanoonClient
from app.clients.mock_kanoon import MockKanoonClient
from app.core.config import settings
from app.db.session import SessionLocal
from app.ingestion.celery_app import celery_app
from app.models.models import Judgment


def _get_client():
    """Pick the real or mock client based on INGESTION_MODE."""
    if settings.INGESTION_MODE == "live":
        return IndianKanoonClient()
    return MockKanoonClient()


@celery_app.task(name="ingest_judgments")
def ingest_judgments(query: str, max_docs: int = 5) -> dict:
    """Search for judgments, fetch each one, and save to Postgres.
    Runs in the background via Celery."""
    client = _get_client()
    session = SessionLocal()
    saved = 0

    try:
        results = client.search(query, page=0)
        docs = results.get("docs", [])[:max_docs]

        for doc in docs:
            doc_id = str(doc["tid"])

            # Skip if we already have this judgment
            existing = (
                session.query(Judgment).filter(Judgment.case_no == doc_id).first()
            )
            if existing:
                continue

            full = client.get_document(doc_id)

            judgment = Judgment(
                court=full.get("docsource", "Unknown"),
                case_no=doc_id,
                title=full.get("title", ""),
                full_text=full.get("doc", ""),
            )
            session.add(judgment)
            saved += 1

        session.commit()
    finally:
        session.close()

    return {"query": query, "saved": saved}
