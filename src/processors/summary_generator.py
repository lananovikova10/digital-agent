"""
Summary generator for creating weekly reports and insights
"""
import os
from typing import List, Dict, Any
import structlog
from datetime import datetime, timedelta
import requests
import json
import asyncio
import aiohttp

logger = structlog.get_logger()


class SummaryGenerator:
    """Generates summaries and insights from ranked articles using Hugging Face models"""
    
    def __init__(self):
        self.hf_token = os.getenv('HUGGING_FACE_TOKEN')
        self.api_base = "https://api-inference.huggingface.co/models/"
        
        # Use different models for different tasks
        self.summarization_model = "facebook/bart-large-cnn"  # Good for summarization
        self.text_generation_model = "microsoft/DialoGPT-medium"  # For generating reports
        
        # Alternative models to try:
        # "facebook/bart-large-cnn" - Good for summarization
        # "google/pegasus-xsum" - Good for extractive summarization  
        # "microsoft/DialoGPT-large" - Good for dialogue and conversation
        # "microsoft/DialoGPT-medium" - Smaller, faster alternative
        # "gpt2" - Simple text generation
        
        self.session = None
    
    async def _init_session(self):
        """Initialize HTTP session for Hugging Face API"""
        if self.session is None:
            if not self.hf_token:
                logger.warning("Hugging Face token not found")
                return False
            
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.hf_token}"},
                timeout=aiohttp.ClientTimeout(total=60)
            )
        return True
    
    async def _query_huggingface_model(self, model_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Query a Hugging Face model via API"""
        if not await self._init_session():
            raise ValueError("Could not initialize Hugging Face session")
        
        url = f"{self.api_base}{model_name}"
        
        try:
            async with self.session.post(url, json=inputs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Hugging Face API error: {response.status} - {error_text}")
                    raise Exception(f"API request failed: {response.status}")
        except Exception as e:
            logger.error(f"Error querying Hugging Face model {model_name}: {str(e)}")
            raise

    async def generate_summary(self, ranked_articles: List[Dict[str, Any]], topics: List[str]) -> Dict[str, Any]:
        """Generate comprehensive summary from ranked articles"""
        try:
            if not await self._init_session():
                logger.warning("Hugging Face session not initialized, using fallback summary")
                return self._generate_fallback_summary(ranked_articles, topics)
                
            logger.info("Generating summary with Hugging Face models", article_count=len(ranked_articles))
            
            # Take top articles for summary
            top_articles = ranked_articles[:50]  # Limit for API efficiency
            
            # Group articles by content type and source
            grouped_articles = self._group_articles(top_articles)
            
            # Generate summaries for each group
            summaries = {}
            for group_name, articles in grouped_articles.items():
                if articles:
                    try:
                        group_summary = await self._summarize_article_group(articles, group_name)
                        summaries[group_name] = group_summary
                    except Exception as e:
                        logger.warning(f"Failed to summarize group {group_name}: {e}")
                        summaries[group_name] = f"Failed to generate summary for {group_name} articles"
            
            # Extract key trends
            trends = await self._extract_trends(top_articles, topics)
            
            # Generate strategic insights
            insights = await self._generate_insights(top_articles, topics)
            
            summary = {
                'topics': topics,
                'period': self._get_period_info(),
                'article_count': len(ranked_articles),
                'top_articles': top_articles[:10],
                'summaries_by_group': summaries,
                'key_trends': trends,
                'strategic_insights': insights,
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info("Summary generation complete")
            return summary
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return self._generate_fallback_summary(ranked_articles, topics)
    
    async def compose_report(self, summary: Dict[str, Any], ranked_articles: List[Dict[str, Any]], topics: List[str]) -> str:
        """Compose the final weekly report"""
        logger.info("Composing final report")
        
        try:
            if not await self._init_session():
                # Return enhanced basic report without Hugging Face
                logger.warning("Hugging Face not available, generating enhanced basic report")
                return self._generate_enhanced_basic_report(summary, ranked_articles, topics)
            
            # Prepare content for report generation
            content = self._prepare_report_content(summary, ranked_articles, topics)
            
            # Generate the report with Hugging Face
            report_prompt = f"""Create a comprehensive weekly intelligence report based on the following content. Structure it professionally with:
1. Executive Summary
2. Key Trends
3. Notable Developments
4. Strategic Recommendations
5. Action Items

Content to analyze:
{content}
"""
            
            # Use text generation model to create the report
            response = await self._query_huggingface_model(
                self.text_generation_model,
                {
                    "inputs": report_prompt,
                    "parameters": {
                        "max_length": 1500,
                        "temperature": 0.3,
                        "do_sample": True,
                        "top_p": 0.9
                    }
                }
            )
            
            # Extract generated text
            if isinstance(response, list) and len(response) > 0:
                report = response[0].get("generated_text", "")
                # Remove the prompt from the response
                if report.startswith(report_prompt):
                    report = report[len(report_prompt):].strip()
            else:
                report = "Error generating report with Hugging Face model."
            
            # Append sources section to the generated report
            sources_section = self._generate_sources_section(ranked_articles[:10])
            report += f"\n\n{sources_section}"
            
            logger.info("Report composition complete")
            return report
            
        except Exception as e:
            logger.error(f"Report composition failed: {e}")
            return self._generate_enhanced_basic_report(summary, ranked_articles, topics)
    
    def _group_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group articles by content type and source"""
        groups = {
            'announcements': [],
            'funding': [],
            'research': [],
            'tutorials': [],
            'general': []
        }
        
        for article in articles:
            content_type = article.get('content_type', 'general')
            if content_type in groups:
                groups[content_type].append(article)
            else:
                groups['general'].append(article)
        
        return groups
    
    async def _summarize_article_group(self, articles: List[Dict[str, Any]], group_name: str) -> str:
        """Summarize a group of articles using Hugging Face"""
        # Prepare articles for summarization
        article_texts = []
        for article in articles[:5]:  # Limit for API efficiency
            text = f"Title: {article.get('title', '')}\n"
            text += f"Source: {article.get('source', '')}\n"
            text += f"Content: {article.get('content', '')[:300]}...\n"
            article_texts.append(text)
        
        content = f"Summarize these {group_name} articles:\n\n" + "\n".join(article_texts)
        
        try:
            # Use a summarization-specific model
            response = await self._query_huggingface_model(
                "facebook/bart-large-cnn",  # Good for summarization
                {
                    "inputs": content,
                    "parameters": {
                        "max_length": 200,
                        "min_length": 50,
                        "do_sample": False
                    }
                }
            )
            
            if isinstance(response, list) and len(response) > 0:
                return response[0].get("summary_text", f"Summary for {group_name} articles")
            else:
                return f"Articles in {group_name} category analyzed and processed"
                
        except Exception as e:
            logger.warning(f"Summarization failed for {group_name}: {e}")
            return f"Articles in {group_name} category: {len(articles)} articles processed"
    
    async def _extract_trends(self, articles: List[Dict[str, Any]], topics: List[str]) -> List[str]:
        """Extract key trends from articles using pattern analysis"""
        try:
            # For now, use a simpler approach based on article analysis
            trends = []
            
            # Count content types
            content_types = {}
            sources = {}
            keywords_count = {}
            
            for article in articles[:15]:
                content_type = article.get('content_type', 'general')
                source = article.get('source', 'unknown')
                
                content_types[content_type] = content_types.get(content_type, 0) + 1
                sources[source] = sources.get(source, 0) + 1
                
                # Extract keywords from title
                title = article.get('title', '').lower()
                for topic in topics:
                    if topic.lower() in title:
                        keywords_count[topic] = keywords_count.get(topic, 0) + 1
            
            # Generate trend insights
            if content_types:
                most_common_type = max(content_types, key=content_types.get)
                trends.append(f"Increased activity in {most_common_type} content")
            
            if sources:
                most_active_source = max(sources, key=sources.get)
                trends.append(f"High engagement from {most_active_source} discussions")
            
            for topic in topics:
                if keywords_count.get(topic, 0) > 2:
                    trends.append(f"Growing interest in {topic}")
            
            trends.append(f"Analysis of {len(articles)} articles from {len(sources)} sources")
            
            return trends[:5]
            
        except Exception as e:
            logger.warning(f"Trend extraction failed: {e}")
            return ["Data processing and analysis completed", "Multiple sources analyzed", "Content trends identified"]
    
    async def _generate_insights(self, articles: List[Dict[str, Any]], topics: List[str]) -> List[str]:
        """Generate strategic insights based on article analysis"""
        try:
            insights = []
            
            # Focus on high-scoring articles
            top_articles = [a for a in articles if a.get('ranking_score', 0) > 0.5][:10]
            
            if not top_articles:
                top_articles = articles[:10]
            
            # Analyze patterns for insights
            tech_keywords = ['AI', 'ML', 'API', 'framework', 'tool', 'library', 'platform', 'developer', 'code']
            business_keywords = ['funding', 'launch', 'acquisition', 'partnership', 'startup', 'company']
            
            tech_count = 0
            business_count = 0
            
            for article in top_articles:
                title_content = f"{article.get('title', '')} {article.get('content', '')[:200]}".lower()
                
                if any(keyword in title_content for keyword in tech_keywords):
                    tech_count += 1
                if any(keyword in title_content for keyword in business_keywords):
                    business_count += 1
            
            # Generate insights based on analysis
            if tech_count > business_count:
                insights.append("Strong focus on technical innovation and developer tools")
                insights.append("Technology trends indicate continued emphasis on AI and ML integration")
            elif business_count > tech_count:
                insights.append("Business development and funding activities are prominent")
                insights.append("Market shows active investment and partnership opportunities")
            else:
                insights.append("Balanced mix of technical and business developments")
            
            # Topic-specific insights
            for topic in topics:
                topic_articles = [a for a in top_articles if topic.lower() in f"{a.get('title', '')} {a.get('content', '')[:200]}".lower()]
                if topic_articles:
                    insights.append(f"{topic} remains a key area of interest with {len(topic_articles)} relevant developments")
            
            insights.append(f"Analyzed {len(articles)} articles to identify strategic opportunities")
            
            return insights[:5]
            
        except Exception as e:
            logger.warning(f"Insights generation failed: {e}")
            return [
                "Technical and business trends analyzed",
                "Multiple development opportunities identified", 
                "Strategic positioning opportunities available",
                "Market intelligence gathered from diverse sources"
            ]
    
    def _prepare_report_content(self, summary: Dict[str, Any], ranked_articles: List[Dict[str, Any]], topics: List[str]) -> str:
        """Prepare content for final report generation"""
        content = f"""
        WEEKLY INTELLIGENCE REPORT
        
        Topics: {', '.join(topics)}
        Period: {summary.get('period', {})}
        Total Articles Analyzed: {summary.get('article_count', 0)}
        
        TOP ARTICLES:
        """
        
        for i, article in enumerate(summary.get('top_articles', [])[:5], 1):
            content += f"""
        {i}. {article.get('title', '')}
           Source: {article.get('source', '')}
           Score: {article.get('ranking_score', 0):.2f}
           URL: {article.get('url', '')}
        """
        
        content += f"""
        
        KEY TRENDS:
        {chr(10).join(f"- {trend}" for trend in summary.get('key_trends', []))}
        
        STRATEGIC INSIGHTS:
        {chr(10).join(f"- {insight}" for insight in summary.get('strategic_insights', []))}
        
        SOURCE ARTICLES WITH QUOTES AND SUMMARIES:
        """
        
        # Add detailed source information with quotes
        for i, article in enumerate(summary.get('top_articles', [])[:10], 1):
            content += f"""
        
        [{i}] {article.get('title', '')}
        Source: {article.get('source', '').upper()}
        Author: {article.get('author', 'Unknown')}
        URL: {article.get('url', '')}
        Published: {str(article.get('published_at', ''))[:10] if article.get('published_at') else 'Unknown'}
        Engagement: {article.get('score', 0)} points, {article.get('comments_count', 0)} comments
        Quality Score: {article.get('ranking_score', 0):.2f}/1.0
        
        Summary: {self._extract_summary(article)}
        
        """
        
        content += f"""
        
        GROUP SUMMARIES:
        """
        
        for group, group_summary in summary.get('summaries_by_group', {}).items():
            if group_summary:
                content += f"""
        {group.upper()}:
        {group_summary}
        """
        
        return content
    
    def _get_period_info(self) -> Dict[str, str]:
        """Get period information for the report"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        return {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'week_of': start_date.strftime('Week of %B %d, %Y')
        }
    
    def _extract_summary(self, article: Dict[str, Any]) -> str:
        """Extract a concise summary from article content"""
        content = article.get('content', '')
        title = article.get('title', '')
        
        if not content:
            return f"Article about {title.lower()}"
        
        # Take first 2 sentences or 200 characters, whichever is shorter
        sentences = content.split('. ')
        if len(sentences) >= 2:
            summary = '. '.join(sentences[:2]) + '.'
        else:
            summary = content[:200] + '...' if len(content) > 200 else content
        
        return summary.strip()
    

    def _generate_fallback_summary(self, ranked_articles: List[Dict[str, Any]], topics: List[str]) -> Dict[str, Any]:
        """Generate a basic summary without LLM"""
        top_articles = ranked_articles[:10]
        
        # Extract basic trends from article titles and content types
        content_types = {}
        sources = {}
        
        for article in top_articles:
            content_type = article.get('content_type', 'general')
            source = article.get('source', 'unknown')
            
            content_types[content_type] = content_types.get(content_type, 0) + 1
            sources[source] = sources.get(source, 0) + 1
        
        trends = [
            f"Most common content type: {max(content_types, key=content_types.get) if content_types else 'N/A'}",
            f"Most active source: {max(sources, key=sources.get) if sources else 'N/A'}",
            f"Total articles analyzed: {len(ranked_articles)}"
        ]
        
        insights = [
            "Hugging Face token required for AI-powered detailed analysis",
            "Configure Hugging Face API key to enable full intelligence features",
            "Basic article ranking and filtering is working"
        ]
        
        return {
            'topics': topics,
            'period': self._get_period_info(),
            'article_count': len(ranked_articles),
            'top_articles': top_articles,
            'summaries_by_group': {'general': 'Basic summary - API key required for detailed analysis'},
            'key_trends': trends,
            'strategic_insights': insights,
            'generated_at': datetime.now().isoformat()
        }
    
    def _generate_enhanced_basic_report(self, summary: Dict[str, Any], ranked_articles: List[Dict[str, Any]], topics: List[str]) -> str:
        """Generate an enhanced basic report without LLM"""
        period_info = summary.get('period', {})
        
        report = f"""WEEKLY INTELLIGENCE REPORT

EXECUTIVE SUMMARY:
This week's intelligence report covers {', '.join(topics)} based on analysis of {len(ranked_articles)} articles from multiple sources. The report highlights key developments, trends, and strategic insights from {period_info.get('start_date', 'the past week')} to {period_info.get('end_date', 'today')}.

KEY TRENDS:
"""
        
        for trend in summary.get('key_trends', []):
            report += f"• {trend}\n"
        
        report += f"""
STRATEGIC INSIGHTS:
"""
        
        for insight in summary.get('strategic_insights', []):
            report += f"• {insight}\n"
        
        # Add sources section
        report += f"\n{self._generate_sources_section(ranked_articles[:10])}"
        
        return report
    
    def _generate_sources_section(self, articles: List[Dict[str, Any]]) -> str:
        """Generate a detailed sources section with quotes and summaries"""
        if not articles:
            return ""
        
        sources_section = """SOURCE ARTICLES & KEY INSIGHTS:

The following articles were analyzed to generate this report. Each entry includes a summary, key quote, and link to the original source.

"""
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Untitled')
            url = article.get('url', '')
            source = article.get('source', 'Unknown').upper()
            author = article.get('author', 'Unknown')
            published_at_raw = article.get('published_at', '')
            if isinstance(published_at_raw, str):
                published_at = published_at_raw[:10] if published_at_raw else 'Unknown'
            else:
                published_at = str(published_at_raw)[:10] if published_at_raw else 'Unknown'
            score = article.get('score', 0)
            comments = article.get('comments_count', 0)
            ranking_score = article.get('ranking_score', 0)
            
            summary = self._extract_summary(article)
            
            sources_section += f"""[{i}] {title}
    Source: {source} | Author: {author} | Published: {published_at}
    Engagement: {score} points, {comments} comments | Quality Score: {ranking_score:.2f}/1.0
    URL: {url}
    
    Summary: {summary}
    
    ---
    
"""
        
        return sources_section
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None