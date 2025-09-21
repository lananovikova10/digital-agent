-- Create tables for weekly intelligence agent

CREATE EXTENSION IF NOT EXISTS vector;

-- Articles table
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT,
    url VARCHAR(1000) UNIQUE NOT NULL,
    author VARCHAR(200),
    source VARCHAR(50) NOT NULL,
    published_at TIMESTAMP NOT NULL,
    score INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    embedding vector(384),
    keywords JSONB,
    entities JSONB,
    tags JSONB,
    quality_score FLOAT DEFAULT 0.0,
    ranking_score FLOAT DEFAULT 0.0,
    content_type VARCHAR(50),
    article_metadata JSONB,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    topics JSONB,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    article_count INTEGER DEFAULT 0,
    summary_data JSONB,
    key_trends JSONB,
    strategic_insights JSONB,
    is_published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Topics table
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    keywords JSONB,
    sources JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    last_processed TIMESTAMP,
    article_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default topics
INSERT INTO topics (name, description, keywords) VALUES 
('AI', 'Artificial Intelligence and Machine Learning', '["artificial intelligence", "machine learning", "deep learning", "neural networks"]'),
('startup', 'Startup News and Funding', '["startup", "funding", "venture capital", "seed round"]'),
('fintech', 'Financial Technology', '["fintech", "cryptocurrency", "blockchain", "digital payments"]'),
('tech', 'General Technology News', '["technology", "software", "programming", "development"]'),
('MCP', 'Model Context Protocol', '["MCP", "model context protocol", "anthropic", "claude"]')
ON CONFLICT (name) DO NOTHING;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_ranking_score ON articles(ranking_score);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);
CREATE INDEX IF NOT EXISTS idx_topics_is_active ON topics(is_active);