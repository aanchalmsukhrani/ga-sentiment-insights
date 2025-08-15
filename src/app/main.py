from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="AI Sentiment & Insights API", version="0.1.0")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, future=True)

@app.get("/health")
def health():
    out = {"status": "ok", "service": "ai-sentiment-insights", "version": "0.1.0"}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        out["db"] = "up"
    except Exception as e:
        out["db"] = f"down: {e.__class__.__name__}"
    return out

# ---- Day 4 endpoints ----

class Product(BaseModel):
    product_id: int
    title: str

@app.get("/products", response_model=list[Product])
def list_products():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT product_id, title
            FROM products
            ORDER BY product_id
            LIMIT 200
        """)).mappings().all()
    return rows

@app.get("/metrics")
def all_product_metrics():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT *
            FROM product_metrics
            ORDER BY product_id
            LIMIT 200
        """)).mappings().all()
    return rows

@app.get("/metrics/{product_id}")
def metrics_for_product(product_id: int):
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT *
            FROM product_metrics
            WHERE product_id = :pid
        """), {"pid": product_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="product not found")
    return row

@app.get("/products/{product_id}/reviews")
def reviews_for_product(product_id: int, limit: int = 100):
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT r.review_id, r.rating, r.review_date, r.review_text,
                   COALESCE(s.label, 'unscored') AS label,
                   s.polarity
            FROM reviews r
            LEFT JOIN sentiment_results s ON s.review_id = r.review_id
            WHERE r.product_id = :pid
            ORDER BY r.review_date NULLS LAST, r.review_id
            LIMIT :lim
        """), {"pid": product_id, "lim": limit}).mappings().all()
    return rows
