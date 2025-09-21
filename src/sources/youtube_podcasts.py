"""
YouTube/Podcast source for fetching episodes from tech channels and podcasts
"""
import asyncio
import aiohttp
import feedparser
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog
import re
import os

from .base import BaseSource

logger = structlog.get_logger()


class YouTubePodcastSource(BaseSource):
    """Fetches episodes from YouTube channels and podcast RSS feeds"""
    
    def __init__(self):
        super().__init__('youtube_podcasts')
        self.rate_limit_delay = 2.0
        
        # Popular tech YouTube channels and podcasts
        self.channels = {
            # YouTube Channels (RSS feeds)
            'latent-space': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCS6N-uYGVs3_2Zt9Yl_bTAg',
            'two-minute-papers': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg',
            'lex-fridman': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCSHZKyawb77ixDdsGog4iWA',
            'yannic-kilcher': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCZHmQk67mSJgfCCTn7xBfew',
            'ai-explained': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCNJ1Ymd5yFuUPtn21xtRbbw',
            'machine-learning-street-talk': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCMLtBahI5DMrt0NPvDSoIRQ',
            
            # Podcast RSS feeds
            'practical-ai': 'https://changelog.com/practicalai/feed',
            'twiml': 'https://twimlai.com/feed/podcast/',
            'the-ai-podcast': 'https://feeds.soundcloud.com/users/soundcloud:users:264034133/sounds.rss',
            'gradient-dissent': 'https://feeds.buzzsprout.com/1926876.rss',
            'chai-time-data-science': 'https://anchor.fm/s/6e3c5d4/podcast/rss',
            'data-skeptic': 'https://dataskeptic.com/feed.rss',
            'linear-digressions': 'http://lineardigressions.com/feed.rss',
            'talking-machines': 'https://www.thetalkingmachines.com/episodes?format=RSS',
            'this-week-in-machine-learning': 'https://twimlai.com/feed/podcast/',
            'the-robot-brains-podcast': 'https://www.therobotbrains.ai/feed.xml'
        }
    
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch episodes from YouTube channels and podcasts"""
        logger.info("Fetching from YouTube/Podcasts", topic=topic)
        
        try:
            articles = []
            
            async with aiohttp.ClientSession() as session:
                tasks = []
                for channel_name, rss_url in self.channels.items():
                    task = self._fetch_channel(session, channel_name, rss_url, topic, days_back)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        articles.extend(result)
                    elif isinstance(result, Exception):
                        logger.warning("YouTube/Podcast channel fetch error", error=str(result))
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            logger.info("YouTube/Podcasts fetch complete", count=len(unique_articles))
            return unique_articles
            
        except Exception as e:
            logger.error("YouTube/Podcasts fetch error", error=str(e))
            return []
    
    async def _fetch_channel(self, session: aiohttp.ClientSession, channel_name: str, rss_url: str, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Fetch episodes from a specific channel or podcast"""
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
                        # Check if episode is relevant to topic
                        title = entry.get('title', '').lower()
                        summary = entry.get('summary', '').lower()
                        description = entry.get('description', '').lower()
                        
                        if (topic_lower in title or 
                            topic_lower in summary or
                            topic_lower in description):
                            
                            article = self._parse_entry(entry, channel_name)
                            if article and self._is_recent(article['published_at'], days_back):
                                articles.append(article)
                
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.warning("Channel fetch error", channel=channel_name, error=str(e))
        
        return articles
    
    def _parse_entry(self, entry: Dict[str, Any], channel: str) -> Dict[str, Any]:
        """Parse YouTube/Podcast RSS entry"""
        try:
            # Parse published date
            published_at = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_at = datetime(*entry.updated_parsed[:6])
            
            # Extract author/channel
            author = ''
            if hasattr(entry, 'author'):
                author = entry.author
            elif hasattr(entry, 'authors') and entry.authors:
                author = entry.authors[0].get('name', '')
            else:
                author = channel.replace('-', ' ').title()
            
            # Get description/summary
            content = ''
            if hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            
            # Clean content
            if content:
                # Remove HTML tags
                content = re.sub(r'<[^>]+>', '', content)
                content = content.strip()[:600]  # Longer excerpts for video/podcast content
            
            # Extract duration if available
            duration = ''
            if hasattr(entry, 'itunes_duration'):
                duration = entry.itunes_duration
            
            # Determine content type
            is_youtube = 'youtube.com' in entry.get('link', '')
            content_type = 'video' if is_youtube else 'podcast'
            
            return self._standardize_article({
                'title': entry.get('title', ''),
                'content': content,
                'url': entry.get('link', ''),
                'author': author,
                'published_at': published_at,
                'score': 0,  # RSS doesn't provide view/like counts
                'comments_count': 0,
                'tags': [content_type, 'tech', channel.replace('-', ' ')],
                'metadata': {
                    'channel': channel,
                    'content_type': content_type,
                    'duration': duration,
                    'guid': entry.get('id', ''),
                    'is_video': is_youtube,
                    'is_podcast': not is_youtube
                }
            })
            
        except Exception as e:
            logger.warning("Episode parse error", error=str(e))
            return None