package com.digestagent

import com.digestagent.config.Configuration
import com.digestagent.telegram.TelegramNotifier
import kotlinx.coroutines.runBlocking
import org.slf4j.LoggerFactory
import kotlin.system.exitProcess

/**
 * Telegram bot testing utility
 * This helps debug Telegram connectivity and get chat IDs
 */
fun main(args: Array<String>) = runBlocking {
    val logger = LoggerFactory.getLogger("TelegramTest")
    
    try {
        logger.info("Starting Telegram Bot Test")
        
        val botToken = Configuration.telegramBotToken
        if (botToken == null) {
            println("❌ TG_BOT_KEY not found in environment variables")
            println("Please add TG_BOT_KEY to your .env file")
            exitProcess(1)
        }
        
        println("🤖 Testing Telegram Bot Connection...")
        println("Bot Token: ${botToken.take(10)}...")
        
        val notifier = TelegramNotifier(botToken)
        
        // Test bot connection
        val connectionTest = notifier.testConnection()
        if (!connectionTest) {
            println("❌ Failed to connect to Telegram bot")
            exitProcess(1)
        }
        
        println("✅ Successfully connected to Telegram bot")
        
        // If chat ID is provided as argument, test sending a message
        if (args.isNotEmpty()) {
            val chatId = args[0]
            println("📱 Testing message send to chat ID: $chatId")
            
            val testMessage = """
                🧪 **Telegram Bot Test**
                
                This is a test message from your Digest Agent.
                
                If you can see this message, your bot is working correctly!
                
                Time: ${java.time.LocalDateTime.now()}
            """.trimIndent()
            
            val success = notifier.postReport(testMessage, chatId)
            if (success) {
                println("✅ Test message sent successfully!")
                println("💡 Add this chat ID to your .env file: TG_CHAT_ID=$chatId")
            } else {
                println("❌ Failed to send test message")
                println("🔍 Common issues:")
                println("   1. Chat ID might be incorrect")
                println("   2. Bot might not be added to the group/chat")
                println("   3. Bot might not have permission to send messages")
            }
        } else {
            println("📋 To test message sending, run:")
            println("   ./gradlew run -PmainClass=com.digestagent.TelegramTestKt --args=\"CHAT_ID\"")
            println()
            println("🔍 To find your chat ID:")
            println("   1. Add your bot to a group")
            println("   2. Send a message in the group")
            println("   3. Visit: https://api.telegram.org/bot${botToken}/getUpdates")
            println("   4. Look for 'chat':{'id': YOUR_CHAT_ID} in the response")
        }
        
    } catch (e: Exception) {
        logger.error("Telegram test failed", e)
        println("❌ Error: ${e.message}")
        exitProcess(1)
    }
}