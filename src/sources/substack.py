"""
Substack source for fetching articles from popular tech newsletters
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


class SubstackSource(BaseSource):
    """Fetches articles from Substack newsletters via RSS"""
    
    def __init__(self):
        super().__init__('substack')
        self.rate_limit_delay = 2.0
        
        # Popular tech Substack newsletters
        self.newsletters = {
            'stratechery': 'https://stratechery.com/feed/',
            'platformer': 'https://www.platformer.news/feed',
            'the-diff': 'https://diff.substack.com/feed',
            'net-interest': 'https://netinterest.substack.com/feed',
            'imported': 'https://imported.substack.com/feed',
            'pragmatic-engineer': 'https://newsletter.pragmaticengineer.com/feed',
            'lenny-newsletter': 'https://www.lennysnewsletter.com/feed',
            'ai-supremacy': 'https://aisupremacy.substack.com/feed',
            'the-neuron': 'https://www.theneurondaily.com/feed',
            'ben-evans': 'https://www.ben-evans.com/feed',
            'casey-newton': 'https://www.platformer.news/feed',
            'alex-kantrowitz': 'https://bigtech.substack.com/feed',
            'turner-novak': 'https://turnernovak.substack.com/feed',
            'not-boring': 'https://www.notboring.co/feed',
            'every': 'https://every.to/feed'
        }
    
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch articles from Substack newsletters"""
        logger.info("Fetching from Substack", topic=topic)
        
        try:
            articles = []
            
            async with aiohttp.ClientSession() as session:
                tasks = []
                for newsletter_name, rss_url in self.newsletters.items():
                    task = self._fetch_newsletter(session, newsletter_name, rss_url, topic, days_back)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        articles.extend(result)
                    elif isinstance(result, Exception):
                        logger.warning("Substack newsletter fetch error", error=str(result))
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            logger.info("Substack fetch complete", count=len(unique_articles))
            return unique_articles
            
        except Exception as e:
            logger.error("Substack fetch error", error=str(e))
            return []
    
    async def _fetch_newsletter(self, session: aiohttp.ClientSession, newsletter_name: str, rss_url: str, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Fetch articles from a specific Substack newsletter"""
        articles = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; WeeklyIntelAgent/1.0)'
            }
            
            async with session.get(rss_url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    topic_lower = topic.lower()
                    for entry in feed.entries:
                        # Check if article is relevant to topic
                        title = entry.get('title', '').lower()
                        summary = entry.get('summary', '').lower()
                        content = entry.get('content', [{}])[0].get('value', '').lower() if entry.get('content') else ''
                        
                        if (topic_lower in title or 
                            topic_lower in summary or
                            topic_lower in content):
                            
                            article = self._parse_entry(entry, newsletter_name)
                            if article and self._is_recent(article['published_at'], days_back):
                                articles.append(article)
                
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.warning("Substack newsletter fetch error", newsletter=newsletter_name, error=str(e))
        
        return articles
    
    def _parse_entry(self, entry: Dict[str, Any], newsletter: str) -> Dict[str, Any]:
        """Parse Substack RSS entry"""
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
            
            # Get content - prefer full content over summary
            content = ''
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].get('value', '')
            else:
                content = entry.get('summary', '')
            
            # Clean content
            if content:
                # Remove HTML tags
                content = re.sub(r'<[^>]+>', '', content)
                content = content.strip()[:800]  # Longer excerpts for newsletters
            
            # Extract tags/categories
            tags = []
            if hasattr(entry, 'tags'):
                tags = [tag.get('term', '') for tag in entry.tags if tag.get('term')]
            
            return self._standardize_article({
                'title': entry.get('title', ''),
                'content': content,
                'url': entry.get('link', ''),
                'author': author,
                'published_at': published_at,
                'score': 0,  # Substack doesn't provide engagement metrics via RSS
                'comments_count': 0,
                'tags': tags,
                'metadata': {
                    'newsletter': newsletter,
                    'guid': entry.get('id', ''),
                    'substack_url': entry.get('link', ''),
                    'is_newsletter': True
                }
            })
            
        except Exception as e:
            logger.warning("Substack entry parse error", error=str(e))
            return None