package com.digestagent

import com.digestagent.agent.WeeklyIntelAgent
import com.digestagent.config.Configuration
import com.digestagent.telegram.TelegramNotifier
import kotlinx.coroutines.runBlocking
import org.slf4j.LoggerFactory
import kotlin.system.exitProcess

/**
 * Main entry point for the Digest Agent Koog migration
 */
fun main(args: Array<String>) = runBlocking {
    val logger = LoggerFactory.getLogger("DigestAgent")
    
    try {
        logger.info("Starting Digest Agent (Koog Version)")
        
        // Validate configuration
        Configuration.validate()
        
        // Parse command line arguments
        var topics = mutableListOf<String>()
        var telegramChatId: String? = null
        var postToTelegram = false
        
        var i = 0
        while (i < args.size) {
            when (args[i]) {
                "--telegram" -> {
                    postToTelegram = true
                    // Check if next argument looks like a chat ID (negative number or long positive number)
                    if (i + 1 < args.size && !args[i + 1].startsWith("--")) {
                        val nextArg = args[i + 1]
                        if (nextArg.matches(Regex("^-?\\d+$")) && (nextArg.toLongOrNull() != null)) {
                            // It's a chat ID
                            telegramChatId = nextArg
                            i++
                        }
                    }
                }
                else -> {
                    if (!args[i].startsWith("--")) {
                        topics.add(args[i])
                    }
                }
            }
            i++
        }
        
        // Use default topics if none provided
        if (topics.isEmpty()) {
            topics = mutableListOf("AI", "machine learning", "startup funding", "fintech")
        }
        
        logger.info("Initializing Weekly Intelligence Agent...")
        val agent = WeeklyIntelAgent(Configuration.openAIApiKey)
        
        logger.info("Running weekly intelligence workflow for topics: {}", topics)
        
        // Run the main workflow
        val report = agent.runWeeklyIntel(topics)
        
        // Save report to file with timestamp
        val timestamp = java.time.LocalDateTime.now().format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"))
        val filename = "weekly_report_$timestamp.md"
        java.io.File(filename).writeText(report)
        
        // Post to Telegram if requested
        if (postToTelegram) {
            val botToken = Configuration.telegramBotToken
            if (botToken != null) {
                // Use command-line chat ID if provided, otherwise use default from .env
                val effectiveChatId = telegramChatId ?: Configuration.telegramChatId
                
                if (effectiveChatId != null) {
                    val notifier = TelegramNotifier(botToken)
                    val success = notifier.postReport(report, effectiveChatId)
                    if (success) {
                        logger.info("Report posted to Telegram successfully to chat: {}", effectiveChatId)
                        println("📱 Report posted to Telegram (Chat: $effectiveChatId)")
                    } else {
                        logger.warn("Failed to post report to Telegram")
                        println("⚠️  Failed to post report to Telegram")
                    }
                } else {
                    logger.warn("Telegram posting requested but no chat ID provided and TG_CHAT_ID not configured")
                    println("⚠️  No Telegram chat ID found. Add TG_CHAT_ID to .env or provide via --telegram CHAT_ID")
                }
            } else {
                logger.warn("Telegram posting requested but TG_BOT_KEY not configured")
                println("⚠️  Telegram posting requested but TG_BOT_KEY not found in environment")
            }
        }
        
        // Output the report
        println("\n" + "=".repeat(80))
        println("WEEKLY INTELLIGENCE REPORT (Koog Version)")
        println("=".repeat(80))
        println(report)
        println("=".repeat(80))
        
        logger.info("Weekly intelligence workflow completed successfully")
        logger.info("Report saved to: {}", filename)
        
    } catch (e: Exception) {
        logger.error("Weekly intelligence workflow failed", e)
        println("\nError: ${e.message}")
        exitProcess(1)
    }
}

/**
 * Alternative main function for streaming reports
 */
suspend fun mainWithStreaming(topics: List<String>) {
    val logger = LoggerFactory.getLogger("DigestAgent.Streaming")
    
    try {
        Configuration.validate()
        
        val agent = WeeklyIntelAgent(Configuration.openAIApiKey)
        
        println("\n" + "=".repeat(80))
        println("STREAMING WEEKLY INTELLIGENCE REPORT")
        println("=".repeat(80))
        
        val report = agent.runWeeklyIntelWithStreaming(topics) { chunk ->
            print(chunk)
            System.out.flush()
        }
        
        println("\n" + "=".repeat(80))
        logger.info("Streaming report completed")
        
    } catch (e: Exception) {
        logger.error("Streaming workflow failed", e)
        throw e
    }
}

/**
 * Demo function showing different usage patterns
 */
suspend fun demo() {
    val agent = WeeklyIntelAgent(Configuration.openAIApiKey)
    
    // Standard workflow
    println("=== Standard Workflow ===")
    val standardReport = agent.runWeeklyIntel(listOf("AI", "startups"))
    println(standardReport.take(200) + "...")
    
    // Focused analysis
    println("\n=== Focused Analysis ===")
    val focusedReport = agent.runFocusedAnalysis(
        topics = listOf("AI", "machine learning"),
        focusArea = "investment trends",
        maxArticles = 15
    )
    println(focusedReport.take(200) + "...")
    
    // Streaming workflow
    println("\n=== Streaming Workflow ===")
    agent.runWeeklyIntelWithStreaming(listOf("fintech")) { chunk ->
        // In a real app, this could update a UI or send to a websocket
        if (chunk.contains("insight") || chunk.contains("trend")) {
            println("📊 $chunk")
        }
    }
}