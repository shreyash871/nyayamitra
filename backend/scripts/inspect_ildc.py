"""Download ILDC (via IL-TUR) and print what's actually inside it."""

from datasets import load_dataset

print("Downloading... first run takes a while, later runs use the cache.\n")

ds = load_dataset("Exploration-Lab/IL-TUR", "cjpe")

print("=== SPLITS AVAILABLE ===")
for name, split in ds.items():
    print(f"  {name:20} {len(split):>7} rows")

first_split = list(ds.keys())[0]
sample = ds[first_split]

print(f"\n=== COLUMNS in '{first_split}' ===")
for col, feat in sample.features.items():
    print(f"  {col:20} {feat}")

print("\n=== FIRST RECORD (truncated) ===")
row = sample[0]
for col, val in row.items():
    text = str(val)
    preview = text[:300].replace("\n", " ") + ("..." if len(text) > 300 else "")
    print(f"\n[{col}]  len={len(text)}")
    print(f"  {preview}")
