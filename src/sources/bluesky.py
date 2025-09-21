"""
Bluesky source for fetching posts
"""
import asyncio
import aiohttp
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog
import os

from .base import BaseSource

logger = structlog.get_logger()


class BlueskySource(BaseSource):
    """Fetches posts from Bluesky"""
    
    def __init__(self):
        super().__init__('bluesky')
        self.base_url = 'https://bsky.social/xrpc'
        self.rate_limit_delay = 1.0
        self.session_token = None
        
        # Get credentials from environment
        self.identifier = os.getenv('BLUESKY_IDENTIFIER')  # username or email
        self.password = os.getenv('BLUESKY_PASSWORD')
    
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch posts from Bluesky"""
        logger.info("Fetching from Bluesky", topic=topic)
        
        if not self.identifier or not self.password:
            logger.warning("Bluesky credentials not found")
            return []
        
        try:
            articles = []
            
            async with aiohttp.ClientSession() as session:
                # Authenticate
                if await self._authenticate(session):
                    # Search for posts
                    search_articles = await self._search_posts(session, topic, days_back)
                    articles.extend(search_articles)
                    
                    # Get posts from tech-focused feeds
                    feed_articles = await self._fetch_tech_feeds(session, topic, days_back)
                    articles.extend(feed_articles)
            
            # Remove duplicates by URL/URI
            seen_uris = set()
            unique_articles = []
            for article in articles:
                uri = article.get('metadata', {}).get('uri', article['url'])
                if uri not in seen_uris:
                    seen_uris.add(uri)
                    unique_articles.append(article)
            
            logger.info("Bluesky fetch complete", count=len(unique_articles))
            return unique_articles
            
        except Exception as e:
            logger.error("Bluesky fetch error", error=str(e))
            return []
    
    async def _authenticate(self, session: aiohttp.ClientSession) -> bool:
        """Authenticate with Bluesky"""
        try:
            url = f"{self.base_url}/com.atproto.server.createSession"
            data = {
                'identifier': self.identifier,
                'password': self.password
            }
            
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.session_token = result.get('accessJwt')
                    return True
                else:
                    logger.warning("Bluesky authentication failed", status=response.status)
                    return False
                    
        except Exception as e:
            logger.warning("Bluesky authentication error", error=str(e))
            return False
    
    async def _search_posts(self, session: aiohttp.ClientSession, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Search for posts by topic"""
        articles = []
        
        if not self.session_token:
            return articles
        
        try:
            headers = {
                'Authorization': f'Bearer {self.session_token}'
            }
            
            url = f"{self.base_url}/app.bsky.feed.searchPosts"
            params = {
                'q': topic,
                'limit': 25
            }
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for post in data.get('posts', []):
                        article = self._parse_post(post)
                        if article and self._is_recent(article['published_at'], days_back):
                            articles.append(article)
                
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.warning("Bluesky search error", error=str(e))
        
        return articles
    
    async def _fetch_tech_feeds(self, session: aiohttp.ClientSession, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Fetch posts from tech-focused feeds"""
        articles = []
        
        if not self.session_token:
            return articles
        
        try:
            headers = {
                'Authorization': f'Bearer {self.session_token}'
            }
            
            # Get timeline (following feed)
            url = f"{self.base_url}/app.bsky.feed.getTimeline"
            params = {
                'limit': 50
            }
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    topic_lower = topic.lower()
                    for item in data.get('feed', []):
                        post = item.get('post', {})
                        
                        # Check if post is relevant to topic
                        text = post.get('record', {}).get('text', '').lower()
                        if topic_lower in text:
                            article = self._parse_post(post)
                            if article and self._is_recent(article['published_at'], days_back):
                                articles.append(article)
                
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.warning("Bluesky feed fetch error", error=str(e))
        
        return articles
    
    def _parse_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Bluesky post"""
        try:
            # Get post record
            record = post.get('record', {})
            
            # Parse creation time
            created_at_str = record.get('createdAt', '')
            if created_at_str:
                # Parse ISO format: 2024-01-01T12:00:00.000Z
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            else:
                created_at = datetime.now()
            
            # Get author info
            author_info = post.get('author', {})
            author = author_info.get('displayName') or author_info.get('handle', 'Unknown')
            
            # Get post text
            text = record.get('text', '')
            
            # Create URL
            uri = post.get('uri', '')
            # Convert AT URI to web URL
            url = self._convert_uri_to_url(uri, author_info.get('handle', ''))
            
            # Get engagement metrics
            like_count = post.get('likeCount', 0)
            repost_count = post.get('repostCount', 0)
            reply_count = post.get('replyCount', 0)
            
            return self._standardize_article({
                'title': text[:100] + '...' if len(text) > 100 else text,  # Use first part as title
                'content': text,
                'url': url,
                'author': author,
                'published_at': created_at,
                'score': like_count + repost_count * 2,  # Weight reposts more
                'comments_count': reply_count,
                'tags': ['bluesky', 'social'],
                'metadata': {
                    'uri': uri,
                    'like_count': like_count,
                    'repost_count': repost_count,
                    'reply_count': reply_count,
                    'author_handle': author_info.get('handle', ''),
                    'author_did': author_info.get('did', '')
                }
            })
            
        except Exception as e:
            logger.warning("Bluesky post parse error", error=str(e))
            return None
    
    def _convert_uri_to_url(self, uri: str, handle: str) -> str:
        """Convert AT URI to web URL"""
        try:
            if uri.startswith('at://'):
                # Extract the record key (post ID)
                parts = uri.split('/')
                if len(parts) >= 5:
                    record_key = parts[-1]
                    return f"https://bsky.app/profile/{handle}/post/{record_key}"
            
            return uri
            
        except Exception:
            return uri