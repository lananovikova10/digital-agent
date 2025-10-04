#!/usr/bin/env python3
"""
Generate a complete weekly intelligence report using all sources
"""
from dotenv import load_dotenv
load_dotenv()

import asyncio
import sys
import os
import json
from datetime import datetime
from collections import Counter

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import all new sources directly
from sources.devto import DevToSource
from sources.medium import MediumSource
from sources.substack import SubstackSource
from sources.youtube_podcasts import YouTubePodcastSource
from sources.stackoverflow import StackOverflowSource
from sources.bluesky import BlueskySource
from sources.arxiv import ArxivSource
from sources.rss_feeds import RSSFeedsSource

# Import original sources
from sources.hackernews import HackerNewsSource
from sources.reddit import RedditSource
from sources.twitter import TwitterSource
from sources.producthunt import ProductHuntSource
from sources.yc_launches import YCLaunchesSource
from sources.techcrunch import TechCrunchSource

async def generate_report():
    """Generate a comprehensive weekly intelligence report"""
    print('🚀 Weekly Intelligence Report Generation')
    print('=' * 60)
    
    # Get topics from environment
    topics = os.getenv('TOPICS', '["MCP", "AI for software developers"]')
    if isinstance(topics, str):
        try:
            topics = json.loads(topics)
        except:
            topics = ["MCP", "AI for software developers"]
    
    print(f'📋 Topics: {", ".join(topics)}')
    print(f'📅 Report date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # Initialize all sources
    sources = {
        # Original sources
        'hackernews': HackerNewsSource(),
        'reddit': RedditSource(),
        'twitter': TwitterSource(),
        'producthunt': ProductHuntSource(),
        'yc_launches': YCLaunchesSource(),
        'techcrunch': TechCrunchSource(),
        
        # New sources
        'devto': DevToSource(),
        'medium': MediumSource(),
        'substack': SubstackSource(),
        'youtube_podcasts': YouTubePodcastSource(),
        'stackoverflow': StackOverflowSource(),
        'bluesky': BlueskySource(),
        'arxiv': ArxivSource(),
        'rss_feeds': RSSFeedsSource()
    }
    
    print(f'\\n🔍 Available sources: {len(sources)}')
    for source_name in sorted(sources.keys()):
        emoji = "🆕" if source_name in ['devto', 'medium', 'substack', 'youtube_podcasts', 'stackoverflow', 'bluesky', 'arxiv', 'rss_feeds'] else "📰"
        print(f'   {emoji} {source_name}')
    
    all_articles = []
    source_stats = {}
    
    # Fetch articles for each topic
    for topic in topics:
        print(f'\\n🔍 Fetching articles for topic: "{topic}"')
        print('-' * 50)
        
        topic_articles = []
        
        # Fetch from each source
        for source_name, source in sources.items():
            try:
                print(f'   Fetching from {source_name}...')
                articles = await source.fetch_articles(topic, days_back=7)
                
                # Add source and topic metadata
                for article in articles:
                    article['source'] = source_name
                    article['topic'] = topic
                
                topic_articles.extend(articles)
                source_stats[source_name] = source_stats.get(source_name, 0) + len(articles)
                
                if len(articles) > 0:
                    print(f'     ✅ {len(articles)} articles')
                else:
                    print(f'     ⚠️  0 articles')
                    
            except Exception as e:
                print(f'     ❌ Error: {str(e)[:50]}...')
                source_stats[source_name] = 0
        
        print(f'\\n📰 Total for "{topic}": {len(topic_articles)} articles')
        all_articles.extend(topic_articles)
    
    print(f'\\n📊 Collection Summary:')
    print(f'   Total articles: {len(all_articles)}')
    
    # Show stats by source
    print(f'\\n📈 Articles by source:')
    for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
        emoji = "🆕" if source in ['devto', 'medium', 'substack', 'youtube_podcasts', 'stackoverflow', 'bluesky', 'arxiv', 'rss_feeds'] else "📰"
        status = "✅" if count > 0 else "⚠️"
        print(f'   {status} {emoji} {source}: {count} articles')
    
    if len(all_articles) == 0:
        print('\\n❌ No articles found. Check API keys and network connectivity.')
        return
    
    # Simple deduplication by URL
    print(f'\\n🔄 Processing articles...')
    seen_urls = set()
    unique_articles = []
    
    for article in all_articles:
        url = article.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)
        elif not url:  # Keep articles without URLs
            unique_articles.append(article)
    
    print(f'   After deduplication: {len(unique_articles)} articles')
    
    # Simple scoring based on engagement
    for article in unique_articles:
        score = 0
        score += min(article.get('score', 0) / 100, 1.0)  # Normalize score
        score += min(article.get('comments_count', 0) / 50, 0.5)  # Comments bonus
        
        # Source credibility bonus
        source = article.get('source', '')
        if source in ['hackernews', 'reddit', 'arxiv']:
            score += 0.3
        elif source in ['techcrunch', 'medium', 'devto']:
            score += 0.2
        
        # Topic relevance (simple keyword matching)
        title_content = (article.get('title', '') + ' ' + article.get('content', '')).lower()
        for topic in topics:
            if topic.lower() in title_content:
                score += 0.5
                break
        
        article['relevance_score'] = score
    
    # Sort by relevance score
    unique_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    # Take top articles
    top_articles = unique_articles[:50]
    
    print(f'   Top articles selected: {len(top_articles)}')
    
    # Generate simple summary
    print(f'\\n📝 Generating summary...')
    
    # Count topics and sources in top articles
    topic_counts = Counter(article.get('topic', 'unknown') for article in top_articles)
    source_counts = Counter(article.get('source', 'unknown') for article in top_articles)
    
    summary_parts = []
    summary_parts.append(f"This weekly intelligence report covers {len(topics)} main topics: {', '.join(topics)}.")
    summary_parts.append(f"We analyzed {len(all_articles)} articles from {len(sources)} sources, selecting the top {len(top_articles)} most relevant articles.")
    
    if topic_counts:
        top_topic = topic_counts.most_common(1)[0]
        summary_parts.append(f"The most covered topic was '{top_topic[0]}' with {top_topic[1]} articles.")
    
    if source_counts:
        top_source = source_counts.most_common(1)[0]
        summary_parts.append(f"The most productive source was {top_source[0]} with {top_source[1]} articles in the final selection.")
    
    # Add insights about new sources
    new_source_articles = sum(1 for article in top_articles if article.get('source') in ['devto', 'medium', 'substack', 'youtube_podcasts', 'stackoverflow', 'bluesky', 'arxiv', 'rss_feeds'])
    if new_source_articles > 0:
        summary_parts.append(f"Our newly integrated sources contributed {new_source_articles} articles to this report, significantly expanding our coverage.")
    
    summary = ' '.join(summary_parts)
    
    # Create report
    report = {
        'id': f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'created_at': datetime.now().isoformat(),
        'topics': topics,
        'summary': summary,
        'articles': top_articles,
        'stats': {
            'total_articles_collected': len(all_articles),
            'unique_articles': len(unique_articles),
            'top_articles_selected': len(top_articles),
            'sources_used': len([s for s, c in source_stats.items() if c > 0]),
            'total_sources_available': len(sources)
        },
        'source_breakdown': dict(source_stats)
    }
    
    # Display results
    print(f'\\n✅ Report Generation Complete!')
    print('=' * 60)
    print(f'📊 Report ID: {report["id"]}')
    print(f'📅 Generated: {report["created_at"]}')
    print(f'📰 Total articles: {report["stats"]["total_articles_collected"]}')
    print(f'🔄 Unique articles: {report["stats"]["unique_articles"]}')
    print(f'⭐ Top articles: {report["stats"]["top_articles_selected"]}')
    print(f'📡 Active sources: {report["stats"]["sources_used"]}/{report["stats"]["total_sources_available"]}')
    
    print(f'\\n📋 Executive Summary:')
    print('-' * 50)
    print(summary)
    
    # Show top articles by source
    final_source_counts = Counter(article.get('source', 'unknown') for article in top_articles)
    print(f'\\n📈 Final Selection by Source:')
    print('-' * 50)
    for source, count in sorted(final_source_counts.items(), key=lambda x: x[1], reverse=True):
        emoji = "🆕" if source in ['devto', 'medium', 'substack', 'youtube_podcasts', 'stackoverflow', 'bluesky', 'arxiv', 'rss_feeds'] else "📰"
        print(f'   {emoji} {source}: {count} articles')
    
    # Show top 10 articles
    print(f'\\n⭐ Top 10 Articles:')
    print('-' * 50)
    for i, article in enumerate(top_articles[:10], 1):
        score = article.get('relevance_score', 0)
        source_emoji = "🆕" if article.get('source') in ['devto', 'medium', 'substack', 'youtube_podcasts', 'stackoverflow', 'bluesky', 'arxiv', 'rss_feeds'] else "📰"
        print(f'{i:2d}. {source_emoji} [{article["source"]}] {article["title"][:55]}...')
        print(f'     👤 {article.get("author", "Unknown")[:30]} | 📊 Score: {score:.2f} | 🏷️  {article.get("topic", "N/A")}')
        print(f'     🔗 {article["url"][:65]}...')
        print()
    
    # Save report
    report_filename = f'weekly_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f'💾 Full report saved to: {report_filename}')
    
    return report

if __name__ == '__main__':
    asyncio.run(generate_report())