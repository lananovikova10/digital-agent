#!/usr/bin/env python3
"""
Simple test script to run the agent with minimal setup
"""
import asyncio
import sys
import os

# Add the src directory to the path
sys.path.append('src')

from sources.hackernews import HackerNewsSource
from sources.yc_launches import YCLaunchesSource

async def test_sources():
    """Test individual sources"""
    print("Testing Hacker News...")
    hn = HackerNewsSource()
    hn_articles = await hn.fetch_articles("AI", days_back=1)
    print(f"Found {len(hn_articles)} HN articles")
    
    if hn_articles:
        print(f"Sample: {hn_articles[0]['title']}")
    
    print("\nTesting Y Combinator...")
    yc = YCLaunchesSource()
    yc_articles = await yc.fetch_articles("AI", days_back=7)
    print(f"Found {len(yc_articles)} YC articles")
    
    if yc_articles:
        print(f"Sample: {yc_articles[0]['title']}")

if __name__ == "__main__":
    asyncio.run(test_sources())