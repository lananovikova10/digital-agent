"""
Stack Overflow source for fetching questions by tags
"""
import asyncio
import aiohttp
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog
import html

from .base import BaseSource

logger = structlog.get_logger()


class StackOverflowSource(BaseSource):
    """Fetches questions from Stack Overflow by tags"""
    
    def __init__(self):
        super().__init__('stackoverflow')
        self.base_url = 'https://api.stackexchange.com/2.3'
        self.rate_limit_delay = 0.1  # Stack Overflow has generous rate limits
        
        # Map topics to Stack Overflow tags
        self.topic_tags = {
            'ai': ['artificial-intelligence', 'machine-learning', 'deep-learning', 'neural-network'],
            'machine learning': ['machine-learning', 'scikit-learn', 'tensorflow', 'pytorch', 'keras'],
            'python': ['python', 'pandas', 'numpy', 'django', 'flask'],
            'javascript': ['javascript', 'node.js', 'react.js', 'vue.js', 'angular'],
            'web development': ['html', 'css', 'javascript', 'web-development', 'frontend'],
            'mobile': ['android', 'ios', 'react-native', 'flutter', 'swift'],
            'cloud': ['amazon-web-services', 'azure', 'google-cloud-platform', 'docker', 'kubernetes'],
            'blockchain': ['blockchain', 'cryptocurrency', 'ethereum', 'smart-contracts', 'web3'],
            'data science': ['data-science', 'pandas', 'numpy', 'matplotlib', 'jupyter-notebook'],
            'devops': ['docker', 'kubernetes', 'jenkins', 'ci-cd', 'terraform'],
            'security': ['security', 'cryptography', 'authentication', 'oauth', 'ssl']
        }
    
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch questions from Stack Overflow"""
        logger.info("Fetching from Stack Overflow", topic=topic)
        
        try:
            articles = []
            
            # Get relevant tags for the topic
            tags = self._get_tags_for_topic(topic)
            
            async with aiohttp.ClientSession() as session:
                for tag in tags[:3]:  # Limit to top 3 tags to avoid rate limits
                    tag_articles = await self._fetch_by_tag(session, tag, days_back)
                    articles.extend(tag_articles)
                    
                    await asyncio.sleep(self.rate_limit_delay)
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            # Sort by score and take top questions
            unique_articles.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info("Stack Overflow fetch complete", count=len(unique_articles))
            return unique_articles[:20]  # Limit to top 20 questions
            
        except Exception as e:
            logger.error("Stack Overflow fetch error", error=str(e))
            return []
    
    def _get_tags_for_topic(self, topic: str) -> List[str]:
        """Get Stack Overflow tags for a given topic"""
        topic_lower = topic.lower()
        
        # Direct match
        if topic_lower in self.topic_tags:
            return self.topic_tags[topic_lower]
        
        # Partial match
        for key, tags in self.topic_tags.items():
            if topic_lower in key or key in topic_lower:
                return tags
        
        # Fallback: use topic as tag (replace spaces with hyphens)
        return [topic_lower.replace(' ', '-')]
    
    async def _fetch_by_tag(self, session: aiohttp.ClientSession, tag: str, days_back: int) -> List[Dict[str, Any]]:
        """Fetch questions by tag"""
        articles = []
        
        try:
            # Calculate date range
            from_date = int((datetime.now() - timedelta(days=days_back)).timestamp())
            
            url = f"{self.base_url}/questions"
            params = {
                'order': 'desc',
                'sort': 'votes',
                'tagged': tag,
                'site': 'stackoverflow',
                'fromdate': from_date,
                'pagesize': 30,
                'filter': 'withbody'  # Include question body
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('items', []):
                        article = self._parse_question(item)
                        if article:
                            articles.append(article)
                else:
                    logger.warning("Stack Overflow API error", status=response.status, tag=tag)
                
        except Exception as e:
            logger.warning("Stack Overflow tag fetch error", tag=tag, error=str(e))
        
        return articles
    
    def _parse_question(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Stack Overflow question"""
        try:
            # Parse creation date
            creation_date = datetime.fromtimestamp(item.get('creation_date', 0))
            
            # Get owner info
            owner = item.get('owner', {})
            author = owner.get('display_name', 'Anonymous')
            
            # Clean body text
            body = item.get('body', '')
            if body:
                # Remove HTML tags
                import re
                body = re.sub(r'<[^>]+>', '', body)
                body = html.unescape(body)
                body = body.strip()[:400]  # Limit length
            
            # Extract tags
            tags = item.get('tags', [])
            
            return self._standardize_article({
                'title': html.unescape(item.get('title', '')),
                'content': body,
                'url': item.get('link', ''),
                'author': author,
                'published_at': creation_date,
                'score': item.get('score', 0),
                'comments_count': item.get('comment_count', 0),
                'tags': tags,
                'metadata': {
                    'question_id': item.get('question_id'),
                    'answer_count': item.get('answer_count', 0),
                    'view_count': item.get('view_count', 0),
                    'is_answered': item.get('is_answered', False),
                    'accepted_answer_id': item.get('accepted_answer_id'),
                    'owner_reputation': owner.get('reputation', 0)
                }
            })
            
        except Exception as e:
            logger.warning("Stack Overflow question parse error", error=str(e))
            return None