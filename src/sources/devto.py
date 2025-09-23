"""
Dev.to data source
"""
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog
import requests
import asyncio
import aiohttp

from .base import BaseSource

logger = structlog.get_logger()


class DevToSource(BaseSource):
    """Dev.to API integration"""
    
    def __init__(self):
        super().__init__("devto")
        self.api_base = "https://dev.to/api"
        self.rate_limit_delay = 1.0  # Dev.to allows 10 requests per second
        
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch articles from Dev.to API"""
        logger.info("Fetching from Dev.to", topic=topic)
        
        articles = []
        
        try:
            # Search for articles by tag/topic
            search_results = await self._search_articles_by_tag(topic, days_back)
            articles.extend(search_results)
            
            # Also search for articles containing the topic in title/content
            text_search_results = await self._search_articles_by_text(topic, days_back)
            articles.extend(text_search_results)
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            articles = unique_articles
            
        except Exception as e:
            logger.error("Dev.to API error", error=str(e))
            return []
        
        logger.info("Dev.to fetch complete", count=len(articles))
        return articles
    
    async def _search_articles_by_tag(self, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Search articles by tag"""
        articles = []
        
        try:
            # Convert topic to tag format (lowercase, replace spaces with hyphens)
            tag = topic.lower().replace(" ", "").replace("-", "")
            
            async with aiohttp.ClientSession() as session:
                # Get articles by tag
                url = f"{self.api_base}/articles"
                params = {
                    'tag': tag,
                    'per_page': 50,
                    'top': 7  # Get top articles from past week
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for item in data:
                            article = self._parse_article(item)
                            if article and self._is_recent(article['published_at'], days_back):
                                articles.append(self._standardize_article(article))
                    else:
                        logger.warning("Dev.to tag search failed", status=response.status)
                
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.error("Dev.to tag search error", error=str(e))
        
        return articles
    
    async def _search_articles_by_text(self, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Search articles by text content"""
        articles = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get recent articles and filter by topic
                url = f"{self.api_base}/articles"
                params = {
                    'per_page': 100,
                    'top': 7  # Get top articles from past week
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for item in data:
                            if self._is_relevant(item, topic):
                                article = self._parse_article(item)
                                if article and self._is_recent(article['published_at'], days_back):
                                    articles.append(self._standardize_article(article))
                    else:
                        logger.warning("Dev.to text search failed", status=response.status)
                
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.error("Dev.to text search error", error=str(e))
        
        return articles
    
    def _is_relevant(self, article_data: Dict[str, Any], topic: str) -> bool:
        """Check if article is relevant to the topic"""
        topic_lower = topic.lower()
        title_lower = article_data.get('title', '').lower()
        description_lower = article_data.get('description', '').lower()
        tags = [tag.lower() for tag in article_data.get('tag_list', [])]
        
        return (
            topic_lower in title_lower or 
            topic_lower in description_lower or
            any(topic_lower in tag for tag in tags) or
            any(tag in topic_lower for tag in tags if len(tag) > 2)
        )
    
    def _parse_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Dev.to article data"""
        try:
            # Parse publication date
            published_str = article_data.get('published_at', article_data.get('created_at'))
            if published_str:
                # Dev.to returns ISO format: "2023-12-01T10:30:00Z"
                published_at = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                # Convert to naive datetime for consistency with other sources
                published_at = published_at.replace(tzinfo=None)
            else:
                published_at = datetime.now()
            
            # Extract user info
            user_info = article_data.get('user', {})
            author = user_info.get('name', user_info.get('username', 'Unknown'))
            
            # Get article content/description
            content = article_data.get('description', '')
            if not content:
                content = article_data.get('body_markdown', '')[:500] + '...' if article_data.get('body_markdown') else ''
            
            return {
                'title': article_data.get('title', ''),
                'content': content,
                'url': article_data.get('url', ''),
                'author': author,
                'published_at': published_at,
                'score': article_data.get('public_reactions_count', 0),
                'comments_count': article_data.get('comments_count', 0),
                'tags': article_data.get('tag_list', []),
                'metadata': {
                    'article_id': article_data.get('id'),
                    'reading_time': article_data.get('reading_time_minutes', 0),
                    'cover_image': article_data.get('cover_image'),
                    'social_image': article_data.get('social_image'),
                    'canonical_url': article_data.get('canonical_url'),
                    'organization': article_data.get('organization', {}).get('name') if article_data.get('organization') else None
                }
            }
            
        except Exception as e:
            logger.error("Failed to parse Dev.to article", error=str(e), article_id=article_data.get('id'))
            return None