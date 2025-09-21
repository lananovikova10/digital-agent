"""
Database manager for the weekly intelligence agent
"""
import os
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import structlog
from datetime import datetime, timedelta

from .models import Base, Article, Report, Topic

logger = structlog.get_logger()


class DatabaseManager:
    """Manages database operations"""
    
    def __init__(self):
        database_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/weekly_intel')
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables"""
        try:
            # Enable pgvector extension
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
            
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Error creating database tables", error=str(e))
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def store_articles(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Store processed articles in database"""
        logger.info("Storing articles", count=len(articles))
        
        stored_ids = []
        
        with self.get_session() as session:
            for article_data in articles:
                try:
                    # Check if article already exists
                    existing = session.query(Article).filter_by(url=article_data['url']).first()
                    
                    if existing:
                        # Update existing article
                        for key, value in article_data.items():
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                        existing.updated_at = datetime.utcnow()
                        stored_ids.append(str(existing.id))
                    else:
                        # Create new article
                        article = Article(**article_data)
                        session.add(article)
                        session.flush()  # Get the ID
                        stored_ids.append(str(article.id))
                
                except IntegrityError as e:
                    logger.warning("Article already exists", url=article_data.get('url', ''))
                    session.rollback()
                    continue
                except Exception as e:
                    logger.error("Error storing article", error=str(e))
                    session.rollback()
                    continue
            
            session.commit()
        
        logger.info("Articles stored", stored_count=len(stored_ids))
        return stored_ids
    
    async def store_report(self, report_content: str, metadata: Dict[str, Any]) -> str:
        """Store weekly report"""
        logger.info("Storing report")
        
        with self.get_session() as session:
            # Calculate period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            report = Report(
                title=f"Weekly Intelligence Report - {start_date.strftime('%Y-%m-%d')}",
                content=report_content,
                topics=metadata.get('topics', []),
                period_start=start_date,
                period_end=end_date,
                article_count=metadata.get('ingestion_count', 0),
                summary_data=metadata.get('summary_data', {}),
                key_trends=metadata.get('key_trends', []),
                strategic_insights=metadata.get('strategic_insights', [])
            )
            
            session.add(report)
            session.commit()
            
            logger.info("Report stored", report_id=str(report.id))
            return str(report.id)
    
    def get_recent_articles(self, days_back: int = 7, limit: int = 100) -> List[Article]:
        """Get recent articles"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with self.get_session() as session:
            articles = session.query(Article)\
                .filter(Article.published_at >= cutoff_date)\
                .order_by(Article.ranking_score.desc())\
                .limit(limit)\
                .all()
            
            return articles
    
    def get_articles_by_topic(self, topic: str, days_back: int = 7) -> List[Article]:
        """Get articles related to a specific topic"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with self.get_session() as session:
            # Search in title, content, and keywords
            articles = session.query(Article)\
                .filter(Article.published_at >= cutoff_date)\
                .filter(
                    Article.title.ilike(f'%{topic}%') |
                    Article.content.ilike(f'%{topic}%') |
                    Article.keywords.astext.ilike(f'%{topic}%')
                )\
                .order_by(Article.ranking_score.desc())\
                .all()
            
            return articles
    
    def search_similar_articles(self, embedding: List[float], limit: int = 10) -> List[Article]:
        """Search for similar articles using vector similarity"""
        with self.get_session() as session:
            # Use pgvector for similarity search
            articles = session.query(Article)\
                .order_by(Article.embedding.cosine_distance(embedding))\
                .limit(limit)\
                .all()
            
            return articles
    
    def get_reports(self, limit: int = 10) -> List[Report]:
        """Get recent reports"""
        with self.get_session() as session:
            reports = session.query(Report)\
                .order_by(Report.created_at.desc())\
                .limit(limit)\
                .all()
            
            return reports
    
    def get_report_by_id(self, report_id: str) -> Optional[Report]:
        """Get report by ID"""
        with self.get_session() as session:
            return session.query(Report).filter_by(id=report_id).first()
    
    def create_topic(self, name: str, description: str = "", keywords: List[str] = None) -> str:
        """Create a new topic"""
        with self.get_session() as session:
            topic = Topic(
                name=name,
                description=description,
                keywords=keywords or []
            )
            
            session.add(topic)
            session.commit()
            
            return str(topic.id)
    
    def get_active_topics(self) -> List[Topic]:
        """Get all active topics"""
        with self.get_session() as session:
            return session.query(Topic).filter_by(is_active=True).all()
    
    def update_topic_stats(self, topic_name: str, article_count: int):
        """Update topic processing statistics"""
        with self.get_session() as session:
            topic = session.query(Topic).filter_by(name=topic_name).first()
            if topic:
                topic.last_processed = datetime.utcnow()
                topic.article_count = article_count
                session.commit()
    
    def cleanup_old_articles(self, days_to_keep: int = 30):
        """Clean up old articles"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with self.get_session() as session:
            deleted_count = session.query(Article)\
                .filter(Article.created_at < cutoff_date)\
                .delete()
            
            session.commit()
            
            logger.info("Cleaned up old articles", deleted_count=deleted_count)