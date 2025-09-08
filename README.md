**Day 1:** Progress: repo scaffold, API health check running locally.

**Day 2:**
- Loaded sample product and review data into the PostgreSQL database.
- Verified data by running queries in pgAdmin to check product reviews, ratings, and dates.
- Created SQL joins between `reviews` and `products` tables to display product titles with their corresponding reviews.
- Built and tested a `v_product_metrics` view to quickly fetch product review counts and average ratings.
- Confirmed that queries return correct results and are ordered as expected.

**Day 3:** Added CSV ingestion (Pandas→Postgres), sample data, and baseline VADER sentiment script. 
- Created `product_metrics` SQL view joining products, reviews, and sentiment results.  
- Added test script to fetch metrics from the view.  

**Day 4:** Added VADER baseline sentiment scoring, created `product_metrics` SQL view, and exposed read-only API endpoints:
- `/products`, `/metrics`, `/metrics/{product_id}`, `/products/{product_id}/reviews`
### API (read-only)
- `GET /products` → list products
- `GET /metrics` → per-product: total_reviews, avg_rating, avg_sentiment_score, positive/neutral/negative counts
- `GET /metrics/{product_id}` → metrics for a single product
- `GET /products/{product_id}/reviews?limit=100` → reviews + sentiment for that product

**Day 5:** Minimal Streamlit dashboard consuming FastAPI:
- `/products`, `/metrics`, `/metrics/{product_id}`, `/products/{product_id}/reviews`
- Charts: sentiment distribution (bar), ratings over time (line)
- Run: `streamlit run app_streamlit.py`

**Quick test**
```bash
curl -s http://127.0.0.1:8000/metrics | jq


## 4) Close/organize GitHub items (2 mins)
- Close “Implement product metrics view for analytics” (if still open anywhere).
- Add a new issue: **“Build minimal dashboard (Day 5)”** with subtasks:
  - Streamlit or simple React page
  - Call `/metrics` and `/products/{id}/reviews`
  - Basic charts (bar for sentiment counts, line for ratings over time)

## 5) Commit the polish
If you added CORS + README updates:
```bash
git add src/app/main.py README.md
git commit -m "chore: enable CORS for dev and document API usage"
git push


![Python](https://img.shields.io/badge/Python-3.10+-informational)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![Status](https://img.shields.io/badge/Project-Active-brightgreen)


# Generative AI–Powered Sentiment & Insights Dashboard

End‑to‑end project: ingest review data → clean & analyze → run sentiment (VADER/BERT) → generate LLM summaries → visualize insights via dashboard and/or BI tool.

## Why it matters
- 2025‑ready: AI‑assisted analytics + cloud-native pipeline
- Highlights SQL, Python, NLP, visualization, and storytelling
- Portfolio- and interview‑friendly

## High‑level architecture
See **docs/assets/architecture.png** and **docs/assets/erd.png**.

## Quickstart (local)
```bash
# 1) Create venv
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install deps
pip install --upgrade pip
pip install -r requirements.txt

# 3) Run API (health check)
uvicorn src.app.main:app --reload

# Run locally (quick alias)
source .venv/bin/activate
uvicorn src.app.main:app --reload
```

API will run at http://127.0.0.1:8000  → Visit `/health`

## Environment variables
Copy `.env.example` to `.env` and fill values when ready.
- `DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:PORT/DBNAME`
- `OPENAI_API_KEY=...` (or other provider)

## Repo layout
```
src/
  app/            # FastAPI app, endpoints
  config/         # settings, env handling
  nlp/            # sentiment + LLM prompt code
scripts/          # ETL/cron jobs
data/             # raw/processed local data (gitignored)
docs/assets/      # diagrams, images, screenshots
notebooks/        # EDA, experiments
tests/            # unit tests
```

## Next steps (backlog)
- [ ] Implement DB init & Alembic migrations
- [ ] Ingestion script for selected dataset
- [ ] Preprocess + sentiment (VADER baseline)
- [ ] LLM summaries per product/time window
- [ ] Dashboard (Streamlit or BI connector)
- [ ] Cloud deploy (AWS RDS, Lambda/EC2, S3)
