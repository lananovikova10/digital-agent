"""
Source Manager - Orchestrates data collection from all sources
"""
import asyncio
from typing import List, Dict, Any
import structlog

from .hackernews import HackerNewsSource
from .reddit import RedditSource
from .twitter import TwitterSource
from .producthunt import ProductHuntSource
from .yc_launches import YCLaunchesSource
from .techcrunch import TechCrunchSource

logger = structlog.get_logger()


class SourceManager:
    """Manages all data sources and coordinates fetching"""
    
    def __init__(self):
        self.sources = {
            'hackernews': HackerNewsSource(),
            'reddit': RedditSource(),
            'twitter': TwitterSource(),
            'producthunt': ProductHuntSource(),
            'yc_launches': YCLaunchesSource(),
            'techcrunch': TechCrunchSource()
        }
    
    async def fetch_all_sources(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch articles from all sources concurrently"""
        logger.info("Fetching from all sources", topic=topic, days_back=days_back)
        
        tasks = []
        for source_name, source in self.sources.items():
            task = self._fetch_with_error_handling(source, topic, days_back)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for i, result in enumerate(results):
            source_name = list(self.sources.keys())[i]
            
            if isinstance(result, Exception):
                logger.error("Source fetch failed", 
                           source=source_name, 
                           error=str(result))
                continue
            
            articles = result or []
            all_articles.extend(articles)
            logger.info("Source fetch complete", 
                       source=source_name, 
                       count=len(articles))
        
        logger.info("All sources fetched", total_articles=len(all_articles))
        return all_articles
    
    async def _fetch_with_error_handling(self, source, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Fetch from a single source with error handling"""
        try:
            return await source.fetch_articles(topic, days_back)
        except Exception as e:
            logger.error("Source error", source=source.name, error=str(e))
            return []
    
    async def fetch_source(self, source_name: str, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch from a specific source"""
        if source_name not in self.sources:
            raise ValueError(f"Unknown source: {source_name}")
        
        source = self.sources[source_name]
        return await self._fetch_with_error_handling(source, topic, days_back)
    
    def get_available_sources(self) -> List[str]:
        """Get list of available source names"""
        return list(self.sources.keys())