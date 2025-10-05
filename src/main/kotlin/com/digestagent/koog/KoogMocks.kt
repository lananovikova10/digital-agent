package com.digestagent.koog

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

/**
 * Mock implementations of Koog API to demonstrate migration structure
 * When actual Koog library is available, replace these with real imports
 */

@Target(AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
annotation class KoogTool(
    val name: String,
    val description: String
)

// Mock OpenAI Models
object OpenAIModels {
    object Chat {
        const val GPT4o = "gpt-4o"
        const val GPT4oMini = "gpt-4o-mini"
        const val GPT35Turbo = "gpt-3.5-turbo"
    }
}

// Mock Executor
interface AIExecutor {
    suspend fun execute(prompt: String, model: String): String
}

fun simpleOpenAIExecutor(apiKey: String): AIExecutor {
    return MockOpenAIExecutor(apiKey)
}

class MockOpenAIExecutor(private val apiKey: String) : AIExecutor {
    override suspend fun execute(prompt: String, model: String): String {
        // In a real implementation, this would call OpenAI API
        // For demo purposes, return a mock response
        return """
            # Weekly Intelligence Report
            
            Based on the analysis of articles related to your topics, here are the key insights:
            
            ## Key Insights
            1. Strong growth in AI adoption across startup ecosystem
            2. Increased funding activity in fintech sector
            3. Machine learning applications expanding into new domains
            
            ## Top Articles
            - AI Startup Raises Series A: Promising AI startup focused on machine learning applications secured $10M
            - Latest developments in AI from HackerNews
            - AI Tools and Products from ProductHunt
            
            ## Trends
            - Increasing focus on AI (2 more mentions)
            - Steady coverage across all monitored topics
            
            This report demonstrates the structure of a Koog-migrated agent.
            In the actual implementation, this would use real AI processing.
        """.trimIndent()
    }
}

// Mock AI Agent
class AIAgent(
    private val executor: AIExecutor,
    private val systemPrompt: String,
    private val llmModel: String,
    private val tools: List<Any> = emptyList() // Simplified for demo
) {
    suspend fun run(prompt: String): String {
        // In real Koog implementation, this would:
        // 1. Process the system prompt
        // 2. Use tools as needed
        // 3. Generate response with LLM
        
        // For demo, just use the executor
        return executor.execute(prompt, llmModel)
    }
    
    fun streamAsFlow(prompt: String): Flow<String> = flow {
        // Mock streaming - in real Koog this would stream from LLM
        val response = executor.execute(prompt, llmModel)
        val chunks = response.split(" ")
        
        for (chunk in chunks) {
            emit("$chunk ")
            kotlinx.coroutines.delay(50) // Simulate streaming delay
        }
    }
}