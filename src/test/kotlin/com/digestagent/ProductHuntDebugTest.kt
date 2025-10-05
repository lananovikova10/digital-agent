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
import org.junit.jupiter.api.Test

class ProductHuntDebugTest {
    
    @Test
    fun testProductHuntApiKeyConfiguration() {
        println("=== ProductHunt API Key Configuration Debug ===")
        
        // Check if API key is loaded
        val apiKey = Configuration.productHuntApiKey
        println("API Key from Configuration: ${if (apiKey != null) "PRESENT (${apiKey.take(5)}...${apiKey.takeLast(5)})" else "NULL"}")
        
        // Check environment directly
        val envKey = System.getenv("PRODUCTHUNT_API_KEY")
        println("API Key from System.getenv: ${if (envKey != null) "PRESENT (${envKey.take(5)}...${envKey.takeLast(5)})" else "NULL"}")
        
        // Check configuration map
        val configMap = Configuration.toMap()
        println("hasProductHuntKey from config map: ${configMap["hasProductHuntKey"]}")
        
        println("Expected API Key: qJTT5mhia0iocIWq8M_lgn3UqPtz0Q-8GDLENmDasQo")
        println("Does expected key match config key: ${apiKey == "qJTT5mhia0iocIWq8M_lgn3UqPtz0Q-8GDLENmDasQo"}")
    }
    
    @Test
    fun testProductHuntSourceFetch() = runBlocking {
        println("=== ProductHunt Source Fetch Debug ===")
        
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
            println("Created ProductHunt source")
            
            val articles = source.fetchArticles("AI", httpClient)
            println("Fetched ${articles.size} articles")
            
            if (articles.isNotEmpty()) {
                println("\nFirst article:")
                val first = articles.first()
                println("Title: ${first.title}")
                println("Content: ${first.content.take(100)}...")
                println("URL: ${first.url}")
                println("Source: ${first.source}")
                println("Author: ${first.author}")
                println("Score: ${first.score}")
                
                // Check if this looks like sample data
                val isSampleData = first.title.contains("Tools and Products") || 
                                 first.url.contains("sample-product") ||
                                 first.title.contains("No API Key")
                println("Appears to be sample data: $isSampleData")
            } else {
                println("No articles returned")
            }
            
        } catch (e: Exception) {
            println("Error during fetch: ${e.message}")
            e.printStackTrace()
        } finally {
            httpClient.close()
        }
    }
    
    @Test
    fun testDirectGraphQLCall() = runBlocking {
        println("=== Direct ProductHunt GraphQL API Call Debug ===")
        
        val apiKey = Configuration.productHuntApiKey
        if (apiKey == null) {
            println("No API key available, skipping direct API test")
            return@runBlocking
        }
        
        val httpClient = HttpClient(CIO) {
            install(ContentNegotiation) {
                json(Json {
                    ignoreUnknownKeys = true
                    isLenient = true
                })
            }
        }
        
        try {
            val query = """
                query {
                  posts(first: 5, order: VOTES) {
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
            
            println("Response status: ${response.status}")
            println("Response headers: ${response.headers}")
            
            val responseText = response.body<String>()
            println("Response body length: ${responseText.length}")
            println("Response body preview: ${responseText.take(500)}...")
            
            // Try to parse the response
            try {
                val json = Json { ignoreUnknownKeys = true }
                val jsonElement = json.parseToJsonElement(responseText)
                println("Successfully parsed JSON response")
                
                val responseObj = jsonElement.jsonObject
                val data = responseObj["data"]
                val errors = responseObj["errors"]
                
                if (errors != null) {
                    println("GraphQL errors found: $errors")
                }
                
                if (data != null) {
                    println("GraphQL data found: ${data.toString().take(200)}...")
                } else {
                    println("No data field in response")
                }
                
            } catch (e: Exception) {
                println("Failed to parse JSON response: ${e.message}")
            }
            
        } catch (e: Exception) {
            println("Direct API call failed: ${e.message}")
            e.printStackTrace()
        } finally {
            httpClient.close()
        }
    }
}