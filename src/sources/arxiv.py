"""
arXiv source for fetching research papers
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


class ArxivSource(BaseSource):
    """Fetches research papers from arXiv"""
    
    def __init__(self):
        super().__init__('arxiv')
        self.base_url = 'http://export.arxiv.org/api/query'
        self.rate_limit_delay = 3.0  # arXiv requests 3 second delays
        
        # Map topics to arXiv categories
        self.topic_categories = {
            'ai': ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV', 'cs.NE'],
            'machine learning': ['cs.LG', 'stat.ML', 'cs.AI'],
            'computer vision': ['cs.CV', 'eess.IV'],
            'natural language processing': ['cs.CL', 'cs.AI'],
            'robotics': ['cs.RO', 'cs.AI'],
            'computer science': ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV', 'cs.DS', 'cs.CR'],
            'deep learning': ['cs.LG', 'cs.AI', 'cs.NE'],
            'neural networks': ['cs.NE', 'cs.LG', 'cs.AI'],
            'statistics': ['stat.ML', 'stat.ME', 'math.ST'],
            'mathematics': ['math.ST', 'math.OC', 'math.PR'],
            'physics': ['physics.data-an', 'physics.comp-ph'],
            'quantum': ['quant-ph', 'cs.ET'],
            'cryptography': ['cs.CR', 'cs.IT'],
            'algorithms': ['cs.DS', 'cs.CC', 'cs.DM'],
            'software engineering': ['cs.SE', 'cs.PL'],
            'human computer interaction': ['cs.HC', 'cs.AI'],
            'information retrieval': ['cs.IR', 'cs.CL'],
            'databases': ['cs.DB', 'cs.IR']
        }
    
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch papers from arXiv"""
        logger.info("Fetching from arXiv", topic=topic)
        
        try:
            articles = []
            
            # Get relevant categories for the topic
            categories = self._get_categories_for_topic(topic)
            
            async with aiohttp.ClientSession() as session:
                # Search by categories
                for category in categories[:3]:  # Limit to avoid rate limits
                    category_articles = await self._fetch_by_category(session, category, topic, days_back)
                    articles.extend(category_articles)
                    
                    await asyncio.sleep(self.rate_limit_delay)
                
                # Also search by keywords
                keyword_articles = await self._fetch_by_keywords(session, topic, days_back)
                articles.extend(keyword_articles)
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            # Sort by published date (most recent first)
            unique_articles.sort(key=lambda x: x['published_at'], reverse=True)
            
            logger.info("arXiv fetch complete", count=len(unique_articles))
            return unique_articles[:15]  # Limit to top 15 papers
            
        except Exception as e:
            logger.error("arXiv fetch error", error=str(e))
            return []
    
    def _get_categories_for_topic(self, topic: str) -> List[str]:
        """Get arXiv categories for a given topic"""
        topic_lower = topic.lower()
        
        # Direct match
        if topic_lower in self.topic_categories:
            return self.topic_categories[topic_lower]
        
        # Partial match
        for key, categories in self.topic_categories.items():
            if topic_lower in key or key in topic_lower:
                return categories
        
        # Default to AI/ML categories
        return ['cs.AI', 'cs.LG']
    
    async def _fetch_by_category(self, session: aiohttp.ClientSession, category: str, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Fetch papers by arXiv category"""
        articles = []
        
        try:
            params = {
                'search_query': f'cat:{category}',
                'start': 0,
                'max_results': 20,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    for entry in feed.entries:
                        article = self._parse_entry(entry)
                        if (article and 
                            self._is_recent(article['published_at'], days_back) and
                            self._is_relevant_to_topic(article, topic)):
                            articles.append(article)
                
        except Exception as e:
            logger.warning("arXiv category fetch error", category=category, error=str(e))
        
        return articles
    
    async def _fetch_by_keywords(self, session: aiohttp.ClientSession, topic: str, days_back: int) -> List[Dict[str, Any]]:
        """Fetch papers by keyword search"""
        articles = []
        
        try:
            # Create search query
            search_terms = topic.replace(' ', '+AND+')
            params = {
                'search_query': f'all:{search_terms}',
                'start': 0,
                'max_results': 15,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    for entry in feed.entries:
                        article = self._parse_entry(entry)
                        if article and self._is_recent(article['published_at'], days_back):
                            articles.append(article)
                
        except Exception as e:
            logger.warning("arXiv keyword search error", topic=topic, error=str(e))
        
        return articles
    
    def _parse_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Parse arXiv entry"""
        try:
            # Parse published date
            published_at = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6])
            
            # Extract authors
            authors = []
            if hasattr(entry, 'authors'):
                authors = [author.get('name', '') for author in entry.authors]
            author = ', '.join(authors[:3])  # Limit to first 3 authors
            if len(authors) > 3:
                author += ' et al.'
            
            # Get abstract
            summary = entry.get('summary', '')
            if summary:
                # Clean up abstract formatting
                summary = re.sub(r'\s+', ' ', summary).strip()
                summary = summary[:600]  # Limit length
            
            # Extract arXiv ID and create PDF URL
            arxiv_id = entry.get('id', '').split('/')[-1]
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            # Extract categories
            categories = []
            if hasattr(entry, 'tags'):
                categories = [tag.get('term', '') for tag in entry.tags]
            
            return self._standardize_article({
                'title': entry.get('title', ''),
                'content': summary,
                'url': entry.get('link', ''),
                'author': author,
                'published_at': published_at,
                'score': 0,  # arXiv doesn't have scoring
                'comments_count': 0,
                'tags': categories,
                'metadata': {
                    'arxiv_id': arxiv_id,
                    'pdf_url': pdf_url,
                    'categories': categories,
                    'authors': authors,
                    'is_preprint': True,
                    'journal_ref': entry.get('arxiv_journal_ref', ''),
                    'doi': entry.get('arxiv_doi', '')
                }
            })
            
        except Exception as e:
            logger.warning("arXiv entry parse error", error=str(e))
            return None
    
    def _is_relevant_to_topic(self, article: Dict[str, Any], topic: str) -> bool:
        """Check if article is relevant to the topic"""
        topic_lower = topic.lower()
        
        # Check title
        title = article.get('title', '').lower()
        if topic_lower in title:
            return True
        
        # Check abstract/content
        content = article.get('content', '').lower()
        if topic_lower in content:
            return True
        
        # Check categories
        categories = article.get('tags', [])
        topic_categories = self._get_categories_for_topic(topic)
        if any(cat in categories for cat in topic_categories):
            return True
        
        return False