"""
RSS Feeds source for fetching from OpenAI, Anthropic, GitHub and other tech company blogs
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


class RSSFeedsSource(BaseSource):
    """Fetches articles from RSS feeds of tech companies and blogs"""
    
    def __init__(self):
        super().__init__('rss_feeds')
        self.rate_limit_delay = 2.0
        
        # Tech company and organization RSS feeds
        self.feeds = {
            # AI Companies
            'openai': 'https://openai.com/blog/rss.xml',
            'anthropic': 'https://www.anthropic.com/news/rss.xml',
            'deepmind': 'https://deepmind.google/discover/blog/rss.xml',
            'meta-ai': 'https://ai.meta.com/blog/rss/',
            
            # Tech Companies
            'github': 'https://github.blog/feed/',
            'google-ai': 'https://blog.google/technology/ai/rss/',
            'microsoft-ai': 'https://blogs.microsoft.com/ai/feed/',
            'nvidia': 'https://blogs.nvidia.com/feed/',
            'aws-machine-learning': 'https://aws.amazon.com/blogs/machine-learning/feed/',
            
            # Research Organizations
            'mit-csail': 'https://www.csail.mit.edu/news/rss.xml',
            'stanford-ai': 'https://hai.stanford.edu/news/rss.xml',
            'berkeley-ai': 'https://bair.berkeley.edu/blog/feed.xml',
            
            # Tech News & Analysis
            'techcrunch-ai': 'https://techcrunch.com/category/artificial-intelligence/feed/',
            'venturebeat-ai': 'https://venturebeat.com/ai/feed/',
            'the-verge-ai': 'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml',
            'wired-ai': 'https://www.wired.com/feed/tag/ai/latest/rss',
            
            # Developer Focused
            'github-changelog': 'https://github.blog/changelog/feed/',
            'stackoverflow-blog': 'https://stackoverflow.blog/feed/',
            'dev-community': 'https://dev.to/feed',
            'hashnode': 'https://hashnode.com/rss',
            
            # Startups & Funding
            'crunchbase-news': 'https://news.crunchbase.com/feed/',
            'techstars': 'https://www.techstars.com/blog/feed',
            'y-combinator': 'https://blog.ycombinator.com/feed',
            
            # Industry Analysis
            'a16z': 'https://a16z.com/feed/',
            'sequoia-capital': 'https://medium.com/feed/sequoia-capital',
            'first-round': 'https://review.firstround.com/rss',
            
            # Open Source
            'apache-foundation': 'https://blogs.apache.org/foundation/feed/entries/atom',
            'linux-foundation': 'https://www.linuxfoundation.org/feed',
            'cncf': 'https://www.cncf.io/feed/',
            
            # Security
            'owasp': 'https://owasp.org/blog/feed.xml',
            'sans': 'https://www.sans.org/blog/rss/',
            
            # Cloud Providers
            'aws-news': 'https://aws.amazon.com/about-aws/whats-new/recent/feed/',
            'azure-updates': 'https://azure.microsoft.com/en-us/updates/feed/',
            'gcp-blog': 'https://cloud.google.com/blog/rss/',
        }
    
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch articles from RSS feeds"""
        logger.info("Fetching from RSS feeds", topic=topic)
        
        try:
            articles = []
            
            # Select relevant feeds based on topic
            relevant_feeds = self._get_relevant_feeds(topic)
            
            async with aiohttp.ClientSession() as session:
                tasks = []
                for feed_name, rss_url in relevant_feeds.items():
                    task = self._fetch_feed(session, feed_name, rss_url, topic, days_back)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        articles.extend(result)
                    elif isinstance(result, Exception):
                        logger.warning("RSS feed fetch error", error=str(result))
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            # Sort by published date
            unique_articles.sort(key=lambda x: x['published_at'], reverse=True)
            
            logger.info("RSS feeds fetch complete", count=len(unique_articles))
            return unique_articles[:25]  # Limit to top 25 articles
            
        except Exception as e:
            logger.error("RSS feeds fetch error", error=str(e))
            return []
    
    def _get_relevant_feeds(self, topic: str) -> Dict[str, str]:
        """Get relevant feeds based on topic"""
        topic_lower = topic.lower()
        relevant_feeds = {}
        
        # Always include major AI companies
        ai_feeds = ['openai', 'anthropic', 'deepmind', 'meta-ai', 'github']
        for feed_name in ai_feeds:
            if feed_name in self.feeds:
                relevant_feeds[feed_name] = self.feeds[feed_name]
        
        # Add topic-specific feeds
        if any(term in topic_lower for term in ['ai', 'artificial intelligence', 'machine learning', 'ml']):
            ai_specific = ['google-ai', 'microsoft-ai', 'nvidia', 'aws-machine-learning', 
                          'stanford-ai', 'berkeley-ai', 'techcrunch-ai', 'venturebeat-ai']
            for feed_name in ai_specific:
                if feed_name in self.feeds:
                    relevant_feeds[feed_name] = self.feeds[feed_name]
        
        if any(term in topic_lower for term in ['startup', 'funding', 'venture']):
            startup_feeds = ['crunchbase-news', 'techstars', 'y-combinator', 'a16z', 'sequoia-capital']
            for feed_name in startup_feeds:
                if feed_name in self.feeds:
                    relevant_feeds[feed_name] = self.feeds[feed_name]
        
        if any(term in topic_lower for term in ['cloud', 'aws', 'azure', 'gcp']):
            cloud_feeds = ['aws-news', 'azure-updates', 'gcp-blog', 'aws-machine-learning']
            for feed_name in cloud_feeds:
                if feed_name in self.feeds:
                    relevant_feeds[feed_name] = self.feeds[feed_name]
        
        if any(term in topic_lower for term in ['security', 'crypto', 'privacy']):
            security_feeds = ['owasp', 'sans']
            for feed_name in security_feeds:
                if feed_name in self.feeds:
                    relevant_feeds[feed_name] = self.feeds[feed_name]
        
        if any(term in topic_lower for term in ['open source', 'linux', 'apache']):
            oss_feeds = ['apache-foundation', 'linux-foundation', 'cncf']
            for feed_name in oss_feeds:
                if feed_name in self.feeds:
                    relevant_feeds[feed_name] = self.feeds[feed_name]
        
        # If no specific matches, return a broader set
        if len(relevant_feeds) < 5:
            general_feeds = ['github', 'stackoverflow-blog', 'dev-community', 'techcrunch-ai', 'the-verge-ai']
            for feed_name in general_feeds:
                if feed_name in self.feeds and feed_name not in relevant_feeds:
                    relevant_feeds[feed_name] = self.feeds[feed_name]
        
        return relevant_feeds
    
    async def _fetch_feed(self, session: aiohttp.ClientSession, feed_name: str, rss_url: str, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Fetch articles from a specific RSS feed"""
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
                            topic_lower in content or
                            self._is_always_relevant_feed(feed_name)):  # Some feeds are always relevant
                            
                            article = self._parse_entry(entry, feed_name)
                            if article and self._is_recent(article['published_at'], days_back):
                                articles.append(article)
                
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.warning("RSS feed fetch error", feed=feed_name, error=str(e))
        
        return articles
    
    def _is_always_relevant_feed(self, feed_name: str) -> bool:
        """Check if feed is always relevant (e.g., OpenAI, Anthropic)"""
        always_relevant = ['openai', 'anthropic', 'deepmind', 'meta-ai', 'github']
        return feed_name in always_relevant
    
    def _parse_entry(self, entry: Dict[str, Any], feed_name: str) -> Dict[str, Any]:
        """Parse RSS entry"""
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
            else:
                author = feed_name.replace('-', ' ').title()
            
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
                content = content.strip()[:700]  # Longer excerpts for company blogs
            
            # Extract tags/categories
            tags = []
            if hasattr(entry, 'tags'):
                tags = [tag.get('term', '') for tag in entry.tags if tag.get('term')]
            
            # Add feed-specific tags
            tags.append(feed_name.replace('-', ' '))
            if 'ai' in feed_name or 'anthropic' in feed_name or 'openai' in feed_name:
                tags.append('AI')
            
            return self._standardize_article({
                'title': entry.get('title', ''),
                'content': content,
                'url': entry.get('link', ''),
                'author': author,
                'published_at': published_at,
                'score': 0,  # RSS doesn't provide engagement metrics
                'comments_count': 0,
                'tags': tags,
                'metadata': {
                    'feed_name': feed_name,
                    'guid': entry.get('id', ''),
                    'rss_url': entry.get('link', ''),
                    'is_company_blog': True
                }
            })
            
        except Exception as e:
            logger.warning("RSS entry parse error", error=str(e))
            return None