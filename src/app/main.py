from fastapi import FastAPI
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load .env into environment variables
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

