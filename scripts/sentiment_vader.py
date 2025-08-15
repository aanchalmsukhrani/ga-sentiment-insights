#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from tqdm import tqdm

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

def main():
    analyzer = SentimentIntensityAnalyzer()
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT review_id, review_text
            FROM reviews r
            WHERE NOT EXISTS (SELECT 1 FROM sentiment_results s WHERE s.review_id = r.review_id)
        """)).fetchall()

        for review_id, review_text in tqdm(rows, desc="Scoring"):
            if not review_text:
                continue
            score = analyzer.polarity_scores(review_text)["compound"]
            label = "positive" if score >= 0.05 else "negative" if score <= -0.05 else "neutral"
            conn.execute(text("""
                INSERT INTO sentiment_results (review_id, model, polarity, label, confidence, keywords_json)
                VALUES (:review_id, 'vader', :polarity, :label, NULL, '{}'::jsonb)
            """), {"review_id": review_id, "polarity": score, "label": label})
    print("✅ Sentiment scored.")

if __name__ == "__main__":
    main()
