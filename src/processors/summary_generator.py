"""
Summary generator for creating weekly reports and insights
"""
import os
from typing import List, Dict, Any
import structlog
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from datetime import datetime, timedelta

logger = structlog.get_logger()


class SummaryGenerator:
    """Generates summaries and insights from ranked articles"""
    
    def __init__(self):
        self.llm = None
        
        # Summary templates
        self.summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert analyst creating weekly intelligence reports. 
            Analyze the provided articles and create insightful summaries focusing on:
            1. Key trends and patterns
            2. Strategic implications
            3. Actionable insights
            4. Market opportunities and threats
            
            Be concise, analytical, and focus on business value."""),
            ("human", "{content}")
        ])
        
        self.report_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are creating a comprehensive weekly intelligence report.
            Structure the report with:
            1. Executive Summary
            2. Key Trends
            3. Notable Developments
            4. Strategic Recommendations
            5. Action Items
            
            Make it professional, actionable, and valuable for decision-makers."""),
            ("human", "{content}")
        ])
    
    def _init_llm(self):
        """Initialize LLM lazily"""
        if self.llm is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OpenAI API key not found")
                return False
            
            self.llm = ChatOpenAI(model="gpt-4", temperature=0.3)
        return True

    async def generate_summary(self, ranked_articles: List[Dict[str, Any]], topics: List[str]) -> Dict[str, Any]:
        """Generate comprehensive summary from ranked articles"""
        if not self._init_llm():
            logger.warning("LLM not initialized, using fallback summary")
            return self._generate_fallback_summary(ranked_articles, topics)
            
        logger.info("Generating summary", article_count=len(ranked_articles))
        
        # Take top articles for summary
        top_articles = ranked_articles[:50]  # Limit for token efficiency
        
        # Group articles by content type and source
        grouped_articles = self._group_articles(top_articles)
        
        # Generate summaries for each group
        summaries = {}
        for group_name, articles in grouped_articles.items():
            if articles:
                group_summary = await self._summarize_article_group(articles, group_name)
                summaries[group_name] = group_summary
        
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
    
    async def compose_report(self, summary: Dict[str, Any], ranked_articles: List[Dict[str, Any]], topics: List[str]) -> str:
        """Compose the final weekly report"""
        logger.info("Composing final report")
        
        # Prepare content for report generation
        content = self._prepare_report_content(summary, ranked_articles, topics)
        
        if not self._init_llm():
            # Return enhanced basic report without LLM
            logger.warning("LLM not available, generating enhanced basic report")
            return self._generate_enhanced_basic_report(summary, ranked_articles, topics)
        
        # Generate the report with LLM
        response = await self.llm.ainvoke(self.report_prompt.format_messages(content=content))
        report = response.content
        
        # Append sources section to the LLM-generated report
        sources_section = self._generate_sources_section(ranked_articles[:10])
        report += f"\n\n{sources_section}"
        
        logger.info("Report composition complete")
        return report
    
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
        """Summarize a group of articles"""
        # Prepare articles for summarization
        article_texts = []
        for article in articles[:10]:  # Limit for token efficiency
            text = f"Title: {article.get('title', '')}\n"
            text += f"Source: {article.get('source', '')}\n"
            text += f"Content: {article.get('content', '')[:500]}...\n"
            text += f"Score: {article.get('ranking_score', 0):.2f}\n\n"
            article_texts.append(text)
        
        content = f"Summarize these {group_name} articles:\n\n" + "\n".join(article_texts)
        
        response = await self.llm.ainvoke(self.summary_prompt.format_messages(content=content))
        return response.content
    
    async def _extract_trends(self, articles: List[Dict[str, Any]], topics: List[str]) -> List[str]:
        """Extract key trends from articles"""
        # Prepare trend analysis content
        trend_content = f"Topics of interest: {', '.join(topics)}\n\n"
        trend_content += "Analyze these articles and identify 3-5 key trends:\n\n"
        
        for article in articles[:20]:
            trend_content += f"- {article.get('title', '')}\n"
            trend_content += f"  Keywords: {', '.join(article.get('keywords', [])[:5])}\n"
            trend_content += f"  Type: {article.get('content_type', 'general')}\n\n"
        
        prompt = "Based on the articles above, identify the top 5 trends. Return as a simple list."
        
        response = await self.llm.ainvoke([
            SystemMessage(content="You are a trend analyst. Identify key patterns and trends from the provided articles."),
            HumanMessage(content=trend_content + "\n" + prompt)
        ])
        
        # Parse trends from response
        trends = [line.strip() for line in response.content.split('\n') if line.strip() and not line.startswith('#')]
        return trends[:5]
    
    async def _generate_insights(self, articles: List[Dict[str, Any]], topics: List[str]) -> List[str]:
        """Generate strategic insights"""
        insight_content = f"Topics: {', '.join(topics)}\n\n"
        insight_content += "Generate strategic insights from these developments:\n\n"
        
        # Focus on high-scoring articles
        top_articles = [a for a in articles if a.get('ranking_score', 0) > 0.7][:15]
        
        for article in top_articles:
            insight_content += f"Title: {article.get('title', '')}\n"
            insight_content += f"Type: {article.get('content_type', 'general')}\n"
            insight_content += f"Summary: {article.get('content', '')[:300]}...\n\n"
        
        prompt = "Provide 3-5 strategic insights and recommendations based on these developments."
        
        response = await self.llm.ainvoke([
            SystemMessage(content="You are a strategic analyst providing actionable business insights for the software company such as JetBrains which specialises in the tools for developers."),
            HumanMessage(content=insight_content + "\n" + prompt)
        ])
        
        # Parse insights from response
        insights = [line.strip() for line in response.content.split('\n') if line.strip() and not line.startswith('#')]
        return insights[:5]
    
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
        
        Key Quote: "{self._extract_key_quote(article)}"
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
    
    def _extract_key_quote(self, article: Dict[str, Any]) -> str:
        """Extract a key quote from article content"""
        content = article.get('content', '')
        title = article.get('title', '')
        
        if not content:
            return title
        
        import re
        
        # Helper function to check if text contains URLs or is mostly links
        def contains_urls_or_links(text: str) -> bool:
            url_patterns = [
                r'https?://[^\s]+',     # HTTP URLs
                r'www\.[^\s]+',         # www links
                r'\[.*?\]\(.*?\)',      # Markdown links
                r'<a\s+href=',          # HTML links
                r'github\.com',         # GitHub references
                r'\.com[/\s\)]',        # .com domains
                r'\.org[/\s\)]',        # .org domains
                r'\.net[/\s\)]',        # .net domains
                r'\.dev[/\s\)]',        # .dev domains
                r'x\.com/',             # X.com (Twitter)
                r'twitter\.com',        # Twitter
                r'linkedin\.com',       # LinkedIn
                r'youtube\.com',        # YouTube
                r'reddit\.com',         # Reddit
            ]
            
            for pattern in url_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            
            # Check if text ends with a URL-like pattern
            if re.search(r'https?://[^\s]+$', text.strip()):
                return True
                
            return False
        
        # Helper function to check if text is meaningful
        def is_meaningful_quote(text: str) -> bool:
            text = text.strip()
            
            # Must be at least 25 characters and not more than 200
            if len(text) < 25 or len(text) > 200:
                return False
                
            # Must contain at least 4 words
            words = text.split()
            if len(words) < 4:
                return False
            
            # Must not contain URLs or links
            if contains_urls_or_links(text):
                return False
            
            # Must not be mostly punctuation or numbers
            alphanumeric_chars = sum(c.isalnum() for c in text)
            if alphanumeric_chars < len(text) * 0.6:
                return False
            
            # Must not be just technical jargon or code
            code_indicators = ['function', 'class', 'import', 'def ', 'var ', 'const ', '{}', '[]', '()', '=>']
            if any(indicator in text.lower() for indicator in code_indicators):
                return False
            
            # Should contain some common English words
            common_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            if not any(word.lower() in text.lower() for word in common_words):
                return False
                
            return True
        
        # Clean content by removing obvious URLs and links first
        cleaned_content = content
        # Remove markdown links
        cleaned_content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned_content)
        # Remove HTML tags
        cleaned_content = re.sub(r'<[^>]+>', '', cleaned_content)
        # Remove standalone URLs
        cleaned_content = re.sub(r'https?://[^\s]+', '', cleaned_content)
        
        # Look for quoted text first
        quotes = re.findall(r'"([^"]*)"', cleaned_content)
        if quotes:
            # Filter and return the longest meaningful quote
            meaningful_quotes = [q for q in quotes if is_meaningful_quote(q)]
            if meaningful_quotes:
                return self._clean_quote_from_urls(max(meaningful_quotes, key=len))
        
        # Look for sentences that start with key phrases
        key_phrases = [
            'according to', 'the company', 'researchers found', 'the study shows',
            'experts believe', 'the report states', 'analysis reveals', 'data shows',
            'the team', 'scientists discovered', 'the research', 'findings suggest'
        ]
        
        sentences = re.split(r'[.!?]+', cleaned_content)
        for sentence in sentences:
            sentence = sentence.strip()
            if any(phrase in sentence.lower() for phrase in key_phrases):
                if is_meaningful_quote(sentence):
                    return self._clean_quote_from_urls(sentence)
        
        # Look for sentences with key action terms
        key_terms = [
            'announced', 'released', 'launched', 'developed', 'created', 'built', 
            'shows', 'demonstrates', 'reveals', 'introduces', 'features', 'offers',
            'enables', 'allows', 'provides', 'supports', 'includes', 'delivers',
            'explained', 'stated', 'mentioned', 'noted', 'said', 'reported'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if (any(term in sentence.lower() for term in key_terms) and 
                is_meaningful_quote(sentence)):
                return self._clean_quote_from_urls(sentence)
        
        # Look for descriptive sentences (avoid questions and commands)
        for sentence in sentences:
            sentence = sentence.strip()
            if (not sentence.endswith('?') and 
                not sentence.lower().startswith(('click', 'visit', 'see', 'check')) and
                is_meaningful_quote(sentence)):
                return self._clean_quote_from_urls(sentence)
        
        # Look for the first meaningful paragraph
        paragraphs = cleaned_content.split('\n')
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if len(paragraph) > 50:  # Substantial paragraph
                # Take first sentence of the paragraph
                first_sentence = re.split(r'[.!?]', paragraph)[0].strip()
                if is_meaningful_quote(first_sentence):
                    return self._clean_quote_from_urls(first_sentence)
        
        # Final fallback - try to extract meaningful content from title + first part of content
        combined = f"{title}. {cleaned_content[:200]}"
        sentences = re.split(r'[.!?]+', combined)
        for sentence in sentences[1:]:  # Skip title
            sentence = sentence.strip()
            if is_meaningful_quote(sentence):
                return self._clean_quote_from_urls(sentence)
        
        # Last resort - return a cleaned version of the title
        return self._clean_quote_from_urls(title)
    
    def _clean_quote_from_urls(self, text: str) -> str:
        """Clean a quote by removing URLs and link artifacts"""
        import re
        
        # Remove URLs
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'www\.[^\s]+', '', text)
        
        # Remove markdown link syntax
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove common URL artifacts
        text = re.sub(r'x\.com/[^\s]+', '', text)
        text = re.sub(r'github\.com[^\s]*', '', text)
        
        # Clean up extra whitespace and punctuation
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove trailing periods if they're at the end after URL removal
        text = text.rstrip('.')
        
        return text

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
            "OpenAI API key required for detailed analysis",
            "Configure API keys to enable full intelligence features",
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
            key_quote = self._extract_key_quote(article)
            
            sources_section += f"""[{i}] {title}
    Source: {source} | Author: {author} | Published: {published_at}
    Engagement: {score} points, {comments} comments | Quality Score: {ranking_score:.2f}/1.0
    URL: {url}
    
    Summary: {summary}
    
    Key Quote: "{key_quote}"
    
    ---
    
"""
        
        return sources_section