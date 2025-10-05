package com.digestagent.tools

import ai.koog.agents.core.tools.annotations.Tool
import ai.koog.agents.core.tools.annotations.LLMDescription
import com.digestagent.model.Article
import com.digestagent.model.Summary
import kotlinx.serialization.Serializable
import org.slf4j.LoggerFactory
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

@Serializable
data class ReportSections(
    val executiveSummary: String,
    val keyInsights: List<String>,
    val topArticles: List<Article>,
    val trends: List<String>,
    val sourceAnalysis: String
)

class ReportGenerationTools {
    private val logger = LoggerFactory.getLogger(ReportGenerationTools::class.java)

    @Tool(customName = "generate_summary_insights")
    @LLMDescription(description = "Generate summary and key insights from ranked articles")
    suspend fun generateSummaryInsights(
        articles: List<Article>, 
        topics: List<String>
    ): Summary {
        logger.info("Generating summary from {} articles for topics: {}", articles.size, topics)
        
        val keyInsights = extractInsights(articles)
        val trends = identifyTrends(articles)
        val topSources = articles.groupingBy { it.source }
            .eachCount()
            .entries
            .sortedByDescending { it.value }
            .take(5)
            .map { it.key }
        
        val summary = Summary(
            keyInsights = keyInsights,
            trends = trends,
            keyQuotes = extractKeyQuotes(articles),
            topSources = topSources,
            metadata = mapOf(
                "generated_at" to System.currentTimeMillis().toString(),
                "article_count" to articles.size.toString(),
                "topics" to topics.joinToString(",")
            )
        )
        
        logger.info("Summary generated with {} insights and {} trends", 
                   keyInsights.size, trends.size)
        return summary
    }

    @Tool(customName = "compose_final_report")
    @LLMDescription(description = "Compose the final weekly intelligence report from summary and articles")
    suspend fun composeFinalReport(
        summary: Summary,
        articles: List<Article>,
        topics: List<String>
    ): String {
        logger.info("Composing final report for {} topics with {} articles", 
                   topics.size, articles.size)
        
        val formatter = DateTimeFormatter.ofPattern("MMMM dd, yyyy")
        val currentDate = LocalDateTime.now().format(formatter)
        
        val report = buildString {
            appendLine("# Weekly Intelligence Report")
            appendLine("**Generated on:** $currentDate")
            appendLine("**Topics:** ${topics.joinToString(", ")}")
            appendLine("**Sources Analyzed:** ${summary.topSources.size} sources, ${articles.size} articles")
            appendLine()
            
            // Executive Summary
            appendLine("## Executive Summary")
            appendLine()
            appendLine("This week's intelligence report covers key developments in ${topics.joinToString(", ")}. ")
            appendLine("Analysis of ${articles.size} articles from ${summary.topSources.size} sources reveals several important trends and insights.")
            appendLine()
            
            // Key Insights
            if (summary.keyInsights.isNotEmpty()) {
                appendLine("## Key Insights")
                appendLine()
                summary.keyInsights.forEachIndexed { index, insight ->
                    appendLine("${index + 1}. $insight")
                }
                appendLine()
            }
            
            // Trends
            if (summary.trends.isNotEmpty()) {
                appendLine("## Emerging Trends")
                appendLine()
                summary.trends.forEach { trend ->
                    appendLine("- $trend")
                }
                appendLine()
            }
            
            // Top Articles
            appendLine("## Featured Articles")
            appendLine()
            articles.take(10).forEachIndexed { index, article ->
                appendLine("### ${index + 1}. ${article.title}")
                appendLine("**Source:** ${article.source}")
                appendLine("**URL:** ${article.url}")
                appendLine("**Score:** ${String.format("%.2f", article.score)}")
                if (article.tags.isNotEmpty()) {
                    appendLine("**Tags:** ${article.tags.joinToString(", ")}")
                }
                appendLine()
                
                // Include AI-generated summary if available, otherwise use excerpt
                if (!article.summary.isNullOrBlank()) {
                    appendLine("**Summary:** ${article.summary}")
                    appendLine()
                } else {
                    val excerpt = if (article.content.length > 200) {
                        article.content.take(200) + "..."
                    } else {
                        article.content
                    }
                    appendLine(excerpt)
                    appendLine()
                }
                
                appendLine("---")
                appendLine()
            }
            
            // Source Analysis
            appendLine("## Source Analysis")
            appendLine()
            appendLine("**Top Sources by Article Count:**")
            val sourceStats = articles.groupingBy { it.source }
                .eachCount()
                .entries
                .sortedByDescending { it.value }
                .take(5)
            
            sourceStats.forEach { (source, count) ->
                appendLine("- $source: $count articles")
            }
            appendLine()
            
            // Footer
            appendLine("---")
            appendLine("*Report generated by Weekly Intelligence Agent*")
            appendLine("*Generation time: ${summary.metadata["generated_at"]}*")
        }
        
        logger.info("Final report composed. Length: {} characters", report.length)
        return report
    }

    @Tool(customName = "create_report_sections")
    @LLMDescription(description = "Create structured report sections for different output formats")
    suspend fun createReportSections(
        summary: Summary,
        articles: List<Article>
    ): ReportSections {
        logger.info("Creating structured report sections")
        
        val executiveSummary = """
            This week's intelligence analysis processed ${articles.size} articles from ${summary.topSources.size} sources.
            Key findings include ${summary.keyInsights.size} major insights and ${summary.trends.size} emerging trends.
            The analysis reveals significant developments across the monitored topic areas.
        """.trimIndent()
        
        val sourceAnalysis = """
            Analysis covered ${summary.topSources.size} primary sources, with the most active being:
            ${summary.topSources.take(3).joinToString(", ")}. 
            Article quality scores ranged from ${articles.minOfOrNull { it.score } ?: 0.0} to ${articles.maxOfOrNull { it.score } ?: 0.0}.
        """.trimIndent()
        
        return ReportSections(
            executiveSummary = executiveSummary,
            keyInsights = summary.keyInsights,
            topArticles = articles.take(10),
            trends = summary.trends,
            sourceAnalysis = sourceAnalysis
        )
    }

    private fun extractInsights(articles: List<Article>): List<String> {
        val insights = mutableListOf<String>()
        
        // Analyze by score distribution
        val highScoreCount = articles.count { it.score > 2.0 }
        if (highScoreCount > 0) {
            insights.add("$highScoreCount articles show high relevance scores, indicating strong topic alignment")
        }
        
        // Analyze by source diversity
        val sourceCount = articles.map { it.source }.distinct().size
        insights.add("Coverage spans $sourceCount different sources, providing diverse perspectives")
        
        // Analyze by tags
        val topTags = articles.flatMap { it.tags }
            .groupingBy { it }
            .eachCount()
            .entries
            .sortedByDescending { it.value }
            .take(3)
            .map { it.key }
        
        if (topTags.isNotEmpty()) {
            insights.add("Most discussed themes: ${topTags.joinToString(", ")}")
        }
        
        return insights
    }
    
    private fun identifyTrends(articles: List<Article>): List<String> {
        val trends = mutableListOf<String>()
        
        // Simple trend identification
        val recentArticles = articles.take(articles.size / 2) // Assume first half is more recent
        val olderArticles = articles.drop(articles.size / 2)
        
        val recentTags = recentArticles.flatMap { it.tags }.groupingBy { it }.eachCount()
        val olderTags = olderArticles.flatMap { it.tags }.groupingBy { it }.eachCount()
        
        recentTags.forEach { (tag, recentCount) ->
            val olderCount = olderTags[tag] ?: 0
            if (recentCount > olderCount * 1.5) {
                trends.add("Increasing focus on $tag (${recentCount - olderCount} more mentions)")
            }
        }
        
        if (trends.isEmpty()) {
            trends.add("Steady coverage across all monitored topics")
        }
        
        return trends
    }
    
    private fun extractKeyQuotes(articles: List<Article>): List<String> {
        // Simple quote extraction - would use NLP in production
        return articles.take(5).map { article ->
            val sentences = article.content.split(". ")
            val bestSentence = sentences.filter { it.length > 50 && it.length < 200 }
                .firstOrNull() ?: sentences.firstOrNull() ?: ""
            "\"$bestSentence\" - ${article.source}"
        }
    }
}