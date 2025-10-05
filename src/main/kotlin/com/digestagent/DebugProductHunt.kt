package com.digestagent

import com.digestagent.config.Configuration
import com.digestagent.sources.ProductHuntSource
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.*

/**
 * Debug utility to test ProductHunt API integration
 */
suspend fun main() {
    println("=== ProductHunt Debug Utility ===\n")
    
    // Test 1: Configuration
    println("1. Testing API Key Configuration")
    println("--------------------------------")
    val apiKey = Configuration.productHuntApiKey
    println("API Key from Configuration: ${if (apiKey != null) "PRESENT (${apiKey.take(5)}...${apiKey.takeLast(5)})" else "NULL"}")
    
    val envKey = System.getenv("PRODUCTHUNT_API_KEY")
    println("API Key from System.getenv: ${if (envKey != null) "PRESENT (${envKey.take(5)}...${envKey.takeLast(5)})" else "NULL"}")
    
    val configMap = Configuration.toMap()
    println("hasProductHuntKey from config map: ${configMap["hasProductHuntKey"]}")
    
    println("Expected API Key: qJTT5mhia0iocIWq8M_lgn3UqPtz0Q-8GDLENmDasQo")
    println("Does expected key match config key: ${apiKey == "qJTT5mhia0iocIWq8M_lgn3UqPtz0Q-8GDLENmDasQo"}")
    
    println("\n" + "=".repeat(50) + "\n")
    
    // Test 2: Source Fetch
    println("2. Testing ProductHunt Source Fetch")
    println("-----------------------------------")
    
    val httpClient = HttpClient(CIO) {
        install(ContentNegotiation) {
            json(Json {
                ignoreUnknownKeys = true
                isLenient = true
            })
        }
    }
    
    try {
        val source = ProductHuntSource()
        println("✓ Created ProductHunt source successfully")
        
        println("Fetching articles for topic 'AI'...")
        val articles = source.fetchArticles("AI", httpClient)
        println("✓ Fetched ${articles.size} articles")
        
        if (articles.isNotEmpty()) {
            println("\nFirst article details:")
            val first = articles.first()
            println("  Title: ${first.title}")
            println("  Content: ${first.content.take(100)}...")
            println("  URL: ${first.url}")
            println("  Source: ${first.source}")
            println("  Author: ${first.author}")
            println("  Score: ${first.score}")
            
            // Check if this looks like sample data
            val isSampleData = first.title.contains("Tools and Products") || 
                             first.url.contains("sample-product") ||
                             first.title.contains("No API Key")
            println("  ⚠️ Appears to be sample data: $isSampleData")
            
            if (articles.size > 1) {
                println("\nAll article titles:")
                articles.forEachIndexed { index, article ->
                    println("  ${index + 1}. ${article.title}")
                }
            }
        } else {
            println("❌ No articles returned")
        }
        
    } catch (e: Exception) {
        println("❌ Error during source fetch: ${e.message}")
        e.printStackTrace()
    }
    
    println("\n" + "=".repeat(50) + "\n")
    
    // Test 3: Direct API Call
    println("3. Testing Direct ProductHunt GraphQL API Call")
    println("---------------------------------------------")
    
    if (apiKey == null) {
        println("❌ No API key available, skipping direct API test")
        httpClient.close()
        return
    }
    
    try {
        val query = """
            query {
              posts(first: 3, order: VOTES) {
                edges {
                  node {
                    name
                    tagline
                    description
                    url
                    votesCount
                    createdAt
                    user {
                      name
                    }
                    topics {
                      edges {
                        node {
                          name
                        }
                      }
                    }
                  }
                }
              }
            }
        """.trimIndent()
        
        val requestBody = mapOf("query" to query)
        println("Making GraphQL request to: https://api.producthunt.com/v2/api/graphql")
        println("Using API key: ${apiKey.take(5)}...${apiKey.takeLast(5)}")
        
        val response = httpClient.post("https://api.producthunt.com/v2/api/graphql") {
            header("Authorization", "Bearer $apiKey")
            header("Content-Type", "application/json")
            setBody(requestBody)
        }
        
        println("✓ Response status: ${response.status}")
        
        val responseText = response.body<String>()
        println("✓ Response body length: ${responseText.length} characters")
        println("Response preview: ${responseText.take(200)}...")
        
        // Try to parse the response
        try {
            val json = Json { ignoreUnknownKeys = true }
            val jsonElement = json.parseToJsonElement(responseText)
            println("✓ Successfully parsed JSON response")
            
            val responseObj = jsonElement.jsonObject
            val data = responseObj["data"]
            val errors = responseObj["errors"]
            
            if (errors != null) {
                println("❌ GraphQL errors found:")
                println(errors.toString())
            }
            
            if (data != null) {
                println("✓ GraphQL data found")
                
                // Try to extract post information
                val posts = data.jsonObject["posts"]?.jsonObject?.get("edges")?.jsonArray
                if (posts != null && posts.size > 0) {
                    println("✓ Found ${posts.size} posts in response")
                    val firstPost = posts[0].jsonObject["node"]?.jsonObject
                    if (firstPost != null) {
                        val name = firstPost["name"]?.jsonPrimitive?.content
                        val tagline = firstPost["tagline"]?.jsonPrimitive?.content
                        val votesCount = firstPost["votesCount"]?.jsonPrimitive?.int
                        println("  First post: '$name' - $tagline ($votesCount votes)")
                    }
                } else {
                    println("❌ No posts found in response data")
                }
            } else {
                println("❌ No 'data' field in GraphQL response")
            }
            
        } catch (e: Exception) {
            println("❌ Failed to parse JSON response: ${e.message}")
            println("Raw response: $responseText")
        }
        
    } catch (e: Exception) {
        println("❌ Direct API call failed: ${e.message}")
        e.printStackTrace()
    } finally {
        httpClient.close()
    }
    
    println("\n" + "=".repeat(50))
    println("Debug completed!")
}