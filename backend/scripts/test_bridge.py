from app.db.session import SessionLocal
from app.services.bns_bridge import expand, expand_query

db = SessionLocal()

print("--- direct expansion ---")
for tag in ["IPC_420", "BNS_318_4", "IPC_302", "IPC_124A", "IPC_999"]:
    print(f"{tag:12} -> {expand(db, tag)}")

print("\n--- free text expansion ---")
queries = [
    "cheating case under IPC 420",
    "accused charged under BNS 318(4) and Section 406 IPC",
    "my client lost money in an online scam",
]
for q in queries:
    print(f"{q!r}\n   -> {expand_query(db, q)}")

db.close()
