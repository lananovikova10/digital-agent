package com.digestagent.telegram

import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.client.request.forms.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.delay
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import org.slf4j.LoggerFactory

/**
 * Telegram notification service for posting reports
 */
class TelegramNotifier(
    private val botToken: String,
    private val chatId: String? = null
) {
    private val logger = LoggerFactory.getLogger(TelegramNotifier::class.java)
    
    private val httpClient = HttpClient(CIO) {
        install(ContentNegotiation) {
            json(Json {
                ignoreUnknownKeys = true
                isLenient = true
            })
        }
    }
    
    private val baseUrl = "https://api.telegram.org/bot$botToken"
    
    @Serializable
    data class TelegramResponse(
        val ok: Boolean,
        val description: String? = null
    )
    
    @Serializable
    data class TelegramUser(
        val id: Long,
        val is_bot: Boolean,
        val first_name: String,
        val username: String? = null
    )
    
    @Serializable
    data class GetMeResponse(
        val ok: Boolean,
        val result: TelegramUser? = null,
        val description: String? = null
    )
    
    /**
     * Posts a report to Telegram
     */
    suspend fun postReport(report: String, targetChatId: String? = null): Boolean {
        return try {
            val effectiveChatId = targetChatId ?: chatId
            if (effectiveChatId == null) {
                logger.error("No chat ID provided for Telegram posting")
                return false
            }
            
            logger.info("Posting report to Telegram chat: {}", effectiveChatId)
            
            // Split report into chunks if too long (Telegram has a 4096 character limit)
            val chunks = splitReportIntoChunks(report)
            
            for ((index, chunk) in chunks.withIndex()) {
                val message = if (chunks.size > 1) {
                    "📊 Weekly Intelligence Report (Part ${index + 1}/${chunks.size})\n\n$chunk"
                } else {
                    "📊 Weekly Intelligence Report\n\n$chunk"
                }
                
                val response = httpClient.post("$baseUrl/sendMessage") {
                    contentType(ContentType.Application.FormUrlEncoded)
                    setBody(FormDataContent(Parameters.build {
                        append("chat_id", effectiveChatId)
                        append("text", message)
                        // Don't use parse_mode to avoid Markdown formatting issues
                    }))
                }
                
                if (!response.status.isSuccess()) {
                    logger.error("Failed to send message part ${index + 1}. Status: ${response.status}")
                    return false
                }
                
                // Add small delay between messages to avoid rate limiting
                if (index < chunks.size - 1) {
                    delay(1000)
                }
            }
            
            logger.info("Successfully posted report to Telegram")
            true
        } catch (e: Exception) {
            logger.error("Failed to post report to Telegram", e)
            false
        }
    }
    
    /**
     * Splits a report into chunks that fit within Telegram's message length limit
     */
    private fun splitReportIntoChunks(report: String, maxLength: Int = 4000): List<String> {
        if (report.length <= maxLength) {
            return listOf(report)
        }
        
        val chunks = mutableListOf<String>()
        var currentChunk = ""
        val lines = report.split('\n')
        
        for (line in lines) {
            if ((currentChunk + line + '\n').length > maxLength) {
                if (currentChunk.isNotEmpty()) {
                    chunks.add(currentChunk.trim())
                    currentChunk = ""
                }
                
                // If a single line is too long, split it
                if (line.length > maxLength) {
                    var remainingLine = line
                    while (remainingLine.length > maxLength) {
                        chunks.add(remainingLine.substring(0, maxLength))
                        remainingLine = remainingLine.substring(maxLength)
                    }
                    if (remainingLine.isNotEmpty()) {
                        currentChunk = remainingLine + '\n'
                    }
                } else {
                    currentChunk = line + '\n'
                }
            } else {
                currentChunk += line + '\n'
            }
        }
        
        if (currentChunk.isNotEmpty()) {
            chunks.add(currentChunk.trim())
        }
        
        return chunks
    }
    
    /**
     * Tests the Telegram connection
     */
    suspend fun testConnection(): Boolean {
        return try {
            val response = httpClient.get("$baseUrl/getMe")
            val getMeResponse = response.body<GetMeResponse>()
            
            if (getMeResponse.ok && getMeResponse.result != null) {
                val user = getMeResponse.result
                logger.info("Successfully connected to Telegram bot: {} ({})", 
                    user.username ?: user.first_name, user.id)
                true
            } else {
                logger.error("Failed to get bot info: {}", getMeResponse.description)
                false
            }
        } catch (e: Exception) {
            logger.error("Failed to connect to Telegram bot", e)
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