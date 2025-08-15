#!/usr/bin/env python3
#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from tqdm import tqdm

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, future=True)

def label_from_score(score: float) -> str:
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"

def main():
    analyzer = SentimentIntensityAnalyzer()

    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT r.review_id, r.review_text
            FROM reviews r
            LEFT JOIN sentiment_results s ON s.review_id = r.review_id
            WHERE s.review_id IS NULL
            ORDER BY r.review_id
        """)).fetchall()

        for review_id, review_text in tqdm(rows, desc="Scoring reviews"):
            if not review_text:
                continue
            comp = analyzer.polarity_scores(review_text)["compound"]
            lab = label_from_score(comp)
            conn.execute(text("""
                INSERT INTO sentiment_results (review_id, model, polarity, label, confidence, keywords_json)
                VALUES (:rid, 'vader', :polarity, :label, NULL, '{}'::jsonb)
            """), {"rid": review_id, "polarity": comp, "label": lab})

    print("✅ Sentiment scoring complete.")

if __name__ == "__main__":
    main()

