#!/usr/bin/env python3
"""
Test script for new data sources
"""
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sources.devto import DevToSource
from sources.medium import MediumSource
from sources.substack import SubstackSource
from sources.youtube_podcasts import YouTubePodcastSource
from sources.stackoverflow import StackOverflowSource
from sources.arxiv import ArxivSource
from sources.rss_feeds import RSSFeedsSource

async def test_source(source, name, topic="AI"):
    """Test a single source"""
    print(f"\n🔍 Testing {name}...")
    try:
        articles = await source.fetch_articles(topic, days_back=7)
        print(f"✅ {name}: Found {len(articles)} articles")
        
        if articles:
            # Show first article as example
            article = articles[0]
            print(f"   📄 Example: {article['title'][:80]}...")
            print(f"   👤 Author: {article['author']}")
            print(f"   🔗 URL: {article['url']}")
            
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)}")

async def main():
    """Test all new sources"""
    print("🚀 Testing New Data Sources")
    print("=" * 50)
    
    sources_to_test = [
        (DevToSource(), "Dev.to"),
        (MediumSource(), "Medium"),
        (SubstackSource(), "Substack"),
        (YouTubePodcastSource(), "YouTube/Podcasts"),
        (StackOverflowSource(), "Stack Overflow"),
        (ArxivSource(), "arXiv"),
        (RSSFeedsSource(), "RSS Feeds")
    ]
    
    for source, name in sources_to_test:
        await test_source(source, name)
    
    print(f"\n✅ Testing complete!")
    print("\n💡 Note: Some sources may show 0 articles if:")
    print("   - API rate limits are hit")
    print("   - No recent articles match the topic")
    print("   - Network connectivity issues")

if __name__ == "__main__":
    asyncio.run(main())