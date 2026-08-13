"""Compare pure vector search against hybrid (vector + section boost)."""

from app.db.session import SessionLocal
from app.services.search import search, hybrid_search
from app.services.bns_bridge import expand_query

QUERIES = [
    "BNS 318 cheating by a public servant",
    "IPC 420 cheating government",
    "criminal conspiracy to commit theft of government property",
    "murder with common intention",
]

db = SessionLocal()

for q in QUERIES:
    print(f"\n{'=' * 90}\nQUERY: {q}")
    print(f"bridge tags: {expand_query(db, q)}\n{'=' * 90}")

    print("\n--- PURE VECTOR ---")
    for r in search(db, q, k=3):
        print(f"  {r['similarity']:.3f}  j={r['judgment_id']:>3}  {r['snippet'][:110]}")

    print("\n--- HYBRID ---")
    for r in hybrid_search(db, q, k=3):
        flag = "SEC" if r["section_match"] else "   "
        print(
            f"  {r['similarity']:.3f} {flag} j={r['judgment_id']:>3}  {r['snippet'][:110]}"
        )

db.close()
