"""Test the RAG gate: a real question and an unanswerable one."""

import time

from app.db.session import SessionLocal
from app.services.search import rag_answer

QUESTIONS = [
    "What did the courts hold about cheating a university by impersonation at an examination?",
    "What is the procedure for filing a patent application for a software invention in Japan?",
]

db = SessionLocal()
for q in QUESTIONS:
    print(f"\n{'=' * 90}\nQ: {q}\n{'=' * 90}")
    t0 = time.time()
    res = rag_answer(db, q, k=4)
    print(f"grounded={res['grounded']}  ({time.time() - t0:.0f}s)")
    if res["grounded"]:
        print(f"\n{res['answer']}\n")
        print("sources:", [(s["judgment_id"], s["year"]) for s in res["sources"]])
    else:
        print(f"\n{res['reason']}")
db.close()
