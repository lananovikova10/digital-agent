package com.digestagent.services

import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.delay
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import org.slf4j.LoggerFactory

/**
 * Hugging Face API service for text summarization using Qwen models
 */
class HuggingFaceService(
    private val apiToken: String
) {
    private val logger = LoggerFactory.getLogger(HuggingFaceService::class.java)
    
    private val httpClient = HttpClient(CIO) {
        install(ContentNegotiation) {
            json(Json {
                ignoreUnknownKeys = true
                isLenient = true
            })
        }
        
        engine {
            // Configure connection timeouts
            requestTimeout = 60000 // 60 seconds
            
            // Enable HTTP/2 support
            pipelining = false
            
            // Connection pool settings
            maxConnectionsCount = 100
        }
    }
    
    // Using microsoft/DialoGPT-medium for better contextual summarization  
    private val baseUrl = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    
    @Serializable
    data class SummarizationRequest(
        val inputs: String,
        val parameters: SummarizationParameters = SummarizationParameters()
    )
    
    @Serializable
    data class SummarizationParameters(
        val max_length: Int = 150,
        val min_length: Int = 30,
        val do_sample: Boolean = false
    )
    
    @Serializable
    data class SummarizationResponse(
        val summary_text: String? = null,
        val error: String? = null
    )
    
    /**
     * Summarize an article using Qwen3-4B-Instruct model
     */
    suspend fun summarizeArticle(
        title: String,
        content: String,
        maxRetries: Int = 3
    ): String? {
        return try {
            // Prepare content for BART summarization
            val textToSummarize = prepareContentForSummarization(title, content)
            
            logger.debug("Summarizing article: {} (content length: {})", title, content.length)
            
            for (attempt in 1..maxRetries) {
                try {
                    val response = httpClient.post(baseUrl) {
                        header("Authorization", "Bearer $apiToken")
                        contentType(ContentType.Application.Json)
                        setBody(SummarizationRequest(inputs = textToSummarize))
                    }
                    
                    if (response.status == HttpStatusCode.ServiceUnavailable) {
                        // Model is loading, wait and retry
                        logger.debug("Model loading, waiting 20 seconds before retry $attempt/$maxRetries")
                        delay(20000)
                        continue
                    }
                    
                    if (!response.status.isSuccess()) {
                        logger.warn("Hugging Face API error (attempt $attempt/$maxRetries): ${response.status}")
                        if (attempt < maxRetries) {
                            delay(2000) // Wait before retry
                            continue
                        }
                        return null
                    }
                    
                    val apiResponse = response.body<List<SummarizationResponse>>()
                    val summaryText = apiResponse.firstOrNull()?.summary_text?.trim()
                    
                    if (!summaryText.isNullOrBlank()) {
                        logger.debug("Successfully summarized article: {}", title)
                        return cleanupSummary(summaryText)
                    } else {
                        logger.warn("Empty generation received for article: {}", title)
                    }
                    
                } catch (e: Exception) {
                    when (e) {
                        is java.net.UnknownHostException -> {
                            logger.error("DNS resolution failed for Hugging Face API: ${e.message}")
                        }
                        is java.net.ConnectException -> {
                            logger.error("Connection failed to Hugging Face API: ${e.message}")
                        }
                        is java.nio.channels.UnresolvedAddressException -> {
                            logger.error("Address resolution failed for Hugging Face API: ${e.message}")
                        }
                        is io.ktor.client.network.sockets.ConnectTimeoutException -> {
                            logger.error("Connection timeout to Hugging Face API: ${e.message}")
                        }
                        else -> {
                            logger.warn("Error in summarization attempt $attempt/$maxRetries for article '$title': ${e::class.simpleName} - ${e.message}", e)
                        }
                    }
                    if (attempt < maxRetries) {
                        delay(2000)
                        continue
                    }
                }
            }
            
            null
        } catch (e: Exception) {
            logger.error("Failed to summarize article '$title'", e)
            null
        }
    }
    
    /**
     * Prepare content for BART summarization
     */
    private fun prepareContentForSummarization(title: String, content: String): String {
        // Limit content to avoid token limits for BART (512 tokens ≈ 2048 characters)
        val maxLength = 2000
        val cleanContent = content
            .replace(Regex("<[^>]*>"), "") // Remove HTML
            .replace(Regex("\\s+"), " ") // Normalize whitespace
            .trim()
        
        val fullText = "$title. $cleanContent"
        
        return if (fullText.length > maxLength) {
            fullText.take(maxLength) + "..."
        } else {
            fullText
        }
    }
    
    /**
     * Detect the type of content for better summarization
     */
    private fun detectContentType(title: String, content: String): ArticleType {
        val titleLower = title.lowercase()
        val contentLower = content.lowercase()
        
        return when {
            titleLower.contains(Regex("\\b(show hn:|github|repository|project)\\b")) || 
            contentLower.contains(Regex("\\b(github\\.com|repository|open source|project)\\b")) -> ArticleType.PROJECT
            
            titleLower.contains(Regex("\\b(release|version|update|v\\d|launched)\\b")) ||
            contentLower.contains(Regex("\\b(released|version|update|changelog|new features)\\b")) -> ArticleType.RELEASE
            
            titleLower.contains(Regex("\\b(tutorial|guide|how to|learn|course)\\b")) ||
            contentLower.contains(Regex("\\b(tutorial|step by step|learn|guide)\\b")) -> ArticleType.TUTORIAL
            
            titleLower.contains(Regex("\\b(api|protocol|framework|library|sdk)\\b")) ||
            contentLower.contains(Regex("\\b(api|protocol|framework|library|integration)\\b")) -> ArticleType.TECHNICAL
            
            titleLower.contains(Regex("\\b(startup|funding|acquisition|company)\\b")) ||
            contentLower.contains(Regex("\\b(funding|investment|acquired|startup)\\b")) -> ArticleType.BUSINESS
            
            else -> ArticleType.GENERAL
        }
    }
    
    /**
     * Get specific guidance based on content type
     */
    private fun getSummaryGuidance(articleType: ArticleType): String {
        return when (articleType) {
            ArticleType.PROJECT -> "For project/repository content: Focus on what problem it solves, key technologies used, and practical applications."
            ArticleType.RELEASE -> "For releases/updates: Highlight new features, improvements, and impact on developers."
            ArticleType.TUTORIAL -> "For tutorials/guides: Summarize what developers will learn and the key concepts covered."
            ArticleType.TECHNICAL -> "For technical content: Focus on the technical innovation, use cases, and developer benefits."
            ArticleType.BUSINESS -> "For business content: Highlight the market impact and implications for the tech industry."
            ArticleType.GENERAL -> "Focus on the main insight or development and its relevance to the tech community."
        }
    }
    
    private enum class ArticleType {
        PROJECT, RELEASE, TUTORIAL, TECHNICAL, BUSINESS, GENERAL
    }
    
    /**
     * Extract summary from generated text by removing the prompt
     */
    private fun extractSummaryFromGeneration(generatedText: String, originalPrompt: String): String {
        // Remove the original prompt from the generated text
        val summary = generatedText.removePrefix(originalPrompt).trim()
        
        // Clean up any remaining chat markers
        return summary
            .removePrefix("<|im_start|>assistant")
            .removePrefix("assistant")
            .removePrefix("\n")
            .trim()
    }
    
    /**
     * Clean up the generated summary by removing generic prefixes and improving quality
     */
    private fun cleanupSummary(summary: String): String {
        return summary
            // Remove common generic prefixes
            .replace(Regex("^(Summary:|Article Summary:|Here's a summary:|The article|This article|The post|This post|Reddit post about)\\s*:?\\s*", RegexOption.IGNORE_CASE), "")
            // Remove redundant phrases
            .replace(Regex("\\b(discusses|explains|talks about|describes|covers|explores)\\b", RegexOption.IGNORE_CASE), "presents")
            // Normalize whitespace
            .replace(Regex("\\s+"), " ")
            .trim()
            .let { cleaned ->
                // Ensure it starts with capital letter
                if (cleaned.isNotEmpty()) {
                    cleaned.replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }
                } else cleaned
            }
            .let { cleaned ->
                // Ensure it ends with proper punctuation
                if (cleaned.isNotEmpty() && !(cleaned.endsWith(".") || cleaned.endsWith("!") || cleaned.endsWith("?"))) {
                    "$cleaned."
                } else {
                    cleaned
                }
            }
    }
    
    /**
     * Test the Hugging Face connection
     */
    suspend fun testConnection(): Boolean {
        return try {
            val testText = "This is a simple test to check if the API connection is working properly for summarization."
            
            val response = httpClient.post(baseUrl) {
                header("Authorization", "Bearer $apiToken")
                contentType(ContentType.Application.Json)
                setBody(SummarizationRequest(
                    inputs = testText,
                    parameters = SummarizationParameters(
                        max_length = 50,
                        min_length = 10
                    )
                ))
            }
            
            if (response.status == HttpStatusCode.ServiceUnavailable) {
                logger.info("Hugging Face model is loading, connection available")
                return true
            }
            
            response.status.isSuccess()
        } catch (e: Exception) {
            when (e) {
                is java.net.UnknownHostException -> {
                    logger.error("DNS resolution failed for Hugging Face API: ${e.message}")
                }
                is java.net.ConnectException -> {
                    logger.error("Connection failed to Hugging Face API: ${e.message}")
                }
                is java.nio.channels.UnresolvedAddressException -> {
                    logger.error("Address resolution failed for Hugging Face API: ${e.message}")
                }
                is io.ktor.client.network.sockets.ConnectTimeoutException -> {
                    logger.error("Connection timeout to Hugging Face API: ${e.message}")
                }
                else -> {
                    logger.error("Failed to test Hugging Face connection: ${e::class.simpleName} - ${e.message}", e)
                }
            }
            false
        }
    }
    
    /**
     * Close HTTP client
     */
    fun close() {
        httpClient.close()
    }
}