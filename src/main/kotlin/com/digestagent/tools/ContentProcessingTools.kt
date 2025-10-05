package com.digestagent.tools

import ai.koog.agents.core.tools.annotations.Tool
import ai.koog.agents.core.tools.annotations.LLMDescription
import com.digestagent.config.Configuration
import com.digestagent.model.Article
import com.digestagent.services.HuggingFaceService
import kotlinx.serialization.Serializable
import org.slf4j.LoggerFactory

@Serializable
data class ProcessingResult(
    val enrichedArticles: List<Article>,
    val processingStats: Map<String, Int>
)

@Serializable
data class RankingResult(
    val rankedArticles: List<Article>,
    val rankingCriteria: List<String>
)

class ContentProcessingTools {
    private val logger = LoggerFactory.getLogger(ContentProcessingTools::class.java)
    private var huggingFaceService: HuggingFaceService? = null
    
    init {
        Configuration.huggingFaceToken?.let { token ->
            huggingFaceService = HuggingFaceService(token)
            logger.info("Hugging Face service initialized for article summarization")
        } ?: logger.warn("Hugging Face token not configured, summaries will be basic")
    }

    @Tool(customName = "enrich_articles")
    @LLMDescription(description = "Enrich articles with metadata, tags, and relevance scores")
    suspend fun enrichArticles(articles: List<Article>, topics: List<String>): ProcessingResult {
        logger.info("Enriching {} articles for topics: {}", articles.size, topics)
        
        val enriched = articles.map { article ->
            // Simple enrichment - in production would use embeddings and ML models
            val relevanceScore = calculateRelevanceScore(article, topics)
            val extractedTags = extractTags(article.content)
            
            article.copy(
                score = relevanceScore,
                tags = extractedTags,
                metadata = article.metadata + mapOf(
                    "enriched_at" to System.currentTimeMillis().toString(),
                    "relevance_score" to relevanceScore.toString()
                )
            )
        }
        
        val stats = mapOf(
            "enriched_count" to enriched.size,
            "avg_score" to enriched.map { it.score }.average().toInt()
        )
        
        logger.info("Enrichment complete. Stats: {}", stats)
        
        return ProcessingResult(enriched, stats)
    }

    @Tool(customName = "rank_articles_by_relevance")
    @LLMDescription(description = "Rank articles by relevance to topics and importance metrics")
    suspend fun rankArticlesByRelevance(
        articles: List<Article>, 
        topics: List<String>,
        maxResults: Int = 50
    ): RankingResult {
        logger.info("Ranking {} articles for topics: {}", articles.size, topics)
        
        val criteria = listOf(
            "Topic relevance",
            "Content quality",
            "Source authority",
            "Recency"
        )
        
        val ranked = articles
            .sortedByDescending { it.score }
            .take(maxResults)
        
        logger.info("Ranking complete. Top {} articles selected", ranked.size)
        
        return RankingResult(ranked, criteria)
    }

    @Tool(customName = "extract_key_insights")
    @LLMDescription(description = "Extract key insights and trends from a collection of articles")
    suspend fun extractKeyInsights(articles: List<Article>): List<String> {
        logger.info("Extracting insights from {} articles", articles.size)
        
        // Simple insight extraction - in production would use NLP and ML
        val insights = mutableListOf<String>()
        
        // Analyze common themes
        val commonWords = articles.flatMap { 
            it.content.split(" ").filter { word -> 
                word.length > 5 && !isCommonWord(word.lowercase()) 
            }
        }
        .groupingBy { it.lowercase() }
        .eachCount()
        .filter { it.value > 2 }
        .keys.take(5)
        
        insights.add("Trending topics: ${commonWords.joinToString(", ")}")
        
        // Analyze sources
        val topSources = articles.groupingBy { it.source }
            .eachCount()
            .entries
            .sortedByDescending { it.value }
            .take(3)
            .map { "${it.key} (${it.value} articles)" }
        
        insights.add("Most active sources: ${topSources.joinToString(", ")}")
        
        logger.info("Extracted {} insights", insights.size)
        return insights
    }

    @Tool(customName = "summarize_articles")
    @LLMDescription(description = "Generate AI-powered summaries for articles using Qwen model")
    suspend fun summarizeArticles(articles: List<Article>): List<Article> {
        logger.info("Generating summaries for {} articles", articles.size)
        
        val huggingFace = huggingFaceService
        if (huggingFace == null) {
            logger.warn("Hugging Face service not available, using basic summaries")
            return articles.map { article ->
                article.copy(summary = generateBasicSummary(article.content))
            }
        }
        
        var successCount = 0
        var errorCount = 0
        
        val summarizedArticles = articles.map { article ->
            try {
                val aiSummary = huggingFace.summarizeArticle(article.title, article.content)
                if (aiSummary != null) {
                    successCount++
                    article.copy(summary = aiSummary)
                } else {
                    errorCount++
                    val fallbackSummary = generateBasicSummary(article.content)
                    article.copy(summary = fallbackSummary)
                }
            } catch (e: Exception) {
                logger.warn("Failed to summarize article '{}', using fallback", article.title, e)
                errorCount++
                val fallbackSummary = generateBasicSummary(article.content)
                article.copy(summary = fallbackSummary)
            }
        }
        
        logger.info("Summarization complete: {} AI summaries, {} fallbacks", successCount, errorCount)
        return summarizedArticles
    }
    
    /**
     * Generate a basic summary when AI service is unavailable
     */
    private fun generateBasicSummary(content: String): String {
        // Take first few sentences or up to 200 characters
        val sentences = content.split(". ", "! ", "? ")
        val summary = when {
            sentences.size >= 2 -> "${sentences[0]}. ${sentences[1]}."
            sentences.size == 1 && sentences[0].length > 200 -> sentences[0].take(200) + "..."
            else -> sentences.firstOrNull() ?: "No content available for summary."
        }
        
        return summary.trim()
    }

    private fun calculateRelevanceScore(article: Article, topics: List<String>): Double {
        val titleMatches = topics.count { topic ->
            article.title.lowercase().contains(topic.lowercase())
        }
        val contentMatches = topics.count { topic ->
            article.content.lowercase().contains(topic.lowercase())
        }
        
        return (titleMatches * 2.0 + contentMatches) / topics.size
    }

    private fun extractTags(content: String): List<String> {
        // Simple tag extraction - would use NLP in production
        val keywords = listOf("AI", "ML", "startup", "funding", "tech", "innovation", "development")
        return keywords.filter { 
            content.lowercase().contains(it.lowercase()) 
        }
    }

    private fun isCommonWord(word: String): Boolean {
        val commonWords = setOf("the", "and", "with", "that", "this", "have", "from", "they", "been", "said")
        return commonWords.contains(word)
    }
}