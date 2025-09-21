"""
Y Combinator launches data source
"""
import httpx
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog
from bs4 import BeautifulSoup

from .base import BaseSource

logger = structlog.get_logger()


class YCLaunchesSource(BaseSource):
    """Y Combinator launches scraper"""
    
    def __init__(self):
        super().__init__("yc_launches")
        self.base_url = "https://www.ycombinator.com"
        self.launches_url = f"{self.base_url}/launches"
    
    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch YC launches matching the topic"""
        logger.info("Fetching from YC Launches", topic=topic)
        
        articles = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Fetch launches page
                response = await client.get(self.launches_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                launch_items = soup.find_all('div', class_='launch-item')
                
                cutoff_date = datetime.now() - timedelta(days=days_back)
                
                for item in launch_items:
                    launch_data = self._parse_launch_item(item)
                    if (launch_data and 
                        launch_data['published_at'] >= cutoff_date and
                        self._is_relevant_to_topic(launch_data, topic)):
                        
                        articles.append(self._standardize_article(launch_data))
        
        except Exception as e:
            logger.error("YC Launches scraping error", error=str(e))
            return []
        
        logger.info("YC Launches fetch complete", count=len(articles))
        return articles
    
    def _parse_launch_item(self, item) -> Dict[str, Any]:
        """Parse a launch item from the HTML"""
        try:
            # Extract title
            title_elem = item.find('h3') or item.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Extract description
            desc_elem = item.find('p', class_='description') or item.find('div', class_='description')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Extract URL
            link_elem = item.find('a')
            url = link_elem.get('href', '') if link_elem else ''
            if url and not url.startswith('http'):
                url = f"{self.base_url}{url}"
            
            # Extract company name (usually in the title or a separate element)
            company_elem = item.find('span', class_='company-name')
            company = company_elem.get_text(strip=True) if company_elem else ''
            
            # Extract tags/categories
            tags = []
            tag_elems = item.find_all('span', class_='tag') or item.find_all('div', class_='category')
            for tag_elem in tag_elems:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
            
            # Extract date (this might need adjustment based on actual HTML structure)
            date_elem = item.find('time') or item.find('span', class_='date')
            if date_elem:
                date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                try:
                    published_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    published_at = datetime.now()  # Fallback to current time
            else:
                published_at = datetime.now()
            
            return {
                'title': title,
                'content': description,
                'url': url,
                'author': company,
                'published_at': published_at,
                'score': 0,  # YC doesn't have public scores
                'comments_count': 0,
                'tags': tags,
                'metadata': {
                    'company': company,
                    'source_type': 'yc_launch'
                }
            }
        
        except Exception as e:
            logger.error("Error parsing YC launch item", error=str(e))
            return None
    
    def _is_relevant_to_topic(self, launch_data: Dict[str, Any], topic: str) -> bool:
        """Check if launch is relevant to the topic"""
        topic_lower = topic.lower()
        
        # Check title and description
        text_to_check = [
            launch_data.get('title', ''),
            launch_data.get('content', '')
        ]
        
        for text in text_to_check:
            if topic_lower in text.lower():
                return True
        
        # Check tags
        for tag in launch_data.get('tags', []):
            if topic_lower in tag.lower():
                return True
        
        return False