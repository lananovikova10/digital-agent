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

1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment: `cp .env.example .env`
3. Initialize database: `python scripts/init_db.py`
4. Start services: `docker-compose up -d`
5. Run agent: `python -m src.agents.weekly_intel`

## Features

- Multi-source data ingestion (HN, Reddit, X, PH, YC)
- Intelligent content ranking and filtering
- Automated weekly report generation
- Strategic insights based on product needs
- Configurable topic tracking
- Real-time monitoring and alerting