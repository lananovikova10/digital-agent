"""
Product Hunt data source
"""
import os
import httpx
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog

from .base import BaseSource

logger = structlog.get_logger()


class ProductHuntSource(BaseSource):
    """Product Hunt API integration"""
    
    def __init__(self):
        super().__init__("producthunt")
        self.api_key = os.getenv('PRODUCTHUNT_API_KEY')
        self.base_url = "https://api.producthunt.com/v2/api/graphql"
        
        if not self.api_key:
            logger.warning("Product Hunt API key not found")
    
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch Product Hunt launches matching the topic"""
        if not self.api_key:
            logger.warning("Product Hunt API key not configured")
            return []
        
        logger.info("Fetching from Product Hunt", topic=topic)
        
        articles = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Get recent posts
                for days_ago in range(days_back):
                    date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                    posts = await self._fetch_posts_for_date(client, date)
                    
                    for post in posts:
                        if self._is_relevant_to_topic(post, topic):
                            article = self._parse_ph_post(post)
                            articles.append(self._standardize_article(article))
        
        except Exception as e:
            logger.error("Product Hunt API error", error=str(e))
            return []
        
        logger.info("Product Hunt fetch complete", count=len(articles))
        return articles
    
    async def _fetch_posts_for_date(self, client: httpx.AsyncClient, date: str) -> List[Dict[str, Any]]:
        """Fetch posts for a specific date"""
        query = """
        query GetPosts($postedAfter: DateTime!, $postedBefore: DateTime!) {
            posts(postedAfter: $postedAfter, postedBefore: $postedBefore, first: 50) {
                edges {
                    node {
                        id
                        name
                        tagline
                        description
                        url
                        votesCount
                        commentsCount
                        createdAt
                        featuredAt
                        user {
                            name
                            username
                        }
                        topics {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "postedAfter": f"{date}T00:00:00Z",
            "postedBefore": f"{date}T23:59:59Z"
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = await client.post(
            self.base_url,
            json={"query": query, "variables": variables},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return [edge['node'] for edge in data.get('data', {}).get('posts', {}).get('edges', [])]
        
        return []
    
    def _parse_ph_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Product Hunt post"""
        topics = [edge['node']['name'] for edge in post.get('topics', {}).get('edges', [])]
        
        return {
            'title': post.get('name', ''),
            'content': post.get('description', post.get('tagline', '')),
            'url': post.get('url', ''),
            'author': post.get('user', {}).get('username', ''),
            'published_at': datetime.fromisoformat(post.get('createdAt', '').replace('Z', '+00:00')),
            'score': post.get('votesCount', 0),
            'comments_count': post.get('commentsCount', 0),
            'tags': topics,
            'metadata': {
                'ph_id': post.get('id'),
                'tagline': post.get('tagline', ''),
                'featured_at': post.get('featuredAt')
            }
        }
    
    def _is_relevant_to_topic(self, post: Dict[str, Any], topic: str) -> bool:
        """Check if post is relevant to the topic"""
        topic_lower = topic.lower()
        
        # Check name, tagline, and description
        text_fields = [
            post.get('name', ''),
            post.get('tagline', ''),
            post.get('description', '')
        ]
        
        for field in text_fields:
            if topic_lower in field.lower():
                return True
        
        # Check topics
        topics = [edge['node']['name'] for edge in post.get('topics', {}).get('edges', [])]
        for ph_topic in topics:
            if topic_lower in ph_topic.lower():
                return True
        
        return False