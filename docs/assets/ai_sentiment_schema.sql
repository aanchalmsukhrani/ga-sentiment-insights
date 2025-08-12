
-- Core schema for Generative AI-Powered Sentiment & Insights Dashboard
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT,
    brand TEXT,
    metadata_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    user_hash TEXT,               -- hashed user identifier (privacy-friendly)
    review_text TEXT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    review_date DATE,
    source TEXT,                  -- e.g., 'amazon', 'play_store'
    lang TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sentiment_results (
    sentiment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    model TEXT NOT NULL,          -- e.g., 'vader', 'distilbert-base-uncased-finetuned-sst-2-english'
    polarity NUMERIC,             -- continuous score (e.g., VADER compound)
    label TEXT,                   -- 'negative' | 'neutral' | 'positive'
    confidence NUMERIC,
    keywords_json JSONB,          -- extracted key phrases
    processed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ai_summaries (
    summary_id BIGSERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    time_window TEXT NOT NULL,    -- e.g., '2025-07', '2025-W31'
    context_stats_json JSONB,     -- aggregates used for prompting
    summary_text TEXT NOT NULL,
    model TEXT NOT NULL,          -- e.g., 'gpt-4.1-mini', 'anthropic-claude'
    prompt_hash TEXT,             -- hash to dedupe prompts
    generated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, time_window, model)
);

-- Helpful indexes
CREATE INDEX idx_reviews_product_date ON reviews(product_id, review_date);
CREATE INDEX idx_sentiment_review ON sentiment_results(review_id);
CREATE INDEX idx_ai_summaries_product_window ON ai_summaries(product_id, time_window);
