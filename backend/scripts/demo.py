"""NyayaMitra demo: BNS-IPC cross-era retrieval."""

from app.db.session import SessionLocal
from app.services.search import search, hybrid_search
from app.services.bns_bridge import expand_query

QUERY = "BNS 318 cheating by a public servant"

db = SessionLocal()

print("\n" + "=" * 78)
print(f"  QUERY:  {QUERY}")
print("  Corpus: Supreme Court judgments, all pre-2024 (IPC era only)")
print("=" * 78)

tags = expand_query(db, QUERY)
print(f"\n  BNS-IPC BRIDGE expanded the query to {len(tags)} statutory tags:")
print(f"  {tags}\n")

print("-" * 78)
print("  WITHOUT the bridge (semantic search only):")
print("-" * 78)
for r in search(db, QUERY, k=3):
    print(f"   {r['similarity']:.3f}  judgment {r['judgment_id']}")
    print(f"          {r['snippet'][:95]}...")

print("\n" + "-" * 78)
print("  WITH the bridge (hybrid: semantic + statutory):")
print("-" * 78)
for r in hybrid_search(db, QUERY, k=3):
    flag = "[SECTION MATCH]" if r["section_match"] else "               "
    print(f"   {r['similarity']:.3f} {flag} judgment {r['judgment_id']}")
    print(f"          {r['snippet'][:95]}...")

print("\n" + "=" * 78)
print("  A 2024-era statute retrieved 2020-era IPC precedent.")
print("=" * 78 + "\n")

db.close()
