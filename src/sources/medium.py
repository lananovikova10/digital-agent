"""
Medium source for fetching articles from specific publications
"""
import asyncio
import aiohttp
import feedparser
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog
import re

from .base import BaseSource

logger = structlog.get_logger()


class MediumSource(BaseSource):
    """Fetches articles from Medium publications via RSS"""
    
    def __init__(self):
        super().__init__('medium')
        self.rate_limit_delay = 2.0
        
        # Popular tech publications on Medium
        self.publications = {
            'towards-data-science': 'https://towardsdatascience.com/feed',
            'better-programming': 'https://betterprogramming.pub/feed',
            'the-startup': 'https://medium.com/swlh/feed',
            'hackernoon': 'https://hackernoon.com/feed',
            'freecodecamp': 'https://www.freecodecamp.org/news/rss/',
            'ai-in-plain-english': 'https://ai.plainenglish.io/feed',
            'level-up-coding': 'https://levelup.gitconnected.com/feed',
            'the-innovation': 'https://medium.com/the-innovation/feed',
            'analytics-vidhya': 'https://medium.com/analytics-vidhya/feed',
            'machine-learning-in-action': 'https://medium.com/machine-learning-in-action/feed'
        }
    
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch articles from Medium publications"""
        logger.info("Fetching from Medium", topic=topic)
        
        try:
            articles = []
            
            async with aiohttp.ClientSession() as session:
                tasks = []
                for pub_name, rss_url in self.publications.items():
                    task = self._fetch_publication(session, pub_name, rss_url, topic, days_back)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        articles.extend(result)
                    elif isinstance(result, Exception):
                        logger.warning("Medium publication fetch error", error=str(result))
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            logger.info("Medium fetch complete", count=len(unique_articles))
            return unique_articles
            
        except Exception as e:
            logger.error("Medium fetch error", error=str(e))
            return []
    
    async def _fetch_publication(self, session: aiohttp.ClientSession, pub_name: str, rss_url: str, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Fetch articles from a specific Medium publication"""
        articles = []
        
        try:
            async with session.get(rss_url) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    topic_lower = topic.lower()
                    for entry in feed.entries:
                        # Check if article is relevant to topic
                        title = entry.get('title', '').lower()
                        summary = entry.get('summary', '').lower()
                        tags = [tag.get('term', '').lower() for tag in entry.get('tags', [])]
                        
                        if (topic_lower in title or 
                            topic_lower in summary or
                            any(topic_lower in tag for tag in tags)):
                            
                            article = self._parse_entry(entry, pub_name)
                            if article and self._is_recent(article['published_at'], days_back):
                                articles.append(article)
                
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.warning("Medium publication fetch error", publication=pub_name, error=str(e))
        
        return articles
    
    def _parse_entry(self, entry: Dict[str, Any], publication: str) -> Dict[str, Any]:
        """Parse Medium RSS entry"""
        try:
            # Parse published date
            published_at = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_at = datetime(*entry.updated_parsed[:6])
            
            # Extract author
            author = ''
            if hasattr(entry, 'author'):
                author = entry.author
            elif hasattr(entry, 'authors') and entry.authors:
                author = entry.authors[0].get('name', '')
            
            # Clean content
            content = entry.get('summary', '')
            if content:
                # Remove HTML tags
                content = re.sub(r'<[^>]+>', '', content)
                content = content.strip()[:500]
            
            # Extract tags
            tags = []
            if hasattr(entry, 'tags'):
                tags = [tag.get('term', '') for tag in entry.tags if tag.get('term')]
            
            return self._standardize_article({
                'title': entry.get('title', ''),
                'content': content,
                'url': entry.get('link', ''),
                'author': author,
                'published_at': published_at,
                'score': 0,  # Medium doesn't provide clap counts via RSS
                'comments_count': 0,
                'tags': tags,
                'metadata': {
                    'publication': publication,
                    'guid': entry.get('id', ''),
                    'medium_url': entry.get('link', '')
                }
            })
            
        except Exception as e:
            logger.warning("Medium entry parse error", error=str(e))
            return None