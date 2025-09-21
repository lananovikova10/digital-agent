"""
Reddit data source
"""
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog
import praw

from .base import BaseSource

logger = structlog.get_logger()


class RedditSource(BaseSource):
    """Reddit API integration"""
    
    def __init__(self):
        super().__init__("reddit")
        self.reddit = None
        
        # Relevant subreddits for different topics
        self.subreddit_mapping = {
            'AI': ['MachineLearning', 'artificial', 'singularity', 'OpenAI'],
            'startup': ['startups', 'entrepreneur', 'smallbusiness'],
            'fintech': ['fintech', 'CryptoCurrency', 'investing'],
            'tech': ['technology', 'programming', 'coding'],
            'Model context protocol': ['mcp']

        }
    
    def _init_reddit(self):
        """Initialize Reddit client lazily"""
        if self.reddit is None:
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                logger.warning("Reddit API credentials not found")
                return False
            
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=os.getenv('REDDIT_USER_AGENT', 'WeeklyIntelAgent/1.0')
            )
        return True

    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch Reddit posts matching the topic"""
        if not self._init_reddit():
            logger.warning("Reddit client not initialized, skipping")
            return []
            
        logger.info("Fetching from Reddit", topic=topic)
        
        subreddits = self._get_subreddits_for_topic(topic)
        articles = []
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get hot posts
                for submission in subreddit.hot(limit=25):
                    if datetime.fromtimestamp(submission.created_utc) >= cutoff_date:
                        article = self._parse_reddit_post(submission)
                        if self._is_relevant_to_topic(article, topic):
                            articles.append(self._standardize_article(article))
                
                # Get top posts from the week
                for submission in subreddit.top(time_filter='week', limit=25):
                    if datetime.fromtimestamp(submission.created_utc) >= cutoff_date:
                        article = self._parse_reddit_post(submission)
                        if self._is_relevant_to_topic(article, topic):
                            articles.append(self._standardize_article(article))
                            
            except Exception as e:
                logger.error("Reddit subreddit error", subreddit=subreddit_name, error=str(e))
                continue
        
        # Remove duplicates
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        logger.info("Reddit fetch complete", count=len(unique_articles))
        return unique_articles
    
    def _get_subreddits_for_topic(self, topic: str) -> List[str]:
        """Get relevant subreddits for a topic"""
        topic_lower = topic.lower()
        
        # Direct mapping
        for key, subreddits in self.subreddit_mapping.items():
            if key.lower() in topic_lower:
                return subreddits
        
        # Default subreddits for general topics
        return ['technology', 'news', 'worldnews']
    
    def _parse_reddit_post(self, submission) -> Dict[str, Any]:
        """Parse Reddit submission"""
        return {
            'title': submission.title,
            'content': submission.selftext,
            'url': submission.url,
            'author': str(submission.author) if submission.author else 'deleted',
            'published_at': datetime.fromtimestamp(submission.created_utc),
            'score': submission.score,
            'comments_count': submission.num_comments,
            'tags': [submission.subreddit.display_name],
            'metadata': {
                'reddit_id': submission.id,
                'subreddit': submission.subreddit.display_name,
                'upvote_ratio': submission.upvote_ratio,
                'is_self': submission.is_self
            }
        }
    
    def _is_relevant_to_topic(self, article: Dict[str, Any], topic: str) -> bool:
        """Check if article is relevant to the topic"""
        topic_lower = topic.lower()
        title_lower = article['title'].lower()
        content_lower = article['content'].lower()
        
        return (topic_lower in title_lower or 
                topic_lower in content_lower or
                any(topic_lower in tag.lower() for tag in article['tags']))