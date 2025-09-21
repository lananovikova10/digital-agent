"""
Weekly Intelligence Agent - Main LangGraph workflow
"""
from typing import Dict, List, Any
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
import structlog

from ..sources import SourceManager
from ..processors import ContentProcessor, RankingEngine, SummaryGenerator
from ..storage import DatabaseManager

logger = structlog.get_logger()


class WeeklyIntelState(BaseModel):
    """State for the weekly intelligence workflow"""
    topics: List[str] = []
    raw_articles: List[Dict[str, Any]] = []
    enriched_articles: List[Dict[str, Any]] = []
    ranked_articles: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {}
    report: str = ""
    metadata: Dict[str, Any] = {}


class WeeklyIntelAgent:
    """Main agent orchestrating the weekly intelligence workflow"""
    
    def __init__(self):
        self.source_manager = SourceManager()
        self.content_processor = ContentProcessor()
        self.ranking_engine = RankingEngine()
        self.summary_generator = SummaryGenerator()
        self.db_manager = DatabaseManager()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(WeeklyIntelState)
        
        # Add nodes
        workflow.add_node("ingest", self._ingest_node)
        workflow.add_node("enrich", self._enrich_node)
        workflow.add_node("rank", self._rank_node)
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("compose", self._compose_node)
        workflow.add_node("deliver", self._deliver_node)
        
        # Define edges
        workflow.set_entry_point("ingest")
        workflow.add_edge("ingest", "enrich")
        workflow.add_edge("enrich", "rank")
        workflow.add_edge("rank", "summarize")
        workflow.add_edge("summarize", "compose")
        workflow.add_edge("compose", "deliver")
        workflow.add_edge("deliver", END)
        
        return workflow.compile()
    
    async def _ingest_node(self, state: WeeklyIntelState) -> WeeklyIntelState:
        """Ingest data from all sources"""
        logger.info("Starting data ingestion", topics=state.topics)
        
        raw_articles = []
        for topic in state.topics:
            articles = await self.source_manager.fetch_all_sources(topic)
            raw_articles.extend(articles)
        
        state.raw_articles = raw_articles
        state.metadata["ingestion_count"] = len(raw_articles)
        
        logger.info("Ingestion complete", count=len(raw_articles))
        return state
    
    async def _enrich_node(self, state: WeeklyIntelState) -> WeeklyIntelState:
        """Enrich articles with metadata and embeddings"""
        logger.info("Starting content enrichment")
        
        enriched_articles = []
        for article in state.raw_articles:
            enriched = await self.content_processor.enrich_article(article)
            enriched_articles.append(enriched)
        
        state.enriched_articles = enriched_articles
        logger.info("Enrichment complete", count=len(enriched_articles))
        return state
    
    async def _rank_node(self, state: WeeklyIntelState) -> WeeklyIntelState:
        """Rank articles by relevance and importance"""
        logger.info("Starting article ranking")
        
        ranked_articles = await self.ranking_engine.rank_articles(
            state.enriched_articles, 
            state.topics
        )
        
        state.ranked_articles = ranked_articles
        logger.info("Ranking complete", count=len(ranked_articles))
        return state
    
    async def _summarize_node(self, state: WeeklyIntelState) -> WeeklyIntelState:
        """Generate summaries and extract insights"""
        logger.info("Starting summarization")
        
        summary = await self.summary_generator.generate_summary(
            state.ranked_articles,
            state.topics
        )
        
        state.summary = summary
        logger.info("Summarization complete")
        return state
    
    async def _compose_node(self, state: WeeklyIntelState) -> WeeklyIntelState:
        """Compose the final report"""
        logger.info("Starting report composition")
        
        report = await self.summary_generator.compose_report(
            state.summary,
            state.ranked_articles,
            state.topics
        )
        
        state.report = report
        logger.info("Report composition complete")
        return state
    
    async def _deliver_node(self, state: WeeklyIntelState) -> WeeklyIntelState:
        """Store and deliver the report"""
        logger.info("Starting report delivery")
        
        # Store articles in database
        if state.ranked_articles:
            stored_ids = await self.db_manager.store_articles(state.ranked_articles)
            logger.info("Articles stored", count=len(stored_ids))
        
        # Store report in database
        report_id = await self.db_manager.store_report(state.report, {
            **state.metadata,
            "topics": state.topics,
            "article_count": len(state.ranked_articles)
        })
        
        state.metadata["report_id"] = report_id
        logger.info("Report stored", report_id=report_id)
        
        # TODO: Add delivery mechanisms (email, Slack, etc.)
        
        logger.info("Report delivery complete")
        return state
    
    async def run_weekly_intel(self, topics: List[str]) -> str:
        """Run the complete weekly intelligence workflow"""
        initial_state = WeeklyIntelState(topics=topics)
        
        logger.info("Starting weekly intelligence workflow", topics=topics)
        
        final_state = await self.graph.ainvoke(initial_state)
        
        logger.info("Weekly intelligence workflow complete")
        
        # Handle both dict and object returns from LangGraph
        if isinstance(final_state, dict):
            return final_state.get("report", "")
        else:
            return final_state.report


if __name__ == "__main__":
    import asyncio
    
    async def main():
        agent = WeeklyIntelAgent()
        topics = ["AI", "machine learning", "startup funding"]
        report = await agent.run_weekly_intel(topics)
        print(report)
    
    asyncio.run(main())