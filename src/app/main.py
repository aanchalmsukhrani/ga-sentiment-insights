from fastapi import FastAPI

app = FastAPI(title="AI Sentiment & Insights API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-sentiment-insights", "version": "0.1.0"}
