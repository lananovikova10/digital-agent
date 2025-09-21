"""
TechCrunch data source
"""
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog
import feedparser
import requests
from bs4 import BeautifulSoup

from .base import BaseSource

logger = structlog.get_logger()


class TechCrunchSource(BaseSource):
    """TechCrunch RSS feed integration"""
    
    def __init__(self):
        super().__init__("techcrunch")
        self.rss_url = "https://techcrunch.com/feed/"
    
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch articles from TechCrunch RSS feed"""
        logger.info("Fetching from TechCrunch", topic=topic)
        
        articles = []
        
        try:
            # Fetch RSS feed
            feed = feedparser.parse(self.rss_url)
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for entry in feed.entries:
                # Parse publication date
                published_at = datetime(*entry.published_parsed[:6])
                
                # Skip old articles
                if published_at < cutoff_date:
                    continue
                
                # Check if article is relevant to topic
                if not self._is_relevant(entry, topic):
                    continue
                
                article = self._parse_entry(entry)
                if article:
                    articles.append(self._standardize_article(article))
        
        except Exception as e:
            logger.error("TechCrunch RSS error", error=str(e))
            return []
        
        logger.info("TechCrunch fetch complete", count=len(articles))
        return articles
    
    def _is_relevant(self, entry, topic: str) -> bool:
        """Check if article is relevant to the topic"""
        topic_lower = topic.lower()
        title_lower = entry.title.lower()
        summary_lower = getattr(entry, 'summary', '').lower()
        
        return (topic_lower in title_lower or 
                topic_lower in summary_lower or
                any(tag.term.lower() == topic_lower for tag in getattr(entry, 'tags', [])))
    
    def _parse_entry(self, entry) -> Dict[str, Any]:
        """Parse RSS entry data"""
        # Extract author from entry
        author = "TechCrunch"
        if hasattr(entry, 'author'):
            author = entry.author
        elif hasattr(entry, 'authors') and entry.authors:
            author = entry.authors[0].get('name', 'TechCrunch')
        
        # Clean up summary/content
        content = getattr(entry, 'summary', '')
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value
        
        # Remove HTML tags from content
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.get_text().strip()
        
        # Extract tags
        tags = []
        if hasattr(entry, 'tags'):
            tags = [tag.term for tag in entry.tags]
        
        return {
            'title': entry.title,
            'content': content,
            'url': entry.link,
            'author': author,
            'published_at': datetime(*entry.published_parsed[:6]),
            'score': 100,  # Default score for TechCrunch articles
            'comments_count': 0,  # RSS doesn't provide comment count
            'tags': tags,
            'metadata': {
                'source_url': entry.link,
                'guid': getattr(entry, 'id', entry.link)
            }
        }