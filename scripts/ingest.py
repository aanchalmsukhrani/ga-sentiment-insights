#!/usr/bin/env python3
"""Skeleton ingestion script.
- Later: load CSV/JSON or call API to fetch reviews.
- Write into Postgres using SQLAlchemy (DATABASE_URL).
"""
from pathlib import Path
from sqlalchemy import create_engine, text
from src.config.settings import DATABASE_URL
import pandas as pd

def main():
    print("Ingestion placeholder. Add dataset path or API call here.")
    engine = create_engine(DATABASE_URL)
    # Example: ensure connection works
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("DB connection OK.")

if __name__ == "__main__":
    main()
