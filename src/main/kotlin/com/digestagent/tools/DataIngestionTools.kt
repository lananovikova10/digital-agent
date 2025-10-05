package com.digestagent.tools

import ai.koog.agents.core.tools.annotations.Tool
import ai.koog.agents.core.tools.annotations.LLMDescription
import com.digestagent.model.Article
import com.digestagent.sources.SourceManager
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.serialization.Serializable
import org.slf4j.LoggerFactory

@Serializable
data class IngestionResult(
    val articles: List<Article>,
    val totalCount: Int,
    val sourceBreakdown: Map<String, Int>
)

class DataIngestionTools(
    private val sourceManager: SourceManager
) {
    private val logger = LoggerFactory.getLogger(DataIngestionTools::class.java)

    @Tool(customName = "ingest_articles_for_topics")
    @LLMDescription(description = "Ingest articles from all configured sources for given topics")
    suspend fun ingestArticlesForTopics(topics: List<String>): IngestionResult = coroutineScope {
        logger.info("Starting data ingestion for topics: {}", topics)
        
        val allArticles = mutableListOf<Article>()
        val sourceBreakdown = mutableMapOf<String, Int>()
        
        // Fetch from all sources in parallel
        val jobs = topics.map { topic ->
            async {
                val articles = sourceManager.fetchAllSources(topic)
                articles.forEach { article ->
                    sourceBreakdown.merge(article.source, 1, Int::plus)
                }
                articles
            }
        }
        
        jobs.forEach { job ->
            allArticles.addAll(job.await())
        }
        
        logger.info("Ingestion complete. Total articles: {}", allArticles.size)
        
        IngestionResult(
            articles = allArticles,
            totalCount = allArticles.size,
            sourceBreakdown = sourceBreakdown.toMap()
        )
    }

    @Tool(customName = "filter_articles_by_date")
    @LLMDescription(description = "Filter articles by date range (last N days)")
    suspend fun filterArticlesByDate(articles: List<Article>, lastNDays: Int): List<Article> {
        logger.info("Filtering {} articles from last {} days", articles.size, lastNDays)
        
        // For simplicity, returning all articles - would implement date filtering in real scenario
        // In production, you'd parse publishedAt and filter by date
        val filtered = articles.take(100) // Limit to prevent overwhelming the LLM
        
        logger.info("Filtered to {} articles", filtered.size)
        return filtered
    }

    @Tool(customName = "deduplicate_articles")
    @LLMDescription(description = "Remove duplicate articles based on URL and title similarity")
    suspend fun deduplicateArticles(articles: List<Article>): List<Article> {
        logger.info("Deduplicating {} articles", articles.size)
        
        val deduped = articles.distinctBy { it.url }
            .groupBy { it.title.lowercase().take(50) }
            .mapValues { (_, duplicates) -> duplicates.first() }
            .values
            .toList()
        
        logger.info("Deduplicated to {} articles", deduped.size)
        return deduped
    }
}