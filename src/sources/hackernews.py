"""
Hacker News data source
"""
import asyncio
import httpx
from typing import List, Dict, Any
from datetime import datetime
import structlog

from .base import BaseSource

logger = structlog.get_logger()


class HackerNewsSource(BaseSource):
    """Hacker News API integration"""
    
    def __init__(self):
        super().__init__("hackernews")
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.search_url = "https://hn.algolia.com/api/v1/search"
    
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch HN articles matching the topic"""
        logger.info("Fetching from Hacker News", topic=topic)
        
        async with httpx.AsyncClient() as client:
            # Search for stories
            search_params = {
                'query': topic,
                'tags': 'story',
                'numericFilters': f'created_at_i>{int((datetime.now().timestamp() - days_back * 86400))}'
            }
            
            response = await client.get(self.search_url, params=search_params)
            response.raise_for_status()
            
            search_data = response.json()
            articles = []
            
            for hit in search_data.get('hits', []):
                article = self._parse_hn_story(hit)
                if article:
                    articles.append(self._standardize_article(article))
        
        logger.info("HN fetch complete", count=len(articles))
        return articles
    
    def _parse_hn_story(self, hit: Dict[str, Any]) -> Dict[str, Any]:
        """Parse HN story from API response"""
        return {
            'title': hit.get('title', ''),
            'content': hit.get('story_text', ''),
            'url': hit.get('url') or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            'author': hit.get('author', ''),
            'published_at': datetime.fromtimestamp(hit.get('created_at_i', 0)),
            'score': hit.get('points', 0),
            'comments_count': hit.get('num_comments', 0),
            'tags': hit.get('_tags', []),
            'metadata': {
                'hn_id': hit.get('objectID'),
                'story_id': hit.get('story_id')
            }
        }