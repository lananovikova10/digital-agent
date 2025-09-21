#!/usr/bin/env python3
"""
Populate test data for the web interface
"""
import requests
import json
from datetime import datetime, timedelta
import random

API_BASE = "http://localhost:8000"

# Sample articles data with diverse sources
sample_articles = [
    {
        "title": "OpenAI Releases GPT-5 with Enhanced Reasoning Capabilities",
        "url": "https://news.ycombinator.com/item?id=38123456",
        "source": "hackernews",
        "author": "sam_altman",
        "content": "OpenAI has announced the release of GPT-5, featuring significantly improved reasoning capabilities and better performance on complex tasks. The new model shows remarkable improvements in mathematical reasoning, code generation, and scientific analysis.",
        "score": 1250,
        "comments_count": 342,
        "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "ranking_score": 0.95
    },
    {
        "title": "New MCP Server Protocol Discussion",
        "url": "https://reddit.com/r/MachineLearning/comments/abc123",
        "source": "reddit",
        "author": "ai_researcher",
        "content": "The Model Context Protocol (MCP) has been updated with new features that allow for better integration between AI models and external systems. This enables more sophisticated AI workflows and better data handling.",
        "score": 890,
        "comments_count": 156,
        "published_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "ranking_score": 0.87
    },
    {
        "title": "AI Coding Assistant Launches on Product Hunt",
        "url": "https://producthunt.com/posts/ai-coding-assistant",
        "source": "producthunt",
        "author": "startup_founder",
        "content": "A new AI-powered coding assistant has launched, promising to revolutionize how developers write code. The tool uses advanced language models to provide intelligent code suggestions and automated refactoring.",
        "score": 450,
        "comments_count": 67,
        "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "ranking_score": 0.82
    },
    {
        "title": "Breaking: Major AI Breakthrough Announced",
        "url": "https://twitter.com/ai_news/status/1234567890",
        "source": "twitter",
        "author": "ai_news",
        "content": "BREAKING: Researchers at Stanford announce breakthrough in AI reasoning capabilities. New model shows human-level performance on complex logical tasks. This could change everything! #AI #MachineLearning",
        "score": 2340,
        "comments_count": 89,
        "published_at": (datetime.now() - timedelta(hours=6)).isoformat(),
        "ranking_score": 0.93
    },
    {
        "title": "YC Startup Raises $50M for AI Development Tools",
        "url": "https://ycombinator.com/launches/abc-ai-dev-tools",
        "source": "yc_launches",
        "author": "yc_team",
        "content": "A Y Combinator startup has raised $50 million in Series A funding to develop AI-powered software development tools. The platform promises to automate routine coding tasks and improve developer productivity.",
        "score": 750,
        "comments_count": 89,
        "published_at": (datetime.now() - timedelta(days=3)).isoformat(),
        "ranking_score": 0.78
    },
    {
        "title": "TechCrunch: The Future of AI in Enterprise",
        "url": "https://techcrunch.com/2025/09/21/future-ai-enterprise",
        "source": "techcrunch",
        "author": "sarah_perez",
        "content": "Enterprise adoption of AI is accelerating rapidly, with companies investing billions in AI infrastructure and talent. New survey data shows 78% of Fortune 500 companies plan to increase AI spending in 2025.",
        "score": 1200,
        "comments_count": 234,
        "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "ranking_score": 0.88
    },
    {
        "title": "Meta's New AI Model Goes Viral on Reddit",
        "url": "https://reddit.com/r/artificial/comments/xyz789",
        "source": "reddit",
        "author": "meta_ai",
        "content": "Meta has open-sourced a new AI model specifically designed for code generation and software development tasks. The model is trained on billions of lines of code and supports multiple programming languages.",
        "score": 1450,
        "comments_count": 234,
        "published_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "ranking_score": 0.85
    },
    {
        "title": "Anthropic Claude 4 Safety Features",
        "url": "https://news.ycombinator.com/item?id=38987654",
        "source": "hackernews",
        "author": "anthropic_team",
        "content": "Anthropic has released Claude 4, featuring enhanced safety mechanisms and better alignment with human values. The model includes new constitutional AI techniques and improved robustness against adversarial inputs.",
        "score": 2100,
        "comments_count": 567,
        "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "ranking_score": 0.92
    },
    {
        "title": "Revolutionary AI Tool Trending",
        "url": "https://producthunt.com/posts/revolutionary-ai-tool",
        "source": "producthunt",
        "author": "product_maker",
        "content": "This revolutionary AI tool is changing how teams collaborate on complex projects. With advanced natural language processing and intelligent task automation, it's the future of productivity.",
        "score": 680,
        "comments_count": 45,
        "published_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "ranking_score": 0.79
    },
    {
        "title": "AI Industry Shakeup: Major Acquisition",
        "url": "https://techcrunch.com/2025/09/20/ai-industry-acquisition",
        "source": "techcrunch",
        "author": "alex_wilhelm",
        "content": "In a surprise move, tech giant acquires leading AI startup for $2.5 billion. The acquisition is expected to accelerate development of next-generation AI products and services across multiple industries.",
        "score": 890,
        "comments_count": 156,
        "published_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "ranking_score": 0.86
    }
]

def populate_articles():
    """Add sample articles directly to the database"""
    print("Populating test articles...")
    
    # We'll need to use the database directly since there's no API endpoint for adding articles
    # For now, let's just create a report that will trigger article storage
    
    # Generate a report which should store articles
    response = requests.post(
        f"{API_BASE}/reports/generate",
        json={"topics": ["AI", "software development", "MCP"]}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Generated report: {result['report_id']}")
        return result['report_id']
    else:
        print(f"❌ Failed to generate report: {response.text}")
        return None

def main():
    print("🚀 Populating test data for Weekly Intelligence Agent")
    
    # Generate a report to populate articles
    report_id = populate_articles()
    
    if report_id:
        print(f"✅ Test data populated successfully!")
        print(f"📊 View the web interface at: http://localhost:3000")
        print(f"📄 View the report at: http://localhost:3000/reports/{report_id}")
    else:
        print("❌ Failed to populate test data")

if __name__ == "__main__":
    main()