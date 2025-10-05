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
    }
    
    // Using microsoft/DialoGPT-medium for better availability on Inference API
    private val baseUrl = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    
    @Serializable
    data class BartSummarizationRequest(
        val inputs: String,
        val parameters: BartParameters = BartParameters()
    )
    
    @Serializable
    data class BartParameters(
        val max_length: Int = 150,
        val min_length: Int = 30,
        val do_sample: Boolean = false
    )
    
    @Serializable
    data class BartSummarizationResponse(
        val summary_text: String? = null,
        val error: String? = null
    )
    
    /**
     * Summarize an article using BART model
     */
    suspend fun summarizeArticle(
        title: String,
        content: String,
        maxRetries: Int = 3
    ): String? {
        return try {
            // Prepare content for BART summarization (limit to ~1000 characters to avoid token limits)
            val textToSummarize = prepareTextForSummarization(title, content)
            
            logger.debug("Summarizing article: {} (content length: {})", title, content.length)
            
            for (attempt in 1..maxRetries) {
                try {
                    val response = httpClient.post(baseUrl) {
                        header("Authorization", "Bearer $apiToken")
                        contentType(ContentType.Application.Json)
                        setBody(BartSummarizationRequest(inputs = textToSummarize))
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
                    
                    val apiResponse = response.body<List<BartSummarizationResponse>>()
                    val summary = apiResponse.firstOrNull()?.summary_text?.trim()
                    
                    if (!summary.isNullOrBlank()) {
                        logger.debug("Successfully summarized article: {}", title)
                        return cleanupSummary(summary)
                    } else {
                        logger.warn("Empty summary received for article: {}", title)
                    }
                    
                } catch (e: Exception) {
                    logger.warn("Error in summarization attempt $attempt/$maxRetries for article '$title'", e)
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
     * Prepare text for BART summarization
     */
    private fun prepareTextForSummarization(title: String, content: String): String {
        // BART works better with raw text, not prompts
        // Combine title and content, limit to ~1000 characters for better performance
        val combinedText = "$title. $content"
        
        return if (combinedText.length > 1000) {
            combinedText.take(1000).trim()
        } else {
            combinedText
        }
    }
    
    /**
     * Clean up the generated summary
     */
    private fun cleanupSummary(summary: String): String {
        return summary
            .replace(Regex("^(Summary:|Article Summary:|Here's a summary:|The article|This article)\\s*:?\\s*", RegexOption.IGNORE_CASE), "")
            .replace(Regex("\\s+"), " ")
            .trim()
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
            val testText = "This is a test article about artificial intelligence and machine learning. The article discusses various aspects of AI technology and its impact on society."
            
            val response = httpClient.post(baseUrl) {
                header("Authorization", "Bearer $apiToken")
                contentType(ContentType.Application.Json)
                setBody(BartSummarizationRequest(
                    inputs = testText,
                    parameters = BartParameters(
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
            logger.error("Failed to test Hugging Face connection", e)
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