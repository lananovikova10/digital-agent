"""
Base class for all data sources
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timedelta


class BaseSource(ABC):
    """Abstract base class for all data sources"""
    
    def __init__(self, name: str):
        self.name = name
        self.rate_limit_delay = 1.0  # seconds between requests
    
    @abstractmethod
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch articles for a given topic from the past N days
        
        Returns:
            List of articles with standardized format:
            {
                'title': str,
                'content': str,
                'url': str,
                'author': str,
                'published_at': datetime,
                'source': str,
                'score': int,
                'comments_count': int,
                'tags': List[str],
                'metadata': Dict[str, Any]
            }
        """
        pass
    
    def _standardize_article(self, raw_article: Dict[str, Any]) -> Dict[str, Any]:
        """Convert source-specific article format to standardized format"""
        return {
            'title': raw_article.get('title', ''),
            'content': raw_article.get('content', ''),
            'url': raw_article.get('url', ''),
            'author': raw_article.get('author', ''),
            'published_at': raw_article.get('published_at', datetime.now()),
            'source': self.name,
            'score': raw_article.get('score', 0),
            'comments_count': raw_article.get('comments_count', 0),
            'tags': raw_article.get('tags', []),
            'metadata': raw_article.get('metadata', {})
        }
    
    def _is_recent(self, published_at: datetime, days_back: int) -> bool:
        """Check if article is within the specified time range"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        return published_at >= cutoff_date