# scripts/ingest_products_csv.py
import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ===== Config =====
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

CSV_PATH = "data/raw/amazon_products_sales_data_cleaned.csv"  # full file
CHUNK = 10_000  # ~5 chunks for ~42k rows

USE_COLUMNS = [
    "product_title",
    "product_rating",
    "total_reviews",
    "purchased_last_month",
    "discounted_price",
    "original_price",
    "discount_percentage",
    "is_best_seller",
    "is_sponsored",
    "has_coupon",
    "buy_box_availability",
    "delivery_date",
    "sustainability_tags",
    "product_image_url",
    "product_page_url",
    "data_collected_at",
    "product_category",
]


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    # strip currency/% if they exist and convert to numbers
    for col in ["discounted_price", "original_price"]:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(r"[^0-9.\-]", "", regex=True)
                .replace("", pd.NA)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "discount_percentage" in df.columns:
        df["discount_percentage"] = (
            df["discount_percentage"].astype(str)
            .str.replace(r"[^0-9.\-]", "", regex=True)
            .replace("", pd.NA)
        )
        df["discount_percentage"] = pd.to_numeric(df["discount_percentage"], errors="coerce")

    # dates
    for dcol in ["delivery_date", "data_collected_at"]:
        if dcol in df.columns:
            df[dcol] = pd.to_datetime(df[dcol], errors="coerce").dt.date

    # Coerce numerics
    for ncol in ["product_rating", "total_reviews", "purchased_last_month"]:
        if ncol in df.columns:
            df[ncol] = pd.to_numeric(df[ncol], errors="coerce")

    return df



def ensure_staging(engine):
    """Create the staging table if needed, then truncate it (2.x-safe)."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS stg_products (
      product_title TEXT,
      product_rating NUMERIC,
      total_reviews INTEGER,
      purchased_last_month INTEGER,
      discounted_price NUMERIC,
      original_price NUMERIC,
      discount_percentage NUMERIC,
      is_best_seller BOOLEAN,
      is_sponsored BOOLEAN,
      has_coupon BOOLEAN,
      buy_box_availability TEXT,
      delivery_date DATE,
      sustainability_tags TEXT,
      product_image_url TEXT,
      product_page_url TEXT,
      data_collected_at DATE,
      product_category TEXT
    );
    """
    with engine.begin() as conn:
        conn.exec_driver_sql(create_sql)
        conn.execute(text("TRUNCATE TABLE stg_products;"))


def main():
    if not DB_URL:
        raise RuntimeError("DATABASE_URL not set in .env")

    engine = create_engine(DB_URL, future=True)

    # Make sure staging exists & is empty
    ensure_staging(engine)

    # Stream the CSV and append in chunks
    total = 0
    reader = pd.read_csv(
        CSV_PATH,
        usecols=USE_COLUMNS,
        chunksize=CHUNK,
        low_memory=False,
        encoding="utf-8",
    )
    for chunk in reader:
        chunk = normalize(chunk)
        # append chunk
        chunk.to_sql("stg_products", engine, if_exists="append", index=False)
        total += len(chunk)
        print(f"Loaded {total:,} rows into stg_products...")

    print(f"Done. Total rows in staging: {total:,}")


if __name__ == "__main__":
    main()
