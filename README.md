# Weekly Intelligence Agent

An AI-powered agent that sources information from Hacker News, Reddit, X (Twitter), Product Hunt, YC launches, and other sources to generate summarized weekly reports with trends and strategic takeaways.

## Architecture

- **Core**: Python with LangGraph for agentic workflows
- **API**: FastAPI for service endpoints
- **Storage**: PostgreSQL with pgvector for embeddings
- **Scheduling**: Celery with Redis backend
- **Monitoring**: OpenTelemetry for distributed tracing
- **Agent Framework**: LangGraph state machine with deterministic workflows

## Project Structure

```
weekly-intel-agent/
├── src/
│   ├── agents/           # LangGraph agent definitions
│   ├── sources/          # Data source integrations
│   ├── processors/       # Data processing and enrichment
│   ├── storage/          # Database models and operations
│   ├── api/              # FastAPI endpoints
│   └── utils/            # Shared utilities
├── config/               # Configuration files
├── docker/               # Docker configurations
├── tests/                # Test suite
└── scripts/              # Deployment and utility scripts
```

## Quick Start

### Option 1: Full Docker Setup (Recommended)

```bash
# 1. Clone and setup
git clone <repository-url>
cd weekly-intel-agent
cp .env.example .env

# 2. Edit .env file with your API keys (at minimum add OPENAI_API_KEY)
# Optional: Add REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, TWITTER_BEARER_TOKEN, PRODUCTHUNT_API_KEY

# 3. Start all services
docker compose up -d

# 4. Wait for services to be ready (about 30 seconds)
# 5. View the web interface at http://localhost:3000
# 6. API available at http://localhost:8000
```

### Option 2: Local Development

```bash
# 1. Setup Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start database services
docker compose up -d postgres redis

# 4. Initialize database
python scripts/init_db.py

# 5. Start API server
uvicorn src.api.main:app --reload --port 8000

# 6. In another terminal, start web interface
python src/web/app.py

# 7. Generate a test report
python populate_test_data.py
```

### Option 3: Quick Test with Sample Data

```bash
# 1. Start services
docker compose up -d

# 2. Generate test report (no API keys needed)
python populate_test_data.py

# 3. View at http://localhost:3000
```

### Running the Agent

```bash
# Generate a report manually
python -m src.agents.weekly_intel --topics "AI,machine learning,developer tools"

# Or use the web interface to generate reports
# Visit http://localhost:3000/generate
```

## Features

### 🔍 **Multi-Source Data Ingestion**

#### **News & Discussion**
- **Hacker News**: Top stories and discussions
- **Reddit**: Relevant subreddit posts  
- **TechCrunch**: Latest tech news and funding announcements
- **Twitter/X**: Tech industry tweets (with API key)
- **Bluesky**: Social media posts (with credentials)

#### **Developer Content**
- **Dev.to**: Developer articles and tutorials
- **Stack Overflow**: Questions and answers by tags
- **Medium**: Tech publications (Towards Data Science, Better Programming, etc.)
- **GitHub Blog**: Official GitHub updates and features

#### **Research & Analysis**
- **arXiv**: Latest research papers in AI, ML, CS
- **Substack**: Tech newsletters (Stratechery, Platformer, etc.)
- **Company Blogs**: OpenAI, Anthropic, DeepMind, Meta AI via RSS

#### **Video & Audio Content**
- **YouTube Channels**: Two Minute Papers, Lex Fridman, AI Explained
- **Podcasts**: Practical AI, TWIML, Latent Space, Machine Learning Street Talk

#### **Startup Ecosystem**
- **YC Launches**: Y Combinator startup launches
- **Product Hunt**: New product launches (with API key)
- **Crunchbase**: Funding news and startup updates

### 🧠 **Intelligent Processing**
- **Content Ranking**: ML-based scoring and relevance filtering
- **Duplicate Detection**: Automatic deduplication of similar articles
- **Quality Assessment**: Content quality scoring and filtering
- **Keyword Extraction**: Automatic topic and keyword identification
- **HTML Decoding**: Clean text extraction from web content

### 📊 **Report Generation**
- **Weekly Intelligence Reports**: Comprehensive summaries with insights
- **Strategic Analysis**: Business implications and recommendations
- **Key Quotes**: Meaningful excerpts from top articles (no more URL-only quotes!)
- **Trend Identification**: Pattern recognition across sources
- **Customizable Topics**: Focus on specific areas of interest

### 🌐 **Web Interface**
- **Interactive Dashboard**: Browse and filter reports
- **Report Generation**: Create reports on-demand
- **Article Details**: Full article content and metadata
- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Live report generation status

### ⚙️ **Technical Features**
- **LangGraph Workflows**: Deterministic agent execution
- **PostgreSQL + pgvector**: Scalable storage with embeddings
- **FastAPI**: High-performance REST API
- **Docker Support**: Easy deployment and scaling
- **Configurable Sources**: Enable/disable sources as needed

## Configuration

### Required API Keys
- **OpenAI API Key**: For AI-powered analysis and report generation
  - Get from: https://platform.openai.com/api-keys
  - Set in `.env`: `OPENAI_API_KEY=your_key_here`

### Optional API Keys (for enhanced data sources)
- **Reddit API**: For Reddit posts
  - Get from: https://www.reddit.com/prefs/apps
  - Set: `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`
- **Twitter/X Bearer Token**: For Twitter posts
  - Get from: https://developer.twitter.com/
  - Set: `TWITTER_BEARER_TOKEN`
- **Product Hunt API**: For Product Hunt launches
  - Get from: https://api.producthunt.com/v2/docs
  - Set: `PRODUCTHUNT_API_KEY`

### Working Without API Keys
The system works with many sources that don't require API keys:
- **Hacker News**: Always available
- **TechCrunch**: RSS feed access  
- **YC Launches**: Web scraping
- **Dev.to**: Public API
- **Medium**: RSS feeds from publications
- **Substack**: RSS feeds from newsletters
- **YouTube/Podcasts**: RSS feeds
- **Stack Overflow**: Public API
- **arXiv**: Public API
- **Company RSS Feeds**: OpenAI, Anthropic, GitHub, etc.

### Topics Configuration
Edit topics in `.env` or specify when running:
```bash
# In .env file
TOPICS=["AI", "machine learning", "developer tools", "startup funding"]

# Or via command line
python -m src.agents.weekly_intel --topics "AI,blockchain,fintech"
```

## Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Make sure PostgreSQL is running
docker compose up -d postgres
# Wait 30 seconds, then initialize
python scripts/init_db.py
```

**Port Already in Use**
```bash
# Check what's using the ports
lsof -i :3000  # Web interface
lsof -i :8000  # API
lsof -i :5432  # PostgreSQL

# Stop conflicting services or change ports in docker-compose.yml
```

**No Articles Found**
- Check your internet connection
- Verify API keys are correct (for Reddit, Twitter, Product Hunt)
- Try with just Hacker News: it requires no API keys
- Check logs: `docker compose logs -f`

**Web Interface Not Loading**
```bash
# Check if services are running
docker compose ps

# Restart web service
docker compose restart web

# Check logs
docker compose logs web
```

### Getting Help

1. **Check System Status**: Look at `SYSTEM_STATUS.md` for current known issues
2. **View Logs**: `docker compose logs -f [service_name]`
3. **Test Individual Components**:
   ```bash
   # Test API
   curl http://localhost:8000/health
   
   # Test database
   python scripts/init_db.py
   
   # Generate test data
   python populate_test_data.py
   ```

## Development

### Project Structure
```
src/
├── agents/           # LangGraph agent workflows
├── api/             # FastAPI endpoints  
├── processors/      # Content processing and AI analysis
├── sources/         # Data source integrations
├── storage/         # Database models and operations
├── web/            # Web interface (Flask)
└── utils/          # Shared utilities
```

### Running Tests
```bash
# Run all tests
make test

# Run specific test
python -m pytest tests/test_sources.py -v
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request