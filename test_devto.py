#!/usr/bin/env python3
"""
Test script for Dev.to source integration
"""
import asyncio
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sources.devto import DevToSource

async def test_devto():
    """Test Dev.to source"""
    print("Testing Dev.to source integration...")
    
    source = DevToSource()
    
    # Test with a popular topic
    topics = ["python", "AI", "javascript"]
    
    for topic in topics:
        print(f"\n--- Testing topic: {topic} ---")
        
        try:
            articles = await source.fetch_articles(topic, days_back=7)
            print(f"Found {len(articles)} articles for '{topic}'")
            
            # Show first few articles
            for i, article in enumerate(articles[:3]):
                print(f"\n{i+1}. {article['title']}")
                print(f"   Author: {article['author']}")
                print(f"   URL: {article['url']}")
                print(f"   Published: {article['published_at']}")
                print(f"   Score: {article['score']}")
                print(f"   Comments: {article['comments_count']}")
                print(f"   Tags: {', '.join(article['tags'])}")
                if article['content']:
                    content_preview = article['content'][:100] + "..." if len(article['content']) > 100 else article['content']
                    print(f"   Content: {content_preview}")
                    
        except Exception as e:
            print(f"Error testing topic '{topic}': {e}")

if __name__ == "__main__":
    asyncio.run(test_devto())