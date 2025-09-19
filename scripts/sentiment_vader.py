# scripts/sentiment_vader.py
import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer




load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
ENGINE = create_engine(DB_URL)

# --- Sentiment scoring logic ---
def run_vader(df: pd.DataFrame) -> pd.DataFrame:
    sid = SentimentIntensityAnalyzer()
    results = []

    for _, row in df.iterrows():
        text = row["review_text"] or ""
        scores = sid.polarity_scores(text)

        # classify
        if scores["compound"] >= 0.05:
            label = "positive"
        elif scores["compound"] <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        results.append(
            {
                "review_id": row["review_id"],
                "model": "vader",
                "polarity": scores["compound"],
                "label": label,
                "confidence": abs(scores["compound"]),  # crude proxy
                "keywords_json": None,  # keep null for now
                "processed_at": datetime.utcnow(),
            }
        )

    return pd.DataFrame(results)


def main(limit: int = 0):
    # 1. fetch unscored reviews
    sql = """
    SELECT r.review_id, r.product_id, r.review_text
    FROM reviews r
    LEFT JOIN sentiment_results s ON s.review_id = r.review_id
    WHERE s.review_id IS NULL
    """
    if limit and int(limit) > 0:
        sql += " LIMIT :limit"

    with ENGINE.begin() as conn:
        df_reviews = pd.read_sql(text(sql), conn, params={"limit": int(limit)} if limit else {})

    if df_reviews.empty:
        print("No unscored reviews found.")
        return

    # 2. run VADER
    scored = run_vader(df_reviews)

    # 3. write back to DB
    with ENGINE.begin() as conn:
        scored.to_sql(
            "sentiment_results",
            con=conn,
            schema="public",
            if_exists="append",
            index=False,
            method="multi",
            chunksize=5000,
        )

    print(f"Wrote {len(scored)} rows to sentiment_results.")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", default=0, help="limit number of reviews to score")
    args = ap.parse_args()
    main(limit=args.limit)
