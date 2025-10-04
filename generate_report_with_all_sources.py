#!/usr/bin/env python3
"""
Generate report with all 14 sources - bypassing import cache
"""
from dotenv import load_dotenv
load_dotenv()

import asyncio
import sys
import os
import importlib.util
from datetime import datetime

# Load modules directly to bypass import cache
def load_module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

async def generate_report():
    """Generate report using direct module loading"""
    print('🚀 Starting Weekly Intelligence Report Generation (All Sources)')
    print('=' * 70)
    
    # Load manager module directly
    manager_module = load_module_from_file('manager', 'src/sources/manager.py')
    content_processor_module = load_module_from_file('content_processor', 'src/processors/content_processor.py')
    ranking_module = load_module_from_file('ranking_engine', 'src/processors/ranking_engine.py')
    summary_module = load_module_from_file('summary_generator', 'src/processors/summary_generator.py')
    
    # Get topics from environment
    topics = os.getenv('TOPICS', '["MCP", "AI for software developers"]')
    if isinstance(topics, str):
        import json
        try:
            topics = json.loads(topics)
        except:
            topics = ["MCP", "AI for software developers"]
    
    print(f'📋 Topics: {", ".join(topics)}')
    print(f'📅 Report date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # Initialize components
    source_manager = manager_module.SourceManager()
    content_processor = content_processor_module.ContentProcessor()
    ranking_engine = ranking_module.RankingEngine()
    summary_generator = summary_module.SummaryGenerator()
    
    print(f'\\n🔍 Available sources: {len(source_manager.get_available_sources())}')
    for source in sorted(source_manager.get_available_sources()):
        print(f'   • {source}')
    
    all_articles = []
    
    # Fetch articles for each topic
    for topic in topics:
        print(f'\\n🔍 Fetching articles for topic: "{topic}"')
        print('-' * 50)
        
        # Fetch from all sources
        topic_articles = await source_manager.fetch_all_sources(topic, days_back=7)
        print(f'📰 Found {len(topic_articles)} articles for "{topic}"')
        
        # Add topic metadata
        for article in topic_articles:
            article['topic'] = topic
        
        all_articles.extend(topic_articles)
    
    print(f'\\n📊 Total articles collected: {len(all_articles)}')
    
    if len(all_articles) == 0:
        print('❌ No articles found. Check API keys and network connectivity.')
        return
    
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
    print('=' * 70)
    print(f'📊 Report ID: {report["id"]}')
    print(f'📅 Generated: {report["created_at"]}')
    print(f'📰 Total articles processed: {report["total_articles_processed"]}')
    print(f'🔄 After deduplication: {report["articles_after_dedup"]}')
    print(f'⭐ Top articles selected: {report["top_articles_count"]}')
    
    # Show summary
    print(f'\\n📋 Executive Summary:')
    print('-' * 50)
    summary_preview = summary[:400] + '...' if len(summary) > 400 else summary
    print(summary_preview)
    
    # Show article breakdown by source
    by_source = {}
    for article in top_articles:
        source = article.get('source', 'unknown')
        by_source[source] = by_source.get(source, 0) + 1
    
    print(f'\\n📈 Top Articles by Source:')
    print('-' * 50)
    for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
        emoji = "🆕" if source in ['devto', 'medium', 'substack', 'youtube_podcasts', 'stackoverflow', 'bluesky', 'arxiv', 'rss_feeds'] else "📰"
        print(f'   {emoji} {source}: {count} articles')
    
    # Show top 5 articles
    print(f'\\n⭐ Top 5 Articles:')
    print('-' * 50)
    for i, article in enumerate(top_articles[:5], 1):
        score = article.get('relevance_score', 0)
        print(f'{i}. [{article["source"]}] {article["title"][:60]}...')
        print(f'   👤 {article["author"]} | 📊 Score: {score:.2f}')
        print(f'   🔗 {article["url"][:70]}...')
        print()
    
    # Save report to file
    import json
    report_filename = f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f'💾 Report saved to: {report_filename}')
    
    return report

if __name__ == '__main__':
    asyncio.run(generate_report())