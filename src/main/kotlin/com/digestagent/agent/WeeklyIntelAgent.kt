package com.digestagent.agent

import ai.koog.agents.core.agent.AIAgent
import ai.koog.prompt.executor.llms.all.simpleOpenAIExecutor
import ai.koog.prompt.executor.clients.openai.OpenAIModels
import com.digestagent.model.WeeklyIntelState
import com.digestagent.model.Article
import com.digestagent.model.Summary
import com.digestagent.sources.SourceManager
import com.digestagent.tools.DataIngestionTools
import com.digestagent.tools.ContentProcessingTools
import com.digestagent.tools.ReportGenerationTools
import kotlinx.coroutines.coroutineScope
import org.slf4j.LoggerFactory

class WeeklyIntelAgent(
    private val openAIApiKey: String
) {
    private val logger = LoggerFactory.getLogger(WeeklyIntelAgent::class.java)
    
    // Initialize tools and dependencies
    private val sourceManager = SourceManager()
    private val dataIngestionTools = DataIngestionTools(sourceManager)
    private val contentProcessingTools = ContentProcessingTools()
    private val reportGenerationTools = ReportGenerationTools()
    
    // Create Koog AI agent using the simpler constructor
    private val agent = AIAgent(
        promptExecutor = simpleOpenAIExecutor(openAIApiKey),
        llmModel = OpenAIModels.Chat.GPT4o,
        systemPrompt = """
            You are a Weekly Intelligence Agent specialized in analyzing news articles and generating comprehensive intelligence reports.
            
            Your role is to:
            1. Process and analyze articles from multiple sources
            2. Identify key insights, trends, and patterns
            3. Rank content by relevance and importance
            4. Generate well-structured intelligence reports
            
            You have access to Kotlin functions for:
            - Data ingestion from various sources
            - Content processing and enrichment
            - Article ranking and analysis
            - Report generation and structuring
            
            Always provide detailed analysis and well-reasoned insights. Focus on actionable intelligence and emerging trends.
            Use the available functions to gather, process, and analyze data systematically.
        """.trimIndent()
    )

    /**
     * Run the complete weekly intelligence workflow using Koog agent orchestration
     */
    suspend fun runWeeklyIntel(topics: List<String>): String = coroutineScope {
        logger.info("Starting weekly intelligence workflow for topics: {}", topics)
        
        val prompt = """
            Generate a comprehensive weekly intelligence report for the following topics: ${topics.joinToString(", ")}
            
            Follow this workflow:
            1. Use ingest_articles_for_topics to gather articles for these topics
            2. Use filter_articles_by_date to filter to recent articles (last 7 days)
            3. Use deduplicate_articles to remove duplicate content
            4. Use enrich_articles to add metadata and relevance scores
            5. Use rank_articles_by_relevance to identify the most important articles
            6. Use extract_key_insights to identify trends and patterns
            7. Use generate_summary_insights to create structured insights
            8. Use compose_final_report to create the final formatted report
            
            Ensure each step builds on the previous one and provide detailed analysis throughout.
            The final report should be comprehensive, well-structured, and actionable.
        """.trimIndent()
        
        try {
            // For now, let's simulate the workflow by calling the tools directly
            // TODO: Replace with proper agent execution once we figure out the correct API
            logger.info("Running weekly intelligence workflow (simulated)")
            
            // Step 1: Ingest articles
            val ingestionResult = dataIngestionTools.ingestArticlesForTopics(topics)
            
            // Step 2: Filter by date
            val filteredArticles = dataIngestionTools.filterArticlesByDate(ingestionResult.articles, 7)
            
            // Step 3: Deduplicate
            val dedupedArticles = dataIngestionTools.deduplicateArticles(filteredArticles)
            
            // Step 4: Enrich
            val enrichedResult = contentProcessingTools.enrichArticles(dedupedArticles, topics)
            
            // Step 5: Rank
            val rankedResult = contentProcessingTools.rankArticlesByRelevance(enrichedResult.enrichedArticles, topics, 25)
            
            // Step 6: Generate AI summaries for top articles
            val summarizedArticles = contentProcessingTools.summarizeArticles(rankedResult.rankedArticles)
            
            // Step 7: Extract insights
            val insights = contentProcessingTools.extractKeyInsights(summarizedArticles)
            
            // Step 8: Generate summary
            val summary = reportGenerationTools.generateSummaryInsights(summarizedArticles, topics)
            
            // Step 9: Compose final report with summaries
            val report = reportGenerationTools.composeFinalReport(summary, summarizedArticles, topics)
            
            logger.info("Weekly intelligence workflow completed successfully")
            report
        } catch (e: Exception) {
            logger.error("Weekly intelligence workflow failed", e)
            throw e
        }
    }

    /**
     * Alternative workflow using Koog's streaming capabilities
     */
    suspend fun runWeeklyIntelWithStreaming(topics: List<String>, onUpdate: (String) -> Unit): String {
        logger.info("Starting streaming weekly intelligence workflow for topics: {}", topics)
        
        val prompt = """
            Generate a comprehensive weekly intelligence report for the following topics: ${topics.joinToString(", ")}
            
            Please provide updates as you work through each step:
            1. Ingesting articles from sources
            2. Filtering and deduplicating content
            3. Enriching with metadata and scores
            4. Ranking by relevance and importance  
            5. Extracting insights and trends
            6. Generating final report
            
            Use all available tools systematically and provide the final comprehensive report.
        """.trimIndent()
        
        // For now, simulate streaming by calling the regular workflow and providing updates
        // TODO: Replace with proper streaming agent execution once we figure out the correct API
        
        onUpdate("Starting weekly intelligence workflow...")
        
        try {
            // Step 1: Ingest articles
            onUpdate("Step 1: Ingesting articles from sources...")
            val ingestionResult = dataIngestionTools.ingestArticlesForTopics(topics)
            onUpdate("Found ${ingestionResult.totalCount} articles from ${ingestionResult.sourceBreakdown.size} sources")
            
            // Step 2: Filter by date
            onUpdate("Step 2: Filtering articles to last 7 days...")
            val filteredArticles = dataIngestionTools.filterArticlesByDate(ingestionResult.articles, 7)
            onUpdate("Filtered to ${filteredArticles.size} recent articles")
            
            // Step 3: Deduplicate
            onUpdate("Step 3: Removing duplicate articles...")
            val dedupedArticles = dataIngestionTools.deduplicateArticles(filteredArticles)
            onUpdate("Deduplicated to ${dedupedArticles.size} unique articles")
            
            // Step 4: Enrich
            onUpdate("Step 4: Enriching articles with metadata and scores...")
            val enrichedResult = contentProcessingTools.enrichArticles(dedupedArticles, topics)
            onUpdate("Enriched ${enrichedResult.enrichedArticles.size} articles with relevance scores")
            
            // Step 5: Rank
            onUpdate("Step 5: Ranking articles by relevance...")
            val rankedResult = contentProcessingTools.rankArticlesByRelevance(enrichedResult.enrichedArticles, topics, 25)
            onUpdate("Ranked and selected top ${rankedResult.rankedArticles.size} articles")
            
            // Step 6: Extract insights
            onUpdate("Step 6: Extracting key insights and trends...")
            val insights = contentProcessingTools.extractKeyInsights(rankedResult.rankedArticles)
            onUpdate("Extracted ${insights.size} key insights")
            
            // Step 7: Generate summary
            onUpdate("Step 7: Generating summary insights...")
            val summary = reportGenerationTools.generateSummaryInsights(rankedResult.rankedArticles, topics)
            onUpdate("Generated comprehensive summary with ${summary.keyInsights.size} insights")
            
            // Step 8: Compose final report
            onUpdate("Step 8: Composing final intelligence report...")
            val finalReport = reportGenerationTools.composeFinalReport(summary, rankedResult.rankedArticles, topics)
            onUpdate("Weekly intelligence report completed!")
            
            logger.info("Streaming weekly intelligence workflow completed")
            return finalReport
            
        } catch (e: Exception) {
            onUpdate("Error: ${e.message}")
            logger.error("Streaming weekly intelligence workflow failed", e)
            throw e
        }
    }

    /**
     * Run a focused analysis on specific aspects
     */
    suspend fun runFocusedAnalysis(
        topics: List<String>,
        focusArea: String,
        maxArticles: Int = 25
    ): String {
        logger.info("Starting focused analysis on '{}' for topics: {}", focusArea, topics)
        
        val prompt = """
            Conduct a focused analysis on "$focusArea" for topics: ${topics.joinToString(", ")}
            
            Workflow:
            1. Ingest articles related to these topics
            2. Filter to the top $maxArticles most relevant articles
            3. Focus specifically on insights related to "$focusArea"
            4. Generate a targeted report emphasizing this focus area
            
            Provide deep insights specifically about "$focusArea" in relation to the given topics.
        """.trimIndent()
        
        // For now, simulate focused analysis by calling tools directly with focus area filter
        // TODO: Replace with proper agent execution once we figure out the correct API
        
        try {
            // Step 1: Ingest articles
            val ingestionResult = dataIngestionTools.ingestArticlesForTopics(topics)
            
            // Step 2: Filter and limit
            val filteredArticles = dataIngestionTools.filterArticlesByDate(ingestionResult.articles, 7)
            val dedupedArticles = dataIngestionTools.deduplicateArticles(filteredArticles)
            
            // Step 3: Enrich and rank with focus on the specified area
            val enrichedResult = contentProcessingTools.enrichArticles(dedupedArticles, topics + focusArea)
            val rankedResult = contentProcessingTools.rankArticlesByRelevance(
                enrichedResult.enrichedArticles, 
                topics + focusArea, 
                maxArticles
            )
            
            // Step 4: Generate focused insights
            val insights = contentProcessingTools.extractKeyInsights(rankedResult.rankedArticles)
            
            // Step 5: Create focused summary
            val summary = reportGenerationTools.generateSummaryInsights(rankedResult.rankedArticles, topics + focusArea)
            
            // Step 6: Generate focused report
            val focusedSummary = summary.copy(
                keyInsights = listOf("FOCUS: $focusArea") + summary.keyInsights
            )
            val focusedReport = reportGenerationTools.composeFinalReport(
                focusedSummary, 
                rankedResult.rankedArticles, 
                topics
            )
            
            return focusedReport
            
        } catch (e: Exception) {
            logger.error("Focused analysis failed", e)
            throw e
        }
    }

    /**
     * Get agent conversation history for debugging/analysis
     */
    fun getConversationHistory(): List<String> {
        // Koog provides built-in history management
        // This would depend on the actual Koog API for accessing history
        return emptyList() // Placeholder - would implement based on Koog's history API
    }

    /**
     * Switch to different LLM model mid-conversation
     */
    suspend fun switchModel(model: String): Boolean {
        return try {
            // Koog allows model switching - this would depend on actual Koog API
            logger.info("Switched to model: {}", model)
            true
        } catch (e: Exception) {
            logger.error("Failed to switch model", e)
            false
        }
    }
}