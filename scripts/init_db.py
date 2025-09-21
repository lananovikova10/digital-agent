#!/usr/bin/env python3
"""
Database initialization script
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.database import DatabaseManager
from src.storage.models import Base
import structlog

logger = structlog.get_logger()


def main():
    """Initialize the database"""
    logger.info("Initializing database...")
    
    try:
        # Create database manager (this will create tables)
        db_manager = DatabaseManager()
        
        # Create some default topics
        default_topics = [
            ("AI", "Artificial Intelligence and Machine Learning", ["artificial intelligence", "machine learning", "deep learning", "neural networks"]),
            ("startup", "Startup News and Funding", ["startup", "funding", "venture capital", "seed round"]),
            ("fintech", "Financial Technology", ["fintech", "cryptocurrency", "blockchain", "digital payments"]),
            ("tech", "General Technology News", ["technology", "software", "programming", "development"])
        ]
        
        for name, description, keywords in default_topics:
            try:
                topic_id = db_manager.create_topic(name, description, keywords)
                logger.info("Created topic", name=name, topic_id=topic_id)
            except Exception as e:
                logger.warning("Topic already exists or error creating", name=name, error=str(e))
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()