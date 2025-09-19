# scripts/ingest_reviews.py
import argparse
import os
import random
import secrets
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# ----- config -----
DAYS_BACK = 120  # how far back to spread review_date timestamps
BATCH_SIZE = 5_000  # write in chunks to avoid giant INSERTs

SENTENCES = [
    "Works well so far!",
    "Solid value for the price.",
    "Battery life could be better.",
    "Exactly as described.",
    "Packaging was damaged but product was fine.",
    "Exceeded my expectations.",
    "Not worth the hype.",
    "Setup was easy and quick.",
    "Customer support was helpful.",
    "I returned it after a week.",
]


def rand_user() -> str:
    # short pseudo-anon user id
    return f"u_{secrets.token_hex(3)}"


def rand_date(within_days: int = DAYS_BACK) -> datetime.date:
    # timezone-aware 'now', then drop tz for a DATE
    today = datetime.now(timezone.utc).date()
    return today - timedelta(days=random.randint(0, within_days))


def ensure_schema(conn) -> None:
    """Make sure reviews has rating/review_date columns."""
    conn.execute(
        text(
            """
            ALTER TABLE reviews
              ADD COLUMN IF NOT EXISTS rating integer,
              ADD COLUMN IF NOT EXISTS review_date date;
            """
        )
    )


def reset_data(conn, reset: bool) -> None:
    """Clear existing data using DELETE (no TRUNCATE privileges needed) and reset sequences."""
    if not reset:
        return

    print("Clearing previous reviews (and dependent sentiment rows) ...")
    # sentiment_results depends on reviews; delete children first
    conn.execute(text("DELETE FROM sentiment_results;"))
    conn.execute(text("DELETE FROM reviews;"))

    # Reset sequences (works if sequence names follow the usual pattern).
    # We try to discover names dynamically; fall back to common defaults.
    def reset_seq(table: str, pk: str, fallback: str | None = None):
        seq_row = conn.execute(
            text("SELECT pg_get_serial_sequence(:t, :c);"),
            {"t": f"public.{table}", "c": pk},
        ).scalar()
        seq_name = seq_row or fallback
        if seq_name:
            conn.execute(text(f'ALTER SEQUENCE {seq_name} RESTART WITH 1;'))

    reset_seq("reviews", "review_id", "reviews_review_id_seq")
    reset_seq("sentiment_results", "sentiment_id", "sentiment_results_sentiment_id_seq")


def pick_products(conn, limit: int) -> list[int]:
    rows = conn.execute(
        text(
            """
            SELECT product_id
            FROM products
            WHERE title IS NOT NULL
            ORDER BY product_id
            LIMIT :n
            """
        ),
        {"n": limit},
    ).fetchall()
    return [r[0] for r in rows]


def build_rows(product_ids: list[int], min_reviews: int, max_reviews: int) -> pd.DataFrame:
    out = {
        "product_id": [],
        "user_hash": [],
        "review_text": [],
        "rating": [],
        "review_date": [],
    }
    for pid in product_ids:
        n = random.randint(min_reviews, max_reviews)
        for _ in range(n):
            out["product_id"].append(pid)
            out["user_hash"].append(rand_user())
            out["review_text"].append(random.choice(SENTENCES))
            # skew a little positive but allow full 1–5 range
            out["rating"].append(int(np.clip(np.round(np.random.normal(4.0, 1.0)), 1, 5)))
            out["review_date"].append(rand_date())
    return pd.DataFrame(out)


def write_in_batches(df: pd.DataFrame, engine) -> int:
    if df.empty:
        return 0
    total = 0
    # Use engine directly (not raw DBAPI connection) so pandas uses SQLAlchemy dialect (no sqlite_master check)
    for start in range(0, len(df), BATCH_SIZE):
        chunk = df.iloc[start : start + BATCH_SIZE]
        chunk.to_sql("reviews", engine, if_exists="append", index=False)
        total += len(chunk)
    return total


def main():
    parser = argparse.ArgumentParser(description="Seed synthetic reviews")
    parser.add_argument("--products", type=int, default=200, help="How many products to seed")
    parser.add_argument("--min", dest="min_reviews", type=int, default=5, help="Min reviews per product")
    parser.add_argument("--max", dest="max_reviews", type=int, default=12, help="Max reviews per product")
    parser.add_argument("--reset", action="store_true", help="Delete existing reviews first")
    args = parser.parse_args()

    if args.min_reviews > args.max_reviews:
        args.min_reviews, args.max_reviews = args.max_reviews, args.min_reviews

    engine = create_engine(DB_URL, pool_pre_ping=True)

    with engine.begin() as conn:
        ensure_schema(conn)
        reset_data(conn, args.reset)
        pids = pick_products(conn, args.products)
        if not pids:
            raise SystemExit("No products found. Did you load products first?")

    print(f"Seeding synthetic reviews for {len(pids)} products "
          f"({args.min_reviews}–{args.max_reviews} per product) ...")

    df = build_rows(pids, args.min_reviews, args.max_reviews)
    inserted = write_in_batches(df, engine)

    print(f"Done. Inserted {inserted} reviews.")
    print("Tip: now run the sentiment job:")
    print("  python scripts/sentiment_vader.py --limit 0   # 0 = process all")


if __name__ == "__main__":
    main()
