#!/usr/bin/env python3
"""
Test source manager integration with new sources
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sources.manager import SourceManager

async def main():
    """Test source manager with new sources"""
    print("🔍 Testing Source Manager Integration")
    print("=" * 50)
    
    manager = SourceManager()
    
    # List available sources
    sources = manager.get_available_sources()
    print(f"📋 Available sources ({len(sources)}):")
    for source in sorted(sources):
        print(f"   • {source}")
    
    print(f"\n🚀 Testing fetch from all sources...")
    
    # Test fetching from all sources
    articles = await manager.fetch_all_sources("AI", days_back=3)
    
    print(f"\n📊 Results:")
    print(f"   Total articles: {len(articles)}")
    
    # Group by source
    by_source = {}
    for article in articles:
        source = article.get('source', 'unknown')
        by_source[source] = by_source.get(source, 0) + 1
    
    print(f"\n📈 Articles by source:")
    for source, count in sorted(by_source.items()):
        print(f"   • {source}: {count} articles")
    
    # Show some examples
    print(f"\n📄 Sample articles:")
    for i, article in enumerate(articles[:5]):
        print(f"   {i+1}. [{article['source']}] {article['title'][:60]}...")

if __name__ == "__main__":
    asyncio.run(main())