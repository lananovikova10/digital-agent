"""
Ranking engine for prioritizing articles by relevance and importance
"""
from typing import List, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import structlog

logger = structlog.get_logger()


class RankingEngine:
    """Ranks articles by relevance and importance"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Ranking weights
        self.weights = {
            'relevance': 0.4,
            'quality': 0.3,
            'engagement': 0.2,
            'recency': 0.1
        }
    
    async def rank_articles(self, articles: List[Dict[str, Any]], topics: List[str]) -> List[Dict[str, Any]]:
        """Rank articles by combined score"""
        logger.info("Starting article ranking", count=len(articles))
        
        if not articles:
            return []
        
        # Generate topic embeddings
        topic_text = " ".join(topics)
        topic_embedding = self.embedding_model.encode(topic_text)
        
        # Calculate scores for each article
        scored_articles = []
        for article in articles:
            scores = await self._calculate_scores(article, topic_embedding)
            
            # Calculate weighted final score
            final_score = (
                scores['relevance'] * self.weights['relevance'] +
                scores['quality'] * self.weights['quality'] +
                scores['engagement'] * self.weights['engagement'] +
                scores['recency'] * self.weights['recency']
            )
            
            article_with_score = article.copy()
            article_with_score['ranking_score'] = final_score
            article_with_score['ranking_breakdown'] = scores
            
            scored_articles.append(article_with_score)
        
        # Sort by score (descending)
        ranked_articles = sorted(scored_articles, key=lambda x: x['ranking_score'], reverse=True)
        
        logger.info("Article ranking complete", 
                   top_score=ranked_articles[0]['ranking_score'] if ranked_articles else 0)
        
        return ranked_articles
    
    async def _calculate_scores(self, article: Dict[str, Any], topic_embedding: np.ndarray) -> Dict[str, float]:
        """Calculate individual scores for an article"""
        scores = {}
        
        # Relevance score (semantic similarity)
        scores['relevance'] = self._calculate_relevance_score(article, topic_embedding)
        
        # Quality score (from content processor)
        scores['quality'] = article.get('quality_score', 0.5)
        
        # Engagement score (normalized)
        scores['engagement'] = self._calculate_engagement_score(article)
        
        # Recency score (time-based decay)
        scores['recency'] = self._calculate_recency_score(article)
        
        return scores
    
    def _calculate_relevance_score(self, article: Dict[str, Any], topic_embedding: np.ndarray) -> float:
        """Calculate semantic relevance to topics"""
        article_embedding = np.array(article.get('embedding', []))
        
        if len(article_embedding) == 0:
            # Fallback to keyword matching
            return self._keyword_relevance_fallback(article)
        
        # Calculate cosine similarity
        similarity = cosine_similarity([topic_embedding], [article_embedding])[0][0]
        
        # Normalize to 0-1 range
        return max(0, min(1, (similarity + 1) / 2))
    
    def _keyword_relevance_fallback(self, article: Dict[str, Any]) -> float:
        """Fallback relevance calculation using keywords"""
        keywords = article.get('keywords', [])
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()
        
        # Simple keyword matching
        relevant_keywords = ['ai', 'machine learning', 'startup', 'tech', 'innovation']
        
        matches = 0
        for keyword in keywords:
            if any(rel_kw in keyword.lower() for rel_kw in relevant_keywords):
                matches += 1
        
        # Check title and content for relevant terms
        for rel_kw in relevant_keywords:
            if rel_kw in title or rel_kw in content:
                matches += 1
        
        return min(1.0, matches / 5.0)  # Normalize to 0-1
    
    def _calculate_engagement_score(self, article: Dict[str, Any]) -> float:
        """Calculate engagement score based on metrics"""
        score = article.get('score', 0)
        comments = article.get('comments_count', 0)
        
        # Normalize based on source
        source = article.get('source', '')
        
        if source == 'hackernews':
            # HN typically has lower scores
            normalized_score = min(1.0, score / 100.0)
            normalized_comments = min(1.0, comments / 50.0)
        elif source == 'reddit':
            # Reddit can have higher scores
            normalized_score = min(1.0, score / 1000.0)
            normalized_comments = min(1.0, comments / 100.0)
        elif source == 'twitter':
            # Twitter engagement (likes + retweets)
            normalized_score = min(1.0, score / 500.0)
            normalized_comments = min(1.0, comments / 50.0)
        else:
            # Default normalization
            normalized_score = min(1.0, score / 100.0)
            normalized_comments = min(1.0, comments / 25.0)
        
        # Weighted combination
        return (normalized_score * 0.7) + (normalized_comments * 0.3)
    
    def _calculate_recency_score(self, article: Dict[str, Any]) -> float:
        """Calculate recency score with time decay"""
        from datetime import datetime, timedelta
        
        published_at = article.get('published_at')
        if not published_at:
            return 0.5  # Default for missing dates
        
        # Calculate hours since publication
        now = datetime.now()
        if published_at.tzinfo is not None:
            # Make now timezone-aware if published_at is
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)
        
        hours_ago = (now - published_at).total_seconds() / 3600
        
        # Exponential decay over 7 days (168 hours)
        decay_factor = 168  # hours
        recency_score = np.exp(-hours_ago / decay_factor)
        
        return max(0, min(1, recency_score))
    
    def get_top_articles(self, ranked_articles: List[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
        """Get top N articles"""
        return ranked_articles[:limit]
    
    def filter_by_threshold(self, ranked_articles: List[Dict[str, Any]], threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Filter articles by minimum ranking score"""
        return [article for article in ranked_articles if article.get('ranking_score', 0) >= threshold]