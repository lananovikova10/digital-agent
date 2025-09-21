"""
Dev.to source for fetching articles
"""
import asyncio
import aiohttp
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog

from .base import BaseSource

logger = structlog.get_logger()


class DevToSource(BaseSource):
    """Fetches articles from Dev.to"""
    
    def __init__(self):
        super().__init__('devto')
        self.base_url = 'https://dev.to/api'
        self.rate_limit_delay = 1.0
    
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch articles from Dev.to"""
        logger.info("Fetching from Dev.to", topic=topic)
        
        try:
            articles = []
            
            # Fetch latest articles with topic search
            async with aiohttp.ClientSession() as session:
                # Get articles by tag
                tag_articles = await self._fetch_by_tag(session, topic, days_back)
                articles.extend(tag_articles)
                
                # Get articles by search
                search_articles = await self._fetch_by_search(session, topic, days_back)
                articles.extend(search_articles)
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            logger.info("Dev.to fetch complete", count=len(unique_articles))
            return unique_articles
            
        except Exception as e:
            logger.error("Dev.to fetch error", error=str(e))
            return []
    
    async def _fetch_by_tag(self, session: aiohttp.ClientSession, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Fetch articles by tag"""
        articles = []
        
        # Convert topic to tag format
        tag = topic.lower().replace(' ', '').replace('-', '')
        
        try:
            url = f"{self.base_url}/articles"
            params = {
                'tag': tag,
                'per_page': 30,
                'state': 'fresh'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data:
                        article = self._parse_article(item)
                        if article and self._is_recent(article['published_at'], days_back):
                            articles.append(article)
                
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.warning("Dev.to tag fetch error", tag=tag, error=str(e))
        
        return articles
    
    async def _fetch_by_search(self, session: aiohttp.ClientSession, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Fetch articles by search"""
        articles = []
        
        try:
            url = f"{self.base_url}/articles"
            params = {
                'per_page': 20,
                'state': 'fresh'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Filter by topic in title or tags
                    topic_lower = topic.lower()
                    for item in data:
                        title = item.get('title', '').lower()
                        # Handle both string and dict formats for tags
                        tag_list = item.get('tag_list', [])
                        if isinstance(tag_list, list):
                            if tag_list and isinstance(tag_list[0], dict):
                                tags = [tag.get('name', '').lower() for tag in tag_list]
                            else:
                                tags = [str(tag).lower() for tag in tag_list]
                        else:
                            tags = []
                        
                        if (topic_lower in title or 
                            any(topic_lower in tag for tag in tags)):
                            article = self._parse_article(item)
                            if article and self._is_recent(article['published_at'], days_back):
                                articles.append(article)
                
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.warning("Dev.to search fetch error", topic=topic, error=str(e))
        
        return articles
    
    def _parse_article(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Dev.to article format"""
        try:
            # Parse published date
            published_str = item.get('published_at', '')
            if published_str:
                try:
                    # Handle different datetime formats
                    if published_str.endswith('Z'):
                        published_at = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    else:
                        published_at = datetime.fromisoformat(published_str)
                    
                    # Make timezone-naive for comparison
                    if published_at.tzinfo is not None:
                        published_at = published_at.replace(tzinfo=None)
                except ValueError:
                    published_at = datetime.now()
            else:
                published_at = datetime.now()
            
            # Extract tags
            tags = []
            if 'tag_list' in item:
                tag_list = item['tag_list']
                if isinstance(tag_list, list):
                    if tag_list and isinstance(tag_list[0], dict):
                        tags = [tag.get('name', '') for tag in tag_list if tag.get('name')]
                    else:
                        tags = [str(tag) for tag in tag_list if tag]
            
            return self._standardize_article({
                'title': item.get('title', ''),
                'content': item.get('description', '') or item.get('body_markdown', '')[:500],
                'url': item.get('url', ''),
                'author': item.get('user', {}).get('name', '') or item.get('user', {}).get('username', ''),
                'published_at': published_at,
                'score': item.get('public_reactions_count', 0),
                'comments_count': item.get('comments_count', 0),
                'tags': tags,
                'metadata': {
                    'reading_time': item.get('reading_time_minutes', 0),
                    'cover_image': item.get('cover_image', ''),
                    'canonical_url': item.get('canonical_url', '')
                }
            })
            
        except Exception as e:
            logger.warning("Dev.to article parse error", error=str(e))
            return None