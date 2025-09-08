# app_streamlit.py
import os
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ===== Config =====
API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="AI Sentiment & Insights",
    page_icon="🧠",
    layout="wide",
)

# ===== Helpers =====
@st.cache_data(ttl=30)
def get_json(path: str, params: dict | None = None):
    url = f"{API_BASE}{path}"
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def to_df(data):
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

# ===== Sidebar =====
st.sidebar.title("Settings")
st.sidebar.markdown(f"**API:** `{API_BASE}`")

# ===== Load products & metrics =====
try:
    products = to_df(get_json("/products"))
    metrics  = to_df(get_json("/metrics"))
except Exception as e:
    st.error(f"Failed to reach API at {API_BASE}. Is FastAPI running?\n\n{e}")
    st.stop()

# ===== Header =====
st.title("🧠 Generative AI — Sentiment & Insights Dashboard")
st.caption("Day 5: Minimal dashboard pulling from your FastAPI API.")

# ===== Metrics table =====
st.subheader("📊 Product Metrics")
if metrics.empty:
    st.info("No metrics yet. Add reviews and run your sentiment script.")
else:
    # Nice columns
    show_cols = [
        "product_id", "title", "total_reviews", "avg_rating",
        "avg_sentiment_score", "positive_count", "neutral_count", "negative_count"
    ]
    existing_cols = [c for c in show_cols if c in metrics.columns]
    st.dataframe(metrics[existing_cols], use_container_width=True)

# ===== Product picker =====
if products.empty:
    st.warning("No products found.")
    st.stop()

product_map = dict(zip(products["title"], products["product_id"]))
choice = st.selectbox("🔎 Choose a product", list(product_map.keys()))
pid = product_map[choice]

# ===== Load reviews for selected product =====
reviews = to_df(get_json(f"/products/{pid}/reviews", params={"limit": 1000}))

# ===== Charts row =====
col1, col2 = st.columns(2)

with col1:
    st.subheader("🙂 Sentiment distribution")
    if "label" in reviews.columns and not reviews.empty:
        counts = reviews["label"].value_counts().reset_index()
        counts.columns = ["label", "count"]
        fig = px.bar(counts, x="label", y="count", text="count", title="Sentiment counts")
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sentiment labels yet. Run the VADER script to generate sentiment_results.")

with col2:
    st.subheader("⭐ Ratings over time")
    if {"review_date", "rating"}.issubset(reviews.columns) and not reviews.empty:
        # ensure proper dtype
        reviews["review_date"] = pd.to_datetime(reviews["review_date"], errors="coerce")
        rtime = reviews.dropna(subset=["review_date"]).sort_values("review_date")
        if not rtime.empty:
            fig = px.line(rtime, x="review_date", y="rating", markers=True, title="Ratings timeline")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No valid review_date values to plot.")
    else:
        st.info("Ratings/time columns missing to plot.")

# ===== Reviews table =====
st.subheader("🧾 Latest Reviews")
if not reviews.empty:
    keep = [c for c in ["review_id","review_date","rating","label","review_text","polarity"] if c in reviews.columns]
    st.dataframe(reviews[keep].sort_values(["review_date","review_id"], na_position="last"), use_container_width=True)
else:
    st.info("No reviews for this product yet.")

# ===== Footer =====
st.caption("Backend endpoints: /products, /metrics, /metrics/{id}, /products/{id}/reviews")
