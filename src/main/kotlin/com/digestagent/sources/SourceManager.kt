package com.digestagent.sources

import com.digestagent.model.Article
import com.digestagent.config.Configuration
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.serialization.json.*
import org.slf4j.LoggerFactory

/**
 * Manages data ingestion from various sources (HackerNews, Product Hunt, YC Launches, etc.)
 * This replaces the Python source manager with Kotlin/Ktor HTTP client
 */
class SourceManager {
    private val logger = LoggerFactory.getLogger(SourceManager::class.java)
    
    private val httpClient = HttpClient(CIO) {
        install(ContentNegotiation) {
            json(Json {
                ignoreUnknownKeys = true
                isLenient = true
            })
        }
    }
    
    private val sources = listOf(
        HackerNewsSource(),
        RedditSource(),
        DevToSource()
    )

    /**
     * Fetch articles from all sources for a given topic
     */
    suspend fun fetchAllSources(topic: String): List<Article> = coroutineScope {
        logger.info("Fetching articles for topic: {} from {} sources", topic, sources.size)
        
        val jobs = sources.map { source ->
            async {
                try {
                    source.fetchArticles(topic, httpClient)
                } catch (e: Exception) {
                    logger.warn("Failed to fetch from source: {}", source.name, e)
                    emptyList<Article>()
                }
            }
        }
        
        val allArticles = jobs.flatMap { it.await() }
        logger.info("Fetched {} total articles for topic: {}", allArticles.size, topic)
        
        allArticles
    }

    /**
     * Fetch from specific sources only
     */
    suspend fun fetchFromSources(topic: String, sourceNames: List<String>): List<Article> {
        val selectedSources = sources.filter { it.name in sourceNames }
        logger.info("Fetching from {} specific sources for topic: {}", selectedSources.size, topic)
        
        return coroutineScope {
            val jobs = selectedSources.map { source ->
                async {
                    try {
                        source.fetchArticles(topic, httpClient)
                    } catch (e: Exception) {
                        logger.warn("Failed to fetch from source: {}", source.name, e)
                        emptyList<Article>()
                    }
                }
            }
            
            jobs.flatMap { it.await() }
        }
    }

    fun getAvailableSources(): List<String> {
        return sources.map { it.name }
    }

    suspend fun close() {
        httpClient.close()
    }
}

/**
 * Base interface for all data sources
 */
abstract class DataSource(val name: String) {
    abstract suspend fun fetchArticles(topic: String, client: HttpClient): List<Article>
}

/**
 * HackerNews source implementation
 */
class HackerNewsSource : DataSource("HackerNews") {
    override suspend fun fetchArticles(topic: String, client: HttpClient): List<Article> {
        return try {
            println("DEBUG: HackerNewsSource fetching articles for topic: $topic")
            // Fetch top stories from HackerNews API
            val topStories: List<Int> = client.get("https://hacker-news.firebaseio.com/v0/topstories.json").body()
            println("DEBUG: HackerNews API returned ${topStories.size} stories")
            
            // Take first 20 stories and fetch their details
            val articles = topStories.take(20).mapNotNull { storyId ->
                try {
                    val storyResponse: Map<String, Any?> = client.get("https://hacker-news.firebaseio.com/v0/item/$storyId.json").body()
                    
                    val title = storyResponse["title"] as? String ?: return@mapNotNull null
                    val url = storyResponse["url"] as? String ?: "https://news.ycombinator.com/item?id=$storyId"
                    val author = storyResponse["by"] as? String ?: "unknown"
                    val score = (storyResponse["score"] as? Number)?.toDouble()?.div(100.0) ?: 0.5
                    val time = (storyResponse["time"] as? Number)?.toLong()?.times(1000L) ?: System.currentTimeMillis()
                    
                    // Filter by topic relevance - use more flexible matching
                    val keywords = when (topic.lowercase()) {
                        "ai" -> listOf("ai", "artificial intelligence", "machine learning", "ml", "neural", "gpt", "llm", "openai", "claude")
                        "mcp" -> listOf("mcp", "model context protocol", "claude", "anthropic", "context protocol", "ai protocol", "server", "tool")
                        else -> listOf(topic.lowercase())
                    }
                    
                    val titleMatches = keywords.any { keyword -> 
                        title.contains(keyword, ignoreCase = true) 
                    }
                    val textMatches = keywords.any { keyword ->
                        (storyResponse["text"] as? String)?.contains(keyword, ignoreCase = true) == true
                    }
                    
                    if (titleMatches || textMatches) {
                        
                        Article(
                            title = title,
                            content = (storyResponse["text"] as? String) ?: "Article from HackerNews",
                            url = url,
                            source = name,
                            publishedAt = time.toString(),
                            author = author,
                            score = score
                        )
                    } else null
                } catch (e: Exception) {
                    null
                }
            }
            
            println("DEBUG: HackerNews found ${articles.size} articles matching topic: $topic")
            articles
        } catch (e: Exception) {
            println("DEBUG: HackerNews API failed with error: ${e.message}")
            // Fallback to sample data if API fails
            listOf(
                Article(
                    title = "[$topic] Latest developments in $topic",
                    content = "Sample content about $topic from HackerNews...",
                    url = "https://news.ycombinator.com/item?id=123456",
                    source = name,
                    publishedAt = System.currentTimeMillis().toString(),
                    author = "hn_user",
                    score = 1.5
                )
            )
        }
    }
}

/**
 * Reddit source implementation
 */
class RedditSource : DataSource("Reddit") {
    
    /**
     * Get relevant subreddits based on the search topic
     */
    private fun getRelevantSubreddits(topic: String): List<String> {
        val topicLower = topic.lowercase()
        
        return when {
            // MCP (Model Context Protocol) specific
            topicLower.contains("mcp") || topicLower.contains("model context protocol") -> {
                listOf("mcp", "anthropic", "claude", "LangChain", "LocalLLaMA", "MachineLearning", "artificial", "programming")
            }
            
            // AI and Machine Learning
            topicLower.contains("ai") || topicLower.contains("artificial intelligence") -> {
                listOf("artificial", "MachineLearning", "LocalLLaMA", "OpenAI", "ChatGPT", "singularity", "technology", "programming")
            }
            
            // Machine Learning specific
            topicLower.contains("machine learning") || topicLower.contains("ml") -> {
                listOf("MachineLearning", "artificial", "datascience", "statistics", "deeplearning", "programming", "technology")
            }
            
            // Fintech
            topicLower.contains("fintech") || topicLower.contains("financial technology") -> {
                listOf("fintech", "CryptoCurrency", "investing", "financialindependence", "SecurityAnalysis", "economics", "startups", "technology")
            }
            
            // Startup related
            topicLower.contains("startup") || topicLower.contains("entrepreneur") -> {
                listOf("startups", "Entrepreneur", "smallbusiness", "venturecapital", "business", "technology")
            }
            
            // Programming/Development
            topicLower.contains("programming") || topicLower.contains("development") || topicLower.contains("coding") -> {
                listOf("programming", "webdev", "learnprogramming", "cscareerquestions", "programming_languages", "technology")
            }
            
            // Blockchain/Crypto
            topicLower.contains("blockchain") || topicLower.contains("crypto") || topicLower.contains("bitcoin") -> {
                listOf("CryptoCurrency", "Bitcoin", "ethereum", "defi", "blockchain", "technology", "fintech")
            }
            
            // General technology
            topicLower.contains("technology") || topicLower.contains("tech") -> {
                listOf("technology", "gadgets", "futurology", "programming", "artificial", "singularity")
            }
            
            // Default fallback - try topic-specific subreddit first, then general ones
            else -> {
                listOf(topicLower, "technology", "programming", "artificial", "startups")
            }
        }.distinct().take(6) // Limit to 6 subreddits to avoid being too slow
    }

    override suspend fun fetchArticles(topic: String, client: HttpClient): List<Article> {
        return try {
            println("DEBUG: RedditSource fetching articles for topic: $topic")
            // Search topic-relevant subreddits based on the topic
            val subreddits = getRelevantSubreddits(topic)
            println("DEBUG: Selected subreddits for '$topic': ${subreddits.joinToString(", ")}")
            val allArticles = mutableListOf<Article>()
            
            subreddits.forEach { subreddit ->
                try {
                    println("DEBUG: Reddit searching subreddit: r/$subreddit")
                    val responseText: String = client.get("https://www.reddit.com/r/$subreddit/search.json") {
                        parameter("q", topic)
                        parameter("restrict_sr", "1")
                        parameter("sort", "hot")
                        parameter("limit", "10")
                        parameter("t", "week")
                    }.body()
                    
                    val json = Json { ignoreUnknownKeys = true; isLenient = true }
                    val response = json.parseToJsonElement(responseText).jsonObject
                    println("DEBUG: Reddit r/$subreddit response received")
                    
                    val data = response["data"]?.jsonObject
                    val children = data?.get("children")?.jsonArray ?: JsonArray(emptyList())
                    println("DEBUG: Reddit r/$subreddit found ${children.size} posts")
                    
                    children.mapNotNull { child ->
                        val post = child.jsonObject["data"]?.jsonObject ?: return@mapNotNull null
                        val title = post["title"]?.jsonPrimitive?.content ?: return@mapNotNull null
                        val selfText = post["selftext"]?.jsonPrimitive?.content ?: ""
                        val permalink = post["permalink"]?.jsonPrimitive?.content ?: ""
                        val url = "https://reddit.com$permalink"
                        val author = post["author"]?.jsonPrimitive?.content ?: "unknown"
                        val score = (post["score"]?.jsonPrimitive?.doubleOrNull ?: 1.0) / 50.0
                        val createdUtc = (post["created_utc"]?.jsonPrimitive?.longOrNull ?: (System.currentTimeMillis() / 1000L)) * 1000L
                        
                        Article(
                            title = title,
                            content = if (selfText.isNotBlank()) selfText else "Reddit post about $topic",
                            url = url,
                            source = "$name/r/$subreddit",
                            publishedAt = createdUtc.toString(),
                            author = author,
                            score = score.coerceIn(0.1, 5.0)
                        )
                    }.let { 
                        allArticles.addAll(it) 
                        println("DEBUG: Reddit r/$subreddit added ${it.size} articles")
                    }
                } catch (e: Exception) {
                    println("DEBUG: Reddit r/$subreddit failed: ${e.message}")
                    // Continue with other subreddits if one fails
                }
            }
            
            println("DEBUG: Reddit total articles found: ${allArticles.size}")
            allArticles
        } catch (e: Exception) {
            println("DEBUG: Reddit API completely failed with error: ${e.message}")
            // Fallback to sample data if API fails
            listOf(
                Article(
                    title = "$topic Discussion on Reddit",
                    content = "Community discussion about $topic trends and developments...",
                    url = "https://reddit.com/r/technology/post/sample",
                    source = name,
                    publishedAt = System.currentTimeMillis().toString(),
                    author = "reddit_user",
                    score = 1.3
                )
            )
        }
    }
}



/**
 * Dev.to source implementation
 */
class DevToSource : DataSource("DevTo") {
    override suspend fun fetchArticles(topic: String, client: HttpClient): List<Article> {
        return try {
            println("DEBUG: DevToSource fetching articles for topic: $topic")
            // Search Dev.to articles by tag/topic - use String response to avoid serialization issues
            val responseText = client.get("https://dev.to/api/articles") {
                parameter("tag", topic.lowercase())
                parameter("per_page", 20)
                parameter("top", 7) // Top articles from last 7 days
            }.body<String>()
            
            println("DEBUG: Dev.to API response length: ${responseText.length}")
            
            // Parse JSON manually to avoid serialization issues
            val json = Json { ignoreUnknownKeys = true; isLenient = true }
            val jsonArray = json.parseToJsonElement(responseText).jsonArray
            
            println("DEBUG: Dev.to API returned ${jsonArray.size} articles")
            
            jsonArray.mapNotNull { element ->
                val articleData = element.jsonObject
                val title = articleData["title"]?.jsonPrimitive?.content ?: return@mapNotNull null
                val description = articleData["description"]?.jsonPrimitive?.content ?: ""
                val url = articleData["url"]?.jsonPrimitive?.content ?: return@mapNotNull null
                val user = articleData["user"]?.jsonObject
                val author = user?.get("name")?.jsonPrimitive?.content ?: "unknown"
                val publishedAt = articleData["published_at"]?.jsonPrimitive?.content ?: System.currentTimeMillis().toString()
                val tagList = articleData["tag_list"]?.jsonArray?.map { it.jsonPrimitive.content } ?: emptyList()
                val positiveReactions = articleData["positive_reactions_count"]?.jsonPrimitive?.int?.toDouble()?.div(10.0) ?: 1.0
                
                Article(
                    title = title,
                    content = description,
                    url = url,
                    source = name,
                    publishedAt = publishedAt,
                    author = author,
                    tags = tagList,
                    score = positiveReactions.coerceIn(0.1, 5.0)
                )
            }
        } catch (e: Exception) {
            println("DEBUG: Dev.to API failed with error: ${e.message}")
            // Fallback to sample data if API fails
            listOf(
                Article(
                    title = "Building with $topic: Developer Guide",
                    content = "Technical article about implementing $topic solutions...",
                    url = "https://dev.to/user/sample-article",
                    source = name,
                    publishedAt = System.currentTimeMillis().toString(),
                    author = "dev_author",
                    tags = listOf("development", topic.lowercase()),
                    score = 1.7
                )
            )
        }
    }
}