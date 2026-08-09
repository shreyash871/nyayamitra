"""Sanity-check InLegal-SBERT before wiring it into the pipeline."""

from sentence_transformers import SentenceTransformer, util

MODEL = "bhavyagiri/InLegal-Sbert"

print(f"Loading {MODEL} (first run downloads ~440 MB)...")
model = SentenceTransformer(MODEL)

vec = model.encode("The accused was convicted under Section 420 IPC.")
print(f"\nvector dimensions: {len(vec)}")
print(f"max sequence length: {model.max_seq_length} tokens")

pairs = [
    ("online banking fraud", "UPI payment scam"),
    ("online banking fraud", "murder by dangerous weapon"),
    ("criminal conspiracy to commit theft", "accused conspired to steal property"),
    ("criminal conspiracy to commit theft", "dispute over land boundary"),
]

print("\ncosine similarity:")
for a, b in pairs:
    sim = util.cos_sim(model.encode(a), model.encode(b)).item()
    print(f"  {sim:.3f}   {a!r} <-> {b!r}")
