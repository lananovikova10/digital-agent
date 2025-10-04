#!/usr/bin/env python3
"""
Generate a weekly intelligence report
"""
from dotenv import load_dotenv
load_dotenv()

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sources.manager import SourceManager
from processors.content_processor import ContentProcessor
from processors.ranking_engine import RankingEngine
from processors.summary_generator import SummaryGenerator

async def generate_report():
    """Generate a complete weekly intelligence report"""
    print('🚀 Starting Weekly Intelligence Report Generation')
    print('=' * 60)
    
    # Get topics from environment
    topics = os.getenv('TOPICS', '["AI", "software development"]')
    if isinstance(topics, str):
        import json
        try:
            topics = json.loads(topics)
        except:
            topics = ["AI", "software development"]
    
    print(f'📋 Topics: {", ".join(topics)}')
    print(f'📅 Report date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # Initialize components
    source_manager = SourceManager()
    content_processor = ContentProcessor()
    ranking_engine = RankingEngine()
    summary_generator = SummaryGenerator()
    
    print(f'\\n🔍 Available sources: {len(source_manager.get_available_sources())}')
    for source in sorted(source_manager.get_available_sources()):
        print(f'   • {source}')
    
    all_articles = []
    
    # Fetch articles for each topic
    for topic in topics:
        print(f'\\n🔍 Fetching articles for topic: "{topic}"')
        print('-' * 40)
        
        # Fetch from all sources
        topic_articles = await source_manager.fetch_all_sources(topic, days_back=7)
        print(f'📰 Found {len(topic_articles)} articles for "{topic}"')
        
        # Add topic metadata
        for article in topic_articles:
            article['topic'] = topic
        
        all_articles.extend(topic_articles)
    
    print(f'\\n📊 Total articles collected: {len(all_articles)}')
    
    # Remove duplicates
    unique_articles = content_processor.deduplicate_articles(all_articles)
    print(f'📊 After deduplication: {len(unique_articles)} articles')
    
    # Process and rank articles
    print('\\n🔄 Processing and ranking articles...')
    processed_articles = []
    
    for article in unique_articles:
        # Process content
        processed = content_processor.process_article(article)
        
        # Calculate relevance score
        for topic in topics:
            if article.get('topic') == topic:
                score = ranking_engine.calculate_relevance_score(processed, topic)
                processed['relevance_score'] = score
                break
        
        processed_articles.append(processed)
    
    # Sort by relevance score
    processed_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    # Take top articles
    top_articles = processed_articles[:50]  # Top 50 articles
    
    print(f'📊 Top articles selected: {len(top_articles)}')
    
    # Generate summary
    print('\\n📝 Generating executive summary...')
    summary = summary_generator.generate_summary(top_articles, topics)
    
    # Create report
    report = {
        'id': f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'created_at': datetime.now().isoformat(),
        'topics': topics,
        'summary': summary,
        'articles': top_articles,
        'total_articles_processed': len(all_articles),
        'articles_after_dedup': len(unique_articles),
        'top_articles_count': len(top_articles)
    }
    
    # Show results
    print('\\n✅ Report Generation Complete!')
    print('=' * 60)
    print(f'📊 Report ID: {report["id"]}')
    print(f'📅 Generated: {report["created_at"]}')
    print(f'📰 Total articles processed: {report["total_articles_processed"]}')
    print(f'🔄 After deduplication: {report["articles_after_dedup"]}')
    print(f'⭐ Top articles selected: {report["top_articles_count"]}')
    
    # Show summary
    print(f'\\n📋 Executive Summary:')
    print('-' * 40)
    summary_preview = summary[:300] + '...' if len(summary) > 300 else summary
    print(summary_preview)
    
    # Show article breakdown by source
    by_source = {}
    for article in top_articles:
        source = article.get('source', 'unknown')
        by_source[source] = by_source.get(source, 0) + 1
    
    print(f'\\n📈 Top Articles by Source:')
    print('-' * 40)
    for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
        print(f'   • {source}: {count} articles')
    
    # Show top 5 articles
    print(f'\\n⭐ Top 5 Articles:')
    print('-' * 40)
    for i, article in enumerate(top_articles[:5], 1):
        score = article.get('relevance_score', 0)
        print(f'{i}. [{article["source"]}] {article["title"][:60]}...')
        print(f'   👤 {article["author"]} | 📊 Score: {score:.2f}')
        print(f'   🔗 {article["url"][:70]}...')
        print()
    
    return report

if __name__ == '__main__':
    asyncio.run(generate_report())