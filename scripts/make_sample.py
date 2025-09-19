import os, glob
import pandas as pd

root = "data/raw"
# find first CSV in data/raw (edit the name if you know it)
candidates = [p for p in glob.glob(os.path.join(root, "Reviews.csv"), recursive=True)]
if not candidates:
    raise SystemExit("❌ No CSV found in data/raw. Please unzip first.")

src = candidates[0]
print(f"Using source CSV: {src}")

df = pd.read_csv(src, nrows=10000)  # read first 10k rows to avoid memory spikes
sample = df.head(1000)
out = "data/raw/sample_reviews.csv"
sample.to_csv(out, index=False)
print(f"✅ Saved sample: {out} (rows={len(sample)})")
