"""
FastAPI application for the weekly intelligence agent
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import structlog

from ..agents.weekly_intel import WeeklyIntelAgent
from ..storage.database import DatabaseManager

logger = structlog.get_logger()

app = FastAPI(
    title="Weekly Intelligence Agent API",
    description="API for managing weekly intelligence reports",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
agent = WeeklyIntelAgent()
db_manager = DatabaseManager()


# Pydantic models
class TopicRequest(BaseModel):
    topics: List[str]
    days_back: Optional[int] = 7


class ReportResponse(BaseModel):
    report_id: str
    content: str
    topics: List[str]
    created_at: str


class ArticleResponse(BaseModel):
    id: str
    title: str
    url: str
    source: str
    published_at: str
    ranking_score: float


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Weekly Intelligence Agent API", "status": "healthy"}


@app.post("/reports/generate")
async def generate_report(request: TopicRequest, background_tasks: BackgroundTasks):
    """Generate a new weekly intelligence report"""
    logger.info("Report generation requested", topics=request.topics)
    
    try:
        # Run the agent workflow
        report_content = await agent.run_weekly_intel(request.topics)
        
        # Store the report
        report_id = await db_manager.store_report(
            report_content, 
            {"topics": request.topics}
        )
        
        return {
            "message": "Report generated successfully",
            "report_id": str(report_id),
            "topics": request.topics
        }
    
    except Exception as e:
        logger.error("Report generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.get("/reports", response_model=List[ReportResponse])
async def get_reports(limit: int = 10):
    """Get recent reports"""
    try:
        reports = db_manager.get_reports(limit=limit)
        
        return [
            ReportResponse(
                report_id=str(report.id),
                content=report.content,
                topics=report.topics or [],
                created_at=report.created_at.isoformat()
            )
            for report in reports
        ]
    
    except Exception as e:
        logger.error("Failed to fetch reports", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch reports")


@app.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str):
    """Get a specific report"""
    try:
        report = db_manager.get_report_by_id(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return ReportResponse(
            report_id=str(report.id),
            content=report.content,
            topics=report.topics or [],
            created_at=report.created_at.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch report", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch report")


@app.get("/articles", response_model=List[ArticleResponse])
async def get_articles(days_back: int = 7, limit: int = 50):
    """Get recent articles"""
    try:
        articles = db_manager.get_recent_articles(days_back=days_back, limit=limit)
        
        return [
            ArticleResponse(
                id=str(article.id),
                title=article.title,
                url=article.url,
                source=article.source,
                published_at=article.published_at.isoformat(),
                ranking_score=article.ranking_score or 0.0
            )
            for article in articles
        ]
    
    except Exception as e:
        logger.error("Failed to fetch articles", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch articles")


@app.get("/articles/topic/{topic}", response_model=List[ArticleResponse])
async def get_articles_by_topic(topic: str, days_back: int = 7):
    """Get articles for a specific topic"""
    try:
        articles = db_manager.get_articles_by_topic(topic, days_back=days_back)
        
        return [
            ArticleResponse(
                id=str(article.id),
                title=article.title,
                url=article.url,
                source=article.source,
                published_at=article.published_at.isoformat(),
                ranking_score=article.ranking_score or 0.0
            )
            for article in articles
        ]
    
    except Exception as e:
        logger.error("Failed to fetch articles by topic", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch articles")


@app.get("/reports/{report_id}/articles")
async def get_report_articles(report_id: str, limit: int = 20):
    """Get articles used in a specific report"""
    try:
        # For now, return recent articles that match the report's topics
        report = db_manager.get_report_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Get articles from the same time period as the report
        articles = db_manager.get_recent_articles(days_back=7, limit=limit)
        
        # Format articles with additional info for the web interface
        formatted_articles = []
        for article in articles:
            content = article.content or ""
            
            # Extract summary (first 2 sentences or 200 chars)
            sentences = content.split('. ')
            if len(sentences) >= 2:
                summary = '. '.join(sentences[:2]) + '.'
            else:
                summary = content[:200] + '...' if len(content) > 200 else content
            
            # Extract key quote
            import re
            key_quote = ""
            if content:
                # Look for quoted text
                quotes = re.findall(r'"([^"]*)"', content)
                if quotes:
                    meaningful_quotes = [q for q in quotes if len(q) > 20 and len(q) < 150]
                    if meaningful_quotes:
                        key_quote = max(meaningful_quotes, key=len)
                
                # If no quotes, extract key sentence
                if not key_quote:
                    key_terms = ['announced', 'released', 'launched', 'developed', 'created', 'built']
                    for sentence in sentences:
                        if any(term in sentence.lower() for term in key_terms) and len(sentence) > 30:
                            key_quote = sentence.strip()
                            break
                    
                    # Fallback to first substantial sentence
                    if not key_quote:
                        for sentence in sentences:
                            if len(sentence) > 30:
                                key_quote = sentence.strip()
                                break
            
            formatted_articles.append({
                "id": str(article.id),
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "author": article.author,
                "published_at": article.published_at.isoformat(),
                "ranking_score": article.ranking_score or 0.0,
                "score": article.score or 0,
                "comments_count": article.comments_count or 0,
                "content": content,
                "summary": summary.strip() if summary else f"Article about {article.title.lower()}",
                "key_quote": key_quote or content[:100] + "..." if content else article.title
            })
        
        return formatted_articles
    
    except Exception as e:
        logger.error("Failed to fetch report articles", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch report articles")


@app.post("/topics")
async def create_topic(name: str, description: str = "", keywords: List[str] = None):
    """Create a new topic"""
    try:
        topic_id = db_manager.create_topic(name, description, keywords or [])
        
        return {
            "message": "Topic created successfully",
            "topic_id": topic_id,
            "name": name
        }
    
    except Exception as e:
        logger.error("Failed to create topic", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create topic")


@app.get("/topics")
async def get_topics():
    """Get all active topics"""
    try:
        topics = db_manager.get_active_topics()
        
        return [
            {
                "id": str(topic.id),
                "name": topic.name,
                "description": topic.description,
                "keywords": topic.keywords or [],
                "article_count": topic.article_count or 0,
                "last_processed": topic.last_processed.isoformat() if topic.last_processed else None
            }
            for topic in topics
        ]
    
    except Exception as e:
        logger.error("Failed to fetch topics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch topics")


@app.post("/sources/test/{source_name}")
async def test_source(source_name: str, topic: str = "AI"):
    """Test a specific data source"""
    try:
        from ..sources.manager import SourceManager
        
        source_manager = SourceManager()
        articles = await source_manager.fetch_source(source_name, topic, days_back=1)
        
        return {
            "source": source_name,
            "topic": topic,
            "article_count": len(articles),
            "sample_articles": articles[:3] if articles else []
        }
    
    except Exception as e:
        logger.error("Source test failed", source=source_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Source test failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)