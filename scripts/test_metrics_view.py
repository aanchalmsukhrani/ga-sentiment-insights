from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, future=True)

with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM product_metrics LIMIT 5"))
    for row in result:
        print(row)
