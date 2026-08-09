"""Run real queries against the embedded corpus."""

from app.db.session import SessionLocal
from app.services.search import search

QUERIES = [
    "criminal conspiracy to commit theft of government property",
    "minority educational institution right to administer",
    "cheating and dishonestly inducing delivery of property",
    "post mortem report cause of death injuries",
    "bail application rejected flight risk",
]

db = SessionLocal()
for q in QUERIES:
    print(f"\n{'=' * 100}\nQUERY: {q}\n{'=' * 100}")
    for r in search(db, q, k=3):
        print(
            f"\n  sim={r['similarity']:.4f}  judgment={r['judgment_id']} "
            f"chunk={r['chunk_idx']}  year={r['year']}  outcome={r['outcome']}"
        )
        print(f"  {r['snippet'][:250]}...")
db.close()
