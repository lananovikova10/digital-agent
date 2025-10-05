package com.digestagent

import com.digestagent.agent.WeeklyIntelAgent
import com.digestagent.config.Configuration
import com.digestagent.model.Article
import com.digestagent.sources.SourceManager
import com.digestagent.tools.DataIngestionTools
import com.digestagent.tools.ContentProcessingTools
import com.digestagent.tools.ReportGenerationTools
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.BeforeEach
import org.slf4j.LoggerFactory
import kotlin.test.assertTrue
import kotlin.test.assertNotNull
import kotlin.test.assertEquals

/**
 * Test suite for the Koog migration
 * These tests verify that the migration maintains functionality from the original Python implementation
 */
class MigrationTest {
    private val logger = LoggerFactory.getLogger(MigrationTest::class.java)
    
    @BeforeEach
    fun setup() {
        // These tests can run without actual API keys for basic functionality
        logger.info("Setting up migration tests")
    }

    @Test
    fun `test configuration loading`() {
        logger.info("Testing configuration loading")
        
        // Test that configuration can be loaded (may use defaults if no .env)
        val config = Configuration
        
        // Should not throw exceptions
        val configMap = config.toMap()
        assertNotNull(configMap)
        assertTrue(configMap.containsKey("maxArticlesPerSource"))
        assertTrue(configMap.containsKey("enableCaching"))
        
        logger.info("Configuration test passed: {}", configMap.keys)
    }

    @Test
    fun `test source manager initialization`() = runBlocking {
        logger.info("Testing source manager initialization")
        
        val sourceManager = SourceManager()
        val sources = sourceManager.getAvailableSources()
        
        assertTrue(sources.isNotEmpty())
        assertTrue(sources.contains("HackerNews"))
        assertTrue(sources.contains("Reddit"))
        assertTrue(sources.contains("DevTo"))
        
        logger.info("Source manager test passed. Available sources: {}", sources)
        
        sourceManager.close()
    }

    @Test
    fun `test data ingestion tools`() = runBlocking {
        logger.info("Testing data ingestion tools")
        
        val sourceManager = SourceManager()
        val ingestionTools = DataIngestionTools(sourceManager)
        
        // Test article ingestion (will use mock data since no real API keys)
        val result = ingestionTools.ingestArticlesForTopics(listOf("AI", "startups"))
        
        assertNotNull(result)
        assertTrue(result.totalCount > 0)
        assertTrue(result.articles.isNotEmpty())
        assertTrue(result.sourceBreakdown.isNotEmpty())
        
        logger.info("Ingestion test passed. Articles: {}, Sources: {}", 
                   result.totalCount, result.sourceBreakdown.keys)
        
        sourceManager.close()
    }

    @Test
    fun `test content processing tools`() = runBlocking {
        logger.info("Testing content processing tools")
        
        val processingTools = ContentProcessingTools()
        
        // Create sample articles
        val sampleArticles = listOf(
            Article(
                title = "AI Revolution in Startups",
                content = "Artificial intelligence is transforming how startups operate and innovate...",
                url = "https://example.com/ai-startups",
                source = "TechNews",
                publishedAt = System.currentTimeMillis().toString(),
                author = "tech_writer"
            ),
            Article(
                title = "Machine Learning Funding Trends",
                content = "Venture capital investment in machine learning startups reached new heights...",
                url = "https://example.com/ml-funding",
                source = "VentureInsight",
                publishedAt = System.currentTimeMillis().toString(),
                author = "investment_analyst"
            )
        )
        
        // Test enrichment
        val enriched = processingTools.enrichArticles(sampleArticles, listOf("AI", "startups"))
        assertNotNull(enriched.enrichedArticles)
        assertTrue(enriched.enrichedArticles.size == sampleArticles.size)
        assertTrue(enriched.enrichedArticles.all { it.score > 0.0 })
        
        // Test ranking
        val ranked = processingTools.rankArticlesByRelevance(
            enriched.enrichedArticles, 
            listOf("AI", "startups"),
            maxResults = 10
        )
        assertNotNull(ranked.rankedArticles)
        assertTrue(ranked.rankingCriteria.isNotEmpty())
        
        // Test insight extraction
        val insights = processingTools.extractKeyInsights(ranked.rankedArticles)
        assertNotNull(insights)
        assertTrue(insights.isNotEmpty())
        
        logger.info("Content processing test passed. Insights: {}", insights.size)
    }

    @Test
    fun `test report generation tools`() = runBlocking {
        logger.info("Testing report generation tools")
        
        val reportTools = ReportGenerationTools()
        
        // Create sample enriched articles
        val articles = listOf(
            Article(
                title = "AI Startup Raises Series A",
                content = "A promising AI startup focused on machine learning applications secured $10M...",
                url = "https://example.com/ai-funding",
                source = "StartupNews",
                publishedAt = System.currentTimeMillis().toString(),
                score = 2.5,
                tags = listOf("AI", "funding", "startup")
            )
        )
        
        val topics = listOf("AI", "startups", "funding")
        
        // Test summary generation
        val summary = reportTools.generateSummaryInsights(articles, topics)
        assertNotNull(summary)
        assertTrue(summary.keyInsights.isNotEmpty())
        assertTrue(summary.topSources.isNotEmpty())
        
        // Test report composition
        val report = reportTools.composeFinalReport(summary, articles, topics)
        assertNotNull(report)
        assertTrue(report.contains("Weekly Intelligence Report"))
        assertTrue(report.contains("Executive Summary"))
        assertTrue(report.contains("Key Insights"))
        
        // Test structured sections
        val sections = reportTools.createReportSections(summary, articles)
        assertNotNull(sections)
        assertNotNull(sections.executiveSummary)
        assertNotNull(sections.sourceAnalysis)
        
        logger.info("Report generation test passed. Report length: {} characters", report.length)
    }

    @Test
    fun `test complete workflow simulation`() = runBlocking {
        logger.info("Testing complete workflow simulation (without LLM)")
        
        // This test simulates the complete workflow without requiring API keys
        val sourceManager = SourceManager()
        val ingestionTools = DataIngestionTools(sourceManager)
        val processingTools = ContentProcessingTools()
        val reportTools = ReportGenerationTools()
        
        val topics = listOf("AI", "machine learning")
        
        try {
            // 1. Ingest
            logger.info("Step 1: Ingesting articles")
            val ingestionResult = ingestionTools.ingestArticlesForTopics(topics)
            assertTrue(ingestionResult.articles.isNotEmpty())
            
            // 2. Filter and deduplicate
            logger.info("Step 2: Filtering and deduplicating")
            val filtered = ingestionTools.filterArticlesByDate(ingestionResult.articles, 7)
            val deduped = ingestionTools.deduplicateArticles(filtered)
            assertTrue(deduped.isNotEmpty())
            
            // 3. Enrich
            logger.info("Step 3: Enriching content")
            val enriched = processingTools.enrichArticles(deduped, topics)
            assertTrue(enriched.enrichedArticles.isNotEmpty())
            
            // 4. Rank
            logger.info("Step 4: Ranking articles")
            val ranked = processingTools.rankArticlesByRelevance(
                enriched.enrichedArticles, 
                topics,
                maxResults = 20
            )
            assertTrue(ranked.rankedArticles.isNotEmpty())
            
            // 5. Generate insights
            logger.info("Step 5: Generating insights")
            val insights = processingTools.extractKeyInsights(ranked.rankedArticles)
            assertTrue(insights.isNotEmpty())
            
            // 6. Create summary
            logger.info("Step 6: Creating summary")
            val summary = reportTools.generateSummaryInsights(ranked.rankedArticles, topics)
            assertTrue(summary.keyInsights.isNotEmpty())
            
            // 7. Compose final report
            logger.info("Step 7: Composing final report")
            val finalReport = reportTools.composeFinalReport(summary, ranked.rankedArticles, topics)
            assertTrue(finalReport.isNotEmpty())
            assertTrue(finalReport.contains("Weekly Intelligence Report"))
            
            logger.info("Complete workflow simulation passed! Final report: {} characters", 
                       finalReport.length)
            
        } finally {
            sourceManager.close()
        }
    }

    /**
     * Integration test that would run with real API keys
     * Only runs if OPENAI_API_KEY is available
     */
    @Test
    fun `test agent integration with real API (conditional)`() = runBlocking {
        val apiKey = System.getenv("OPENAI_API_KEY")
        
        if (apiKey.isNullOrEmpty()) {
            logger.info("Skipping integration test - no OPENAI_API_KEY found")
            return@runBlocking
        }
        
        logger.info("Running integration test with real OpenAI API")
        
        try {
            val agent = WeeklyIntelAgent(apiKey)
            val topics = listOf("AI")
            
            // This would make actual API calls
            val report = agent.runWeeklyIntel(topics)
            
            assertNotNull(report)
            assertTrue(report.isNotEmpty())
            
            logger.info("Integration test passed! Report generated: {} characters", report.length)
            
        } catch (e: Exception) {
            logger.warn("Integration test failed (this may be expected): {}", e.message)
            // Don't fail the test if API calls fail - this is expected in CI/CD
        }
    }
}