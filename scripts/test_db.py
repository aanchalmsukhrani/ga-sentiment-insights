from sqlalchemy import create_engine

# Update password if needed
DATABASE_URL = "postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/ga_sentiment_dashboard"
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("Connection OK:", list(result))
except Exception as e:
    print("Connection failed:", e)
