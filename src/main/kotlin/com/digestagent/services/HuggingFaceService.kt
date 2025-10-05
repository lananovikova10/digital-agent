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
    
    // Using Qwen3-4B-Instruct for better contextual summarization
    private val baseUrl = "https://api-inference.huggingface.co/models/Qwen/Qwen3-4B-Instruct-2507"
    
    @Serializable
    data class QwenGenerationRequest(
        val inputs: String,
        val parameters: QwenParameters = QwenParameters()
    )
    
    @Serializable
    data class QwenParameters(
        val max_new_tokens: Int = 200,
        val temperature: Double = 0.3,
        val do_sample: Boolean = true,
        val top_p: Double = 0.9,
        val stop: List<String> = listOf("\n\n", "Human:", "Assistant:")
    )
    
    @Serializable
    data class QwenGenerationResponse(
        val generated_text: String? = null,
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
            // Create a chat prompt for Qwen model
            val chatPrompt = buildQwenSummarizationPrompt(title, content)
            
            logger.debug("Summarizing article: {} (content length: {})", title, content.length)
            
            for (attempt in 1..maxRetries) {
                try {
                    val response = httpClient.post(baseUrl) {
                        header("Authorization", "Bearer $apiToken")
                        contentType(ContentType.Application.Json)
                        setBody(QwenGenerationRequest(inputs = chatPrompt))
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
                    
                    val apiResponse = response.body<List<QwenGenerationResponse>>()
                    val generatedText = apiResponse.firstOrNull()?.generated_text?.trim()
                    
                    if (!generatedText.isNullOrBlank()) {
                        // Extract the summary from the generated text (remove the original prompt)
                        val summary = extractSummaryFromGeneration(generatedText, chatPrompt)
                        if (summary.isNotBlank()) {
                            logger.debug("Successfully summarized article: {}", title)
                            return cleanupSummary(summary)
                        }
                    } else {
                        logger.warn("Empty generation received for article: {}", title)
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
     * Build Qwen chat prompt for summarization
     */
    private fun buildQwenSummarizationPrompt(title: String, content: String): String {
        // Limit content to avoid token limits (~1500 characters for better context)
        val truncatedContent = if (content.length > 1500) {
            content.take(1500) + "..."
        } else {
            content
        }
        
        return """<|im_start|>system
You are a professional news analyst. Summarize the given article in 2-3 concise, informative sentences that capture the main points and key insights. Focus on the most important information and avoid redundancy.
<|im_end|>
<|im_start|>user
Article Title: $title

Article Content: $truncatedContent

Please provide a clear, professional summary:
<|im_end|>
<|im_start|>assistant
"""
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
            val testPrompt = """<|im_start|>system
You are a helpful assistant.
<|im_end|>
<|im_start|>user
Say "Connection successful" to test the API.
<|im_end|>
<|im_start|>assistant
"""
            
            val response = httpClient.post(baseUrl) {
                header("Authorization", "Bearer $apiToken")
                contentType(ContentType.Application.Json)
                setBody(QwenGenerationRequest(
                    inputs = testPrompt,
                    parameters = QwenParameters(
                        max_new_tokens = 10,
                        temperature = 0.1
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