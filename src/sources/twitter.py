"""
Twitter/X data source
"""
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog
import tweepy

from .base import BaseSource

logger = structlog.get_logger()


class TwitterSource(BaseSource):
    """Twitter/X API integration"""
    
    def __init__(self):
        super().__init__("twitter")
        self.client = None
    
    def _init_twitter(self):
        """Initialize Twitter client lazily"""
        if self.client is None:
            bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            if not bearer_token:
                logger.warning("Twitter bearer token not found")
                return False
            
            self.client = tweepy.Client(bearer_token=bearer_token)
        return True

    async def fetch_articles(self, topic: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch tweets matching the topic"""
        if not self._init_twitter():
            logger.warning("Twitter client not initialized, skipping")
            return []
        
        logger.info("Fetching from Twitter", topic=topic)
        
        articles = []
        
        try:
            # Search for recent tweets
            query = f"{topic} -is:retweet lang:en"
            start_time = datetime.now() - timedelta(days=days_back)
            
            tweets = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                start_time=start_time,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations'],
                user_fields=['username', 'name', 'verified'],
                expansions=['author_id'],
                max_results=100
            ).flatten(limit=500)
            
            for tweet in tweets:
                article = self._parse_tweet(tweet)
                if article:
                    articles.append(self._standardize_article(article))
        
        except Exception as e:
            logger.error("Twitter API error", error=str(e))
            return []
        
        logger.info("Twitter fetch complete", count=len(articles))
        return articles
    
    def _parse_tweet(self, tweet) -> Dict[str, Any]:
        """Parse tweet data"""
        metrics = tweet.public_metrics or {}
        
        return {
            'title': tweet.text[:100] + "..." if len(tweet.text) > 100 else tweet.text,
            'content': tweet.text,
            'url': f"https://twitter.com/i/status/{tweet.id}",
            'author': getattr(tweet.author, 'username', 'unknown') if hasattr(tweet, 'author') else 'unknown',
            'published_at': tweet.created_at,
            'score': metrics.get('like_count', 0) + metrics.get('retweet_count', 0),
            'comments_count': metrics.get('reply_count', 0),
            'tags': self._extract_hashtags(tweet.text),
            'metadata': {
                'tweet_id': tweet.id,
                'retweet_count': metrics.get('retweet_count', 0),
                'like_count': metrics.get('like_count', 0),
                'reply_count': metrics.get('reply_count', 0),
                'quote_count': metrics.get('quote_count', 0)
            }
        }
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from tweet text"""
        import re
        hashtags = re.findall(r'#\w+', text)
        return [tag[1:] for tag in hashtags]  # Remove the # symbol