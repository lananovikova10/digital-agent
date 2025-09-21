"""
Database models for the weekly intelligence agent
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

Base = declarative_base()


class Article(Base):
    """Article model for storing processed articles"""
    __tablename__ = 'articles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    url = Column(String(1000), unique=True, nullable=False)
    author = Column(String(200))
    source = Column(String(50), nullable=False)
    published_at = Column(DateTime, nullable=False)
    
    # Engagement metrics
    score = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    
    # Processing results
    embedding = Column(Vector(384))  # Dimension for all-MiniLM-L6-v2
    keywords = Column(JSON)
    entities = Column(JSON)
    tags = Column(JSON)
    
    # Quality and ranking
    quality_score = Column(Float, default=0.0)
    ranking_score = Column(Float, default=0.0)
    content_type = Column(String(50))
    
    # Metadata
    article_metadata = Column(JSON)
    processed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Report(Base):
    """Weekly report model"""
    __tablename__ = 'reports'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    
    # Report metadata
    topics = Column(JSON)  # List of topics covered
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    article_count = Column(Integer, default=0)
    
    # Summary data
    summary_data = Column(JSON)  # Full summary object
    key_trends = Column(JSON)    # List of trends
    strategic_insights = Column(JSON)  # List of insights
    
    # Status
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Topic(Base):
    """Topic configuration model"""
    __tablename__ = 'topics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    
    # Configuration
    keywords = Column(JSON)  # Related keywords
    sources = Column(JSON)   # Preferred sources
    is_active = Column(Boolean, default=True)
    
    # Tracking
    last_processed = Column(DateTime)
    article_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)