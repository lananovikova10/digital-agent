"""
Celery tasks for weekly intelligence processing
"""
from typing import List
import structlog
from .celery_app import celery_app
from ..agents.weekly_intel import WeeklyIntelAgent
from ..storage.database import DatabaseManager

logger = structlog.get_logger()


@celery_app.task(bind=True)
def generate_weekly_report(self, topics: List[str]):
    """Generate weekly intelligence report task"""
    logger.info("Starting weekly report generation task", topics=topics)
    
    try:
        # Initialize agent
        agent = WeeklyIntelAgent()
        
        # Run the workflow
        report = agent.run_weekly_intel(topics)
        
        logger.info("Weekly report generation completed", topics=topics)
        return {
            "status": "success",
            "topics": topics,
            "report_length": len(report)
        }
    
    except Exception as e:
        logger.error("Weekly report generation failed", error=str(e))
        self.retry(countdown=60, max_retries=3)


@celery_app.task
def cleanup_old_articles(days_to_keep: int = 30):
    """Clean up old articles task"""
    logger.info("Starting article cleanup", days_to_keep=days_to_keep)
    
    try:
        db_manager = DatabaseManager()
        db_manager.cleanup_old_articles(days_to_keep)
        
        logger.info("Article cleanup completed")
        return {"status": "success", "days_to_keep": days_to_keep}
    
    except Exception as e:
        logger.error("Article cleanup failed", error=str(e))
        return {"status": "error", "error": str(e)}


@celery_app.task
def process_topic_articles(topic: str, days_back: int = 7):
    """Process articles for a specific topic"""
    logger.info("Processing topic articles", topic=topic)
    
    try:
        from ..sources.manager import SourceManager
        from ..processors.content_processor import ContentProcessor
        from ..storage.database import DatabaseManager
        
        # Fetch articles
        source_manager = SourceManager()
        articles = source_manager.fetch_all_sources(topic, days_back)
        
        # Process articles
        processor = ContentProcessor()
        enriched_articles = []
        
        for article in articles:
            enriched = processor.enrich_article(article)
            enriched_articles.append(enriched)
        
        # Store articles
        db_manager = DatabaseManager()
        stored_ids = db_manager.store_articles(enriched_articles)
        
        # Update topic stats
        db_manager.update_topic_stats(topic, len(stored_ids))
        
        logger.info("Topic processing completed", 
                   topic=topic, 
                   processed_count=len(stored_ids))
        
        return {
            "status": "success",
            "topic": topic,
            "processed_count": len(stored_ids)
        }
    
    except Exception as e:
        logger.error("Topic processing failed", topic=topic, error=str(e))
        return {"status": "error", "topic": topic, "error": str(e)}