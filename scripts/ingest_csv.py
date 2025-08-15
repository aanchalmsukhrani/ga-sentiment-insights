#!/usr/bin/env python3
"""
Ingest reviews CSV → Postgres (ga_sentiment).
- Upserts products (by title+brand)
- Inserts reviews referencing product_id
"""
import os
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://ga_user:ga_password@localhost:5432/ga_sentiment")
engine = create_engine(DATABASE_URL, future=True)

CSV_PATH = os.getenv("CSV_PATH", "data/raw/reviews_sample.csv")

# Minimal cleaning helpers
def clean_str(s):
    if pd.isna(s):
        return None
    s = str(s).strip()
    return " ".join(s.split())  # collapse whitespace

def to_date(s):
    if pd.isna(s) or not str(s).strip():
        return None
    return pd.to_datetime(s, errors="coerce").date()

def main():
    df = pd.read_csv(CSV_PATH)
    # basic normalization
    df["product_title"] = df["product_title"].map(clean_str)
    df["category"] = df["category"].map(clean_str)
    df["brand"] = df["brand"].map(clean_str)
    df["user_hash"] = df["user_hash"].map(clean_str)
    df["review_text"] = df["review_text"].map(clean_str)
    df["source"] = df.get("source", "sample")
    df["lang"] = df.get("lang", "en")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").clip(1, 5)
    df["review_date"] = df["review_date"].map(to_date)

    # 1) Upsert products, keep a lookup: (title,brand) -> product_id
    product_ids = {}
    with engine.begin() as conn:
        for (title, brand, category) in tqdm(
            df[["product_title", "brand", "category"]].drop_duplicates().itertuples(index=False, name=None),
            desc="Upserting products"
        ):
            res = conn.execute(
                text("""
                    INSERT INTO products (title, category, brand, metadata_json)
                    VALUES (:title, :category, :brand, '{}'::jsonb)
                    ON CONFLICT DO NOTHING
                    RETURNING product_id;
                """),
                {"title": title, "category": category, "brand": brand}
            )
            row = res.first()
            if row is None:
                # fetch existing id
                row = conn.execute(
                    text("SELECT product_id FROM products WHERE title=:title AND COALESCE(brand,'')=COALESCE(:brand,'')"),
                    {"title": title, "brand": brand}
                ).first()
            product_ids[(title, brand)] = row[0]

        # 2) Insert reviews with product_id
        for r in tqdm(df.to_dict(orient="records"), desc="Inserting reviews"):
            pid = product_ids[(r["product_title"], r["brand"])]
            conn.execute(
                text("""
                    INSERT INTO reviews (product_id, user_hash, review_text, rating, review_date, source, lang)
                    VALUES (:product_id, :user_hash, :review_text, :rating, :review_date, :source, :lang)
                """),
                {
                    "product_id": pid,
                    "user_hash": r.get("user_hash"),
                    "review_text": r.get("review_text"),
                    "rating": int(r.get("rating") or 0),
                    "review_date": r.get("review_date"),
                    "source": r.get("source") or "sample",
                    "lang": r.get("lang") or "en",
                }
            )

    print("✅ Ingestion complete.")
    with engine.connect() as conn:
        total_p = conn.execute(text("SELECT COUNT(*) FROM products")).scalar_one()
        total_r = conn.execute(text("SELECT COUNT(*) FROM reviews")).scalar_one()
        print(f"Products: {total_p}, Reviews: {total_r}")

if __name__ == "__main__":
    main()
