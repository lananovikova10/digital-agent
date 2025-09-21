"""
Content processor for enriching articles with metadata and embeddings
"""
import asyncio
from typing import Dict, Any, List
import structlog
from sentence_transformers import SentenceTransformer
import numpy as np

logger = structlog.get_logger()


class ContentProcessor:
    """Processes and enriches article content"""
    
    def __init__(self):
        # Load embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Content quality thresholds
        self.min_content_length = 50
        self.max_content_length = 10000
    
    async def enrich_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich article with additional metadata and embeddings"""
        enriched = article.copy()
        
        # Generate content embedding
        content_text = self._prepare_text_for_embedding(article)
        embedding = await self._generate_embedding(content_text)
        enriched['embedding'] = embedding.tolist()
        
        # Extract keywords
        keywords = self._extract_keywords(content_text)
        enriched['keywords'] = keywords
        
        # Calculate content quality score
        quality_score = self._calculate_quality_score(article)
        enriched['quality_score'] = quality_score
        
        # Detect content type
        content_type = self._detect_content_type(article)
        enriched['content_type'] = content_type
        
        # Extract entities (simplified version)
        entities = self._extract_entities(content_text)
        enriched['entities'] = entities
        
        logger.debug("Article enriched", 
                    title=article.get('title', '')[:50],
                    quality_score=quality_score)
        
        return enriched
    
    def _prepare_text_for_embedding(self, article: Dict[str, Any]) -> str:
        """Prepare text for embedding generation"""
        title = article.get('title', '')
        content = article.get('content', '')
        
        # Combine title and content, truncate if too long
        combined_text = f"{title}. {content}"
        
        if len(combined_text) > self.max_content_length:
            combined_text = combined_text[:self.max_content_length]
        
        return combined_text
    
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, 
            self.embedding_model.encode, 
            text
        )
        return embedding
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (simplified implementation)"""
        # This is a basic implementation - in production, use more sophisticated NLP
        import re
        from collections import Counter
        
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        words = [word for word in words if word not in stop_words]
        
        # Get most common words
        word_counts = Counter(words)
        keywords = [word for word, count in word_counts.most_common(10)]
        
        return keywords
    
    def _calculate_quality_score(self, article: Dict[str, Any]) -> float:
        """Calculate content quality score (0-1)"""
        score = 0.0
        
        # Title quality
        title = article.get('title', '')
        if len(title) > 10:
            score += 0.2
        
        # Content length
        content = article.get('content', '')
        if len(content) >= self.min_content_length:
            score += 0.3
        
        # Engagement metrics
        score_val = article.get('score', 0)
        comments = article.get('comments_count', 0)
        
        if score_val > 10:
            score += 0.2
        if comments > 5:
            score += 0.2
        
        # Source credibility (basic)
        source = article.get('source', '')
        if source in ['hackernews', 'reddit', 'producthunt']:
            score += 0.1
        
        return min(score, 1.0)
    
    def _detect_content_type(self, article: Dict[str, Any]) -> str:
        """Detect the type of content"""
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()
        url = article.get('url', '').lower()
        
        # Check for different content types
        if any(word in title + content for word in ['launch', 'announce', 'release']):
            return 'announcement'
        elif any(word in title + content for word in ['funding', 'raised', 'investment']):
            return 'funding'
        elif any(word in title + content for word in ['tutorial', 'how to', 'guide']):
            return 'tutorial'
        elif 'github.com' in url:
            return 'code'
        elif any(word in title + content for word in ['research', 'study', 'paper']):
            return 'research'
        else:
            return 'general'
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities (simplified implementation)"""
        # This is a basic implementation - in production, use spaCy or similar
        import re
        
        entities = []
        
        # Extract company names (capitalized words)
        companies = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for company in companies[:5]:  # Limit to 5
            entities.append({'text': company, 'type': 'company'})
        
        # Extract URLs
        urls = re.findall(r'https?://[^\s]+', text)
        for url in urls[:3]:  # Limit to 3
            entities.append({'text': url, 'type': 'url'})
        
        return entities