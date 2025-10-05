package com.digestagent.config

import io.github.cdimascio.dotenv.Dotenv
import org.slf4j.LoggerFactory

/**
 * Configuration management for the Digest Agent
 * Handles environment variables and settings
 */
object Configuration {
    private val logger = LoggerFactory.getLogger(Configuration::class.java)
    
    private val dotenv = try {
        Dotenv.configure()
            .ignoreIfMalformed()
            .ignoreIfMissing()
            .load()
    } catch (e: Exception) {
        logger.warn("Could not load .env file: {}", e.message)
        null
    }

    /**
     * Get environment variable with optional fallback
     */
    private fun getEnv(key: String, default: String? = null): String {
        return System.getenv(key) 
            ?: dotenv?.get(key) 
            ?: default
            ?: throw IllegalStateException("Required environment variable $key is not set")
    }

    /**
     * Get optional environment variable
     */
    private fun getEnvOptional(key: String): String? {
        return System.getenv(key) ?: dotenv?.get(key)
    }

    // OpenAI Configuration
    val openAIApiKey: String by lazy {
        getEnv("OPENAI_API_KEY")
            ?: throw IllegalStateException("OPENAI_API_KEY must be set")
    }

    // Anthropic Configuration (optional)
    val anthropicApiKey: String? by lazy {
        getEnvOptional("ANTHROPIC_API_KEY")
    }

    // Database Configuration
    val databaseUrl: String by lazy {
        getEnv("DATABASE_URL", "jdbc:postgresql://localhost:5432/digest_agent")
    }

    val databaseUser: String by lazy {
        getEnv("DATABASE_USER", "postgres")
    }

    val databasePassword: String by lazy {
        getEnv("DATABASE_PASSWORD", "password")
    }

    // Redis Configuration
    val redisUrl: String by lazy {
        getEnv("REDIS_URL", "redis://localhost:6379")
    }

    // Source API Keys
    val redditClientId: String? by lazy {
        getEnvOptional("REDDIT_CLIENT_ID")
    }

    val redditClientSecret: String? by lazy {
        getEnvOptional("REDDIT_CLIENT_SECRET")
    }

    val twitterBearerToken: String? by lazy {
        getEnvOptional("TWITTER_BEARER_TOKEN")
    }

    val devToApiKey: String? by lazy {
        getEnvOptional("DEVTO_API_KEY")
    }

    val productHuntApiKey: String? by lazy {
        getEnvOptional("PRODUCTHUNT_API_KEY")
    }

    // Telegram Configuration
    val telegramBotToken: String? by lazy {
        getEnvOptional("TG_BOT_KEY")
    }

    val telegramChatId: String? by lazy {
        getEnvOptional("TG_CHAT_ID")
    }

    // Hugging Face Configuration
    val huggingFaceToken: String? by lazy {
        getEnvOptional("HUGGING_FACE_TOKEN")
    }

    // Application Configuration
    val maxArticlesPerSource: Int by lazy {
        getEnv("MAX_ARTICLES_PER_SOURCE", "50").toInt()
    }

    val reportGenerationTimeout: Long by lazy {
        getEnv("REPORT_GENERATION_TIMEOUT_MS", "300000").toLong() // 5 minutes
    }

    val logLevel: String by lazy {
        getEnv("LOG_LEVEL", "INFO")
    }

    // Feature Flags
    val enableOpenTelemetry: Boolean by lazy {
        getEnv("ENABLE_OPENTELEMETRY", "false").toBoolean()
    }

    val enableCaching: Boolean by lazy {
        getEnv("ENABLE_CACHING", "true").toBoolean()
    }

    val enableStreaming: Boolean by lazy {
        getEnv("ENABLE_STREAMING", "true").toBoolean()
    }

    /**
     * Validate that all required configuration is present
     */
    fun validate() {
        logger.info("Validating configuration...")
        
        try {
            // Check required keys
            openAIApiKey
            databaseUrl
            databaseUser
            databasePassword
            
            logger.info("Configuration validation successful")
            logger.info("Database URL: {}", databaseUrl.replace(Regex("://.*@"), "://***@"))
            logger.info("Max articles per source: {}", maxArticlesPerSource)
            logger.info("Report timeout: {}ms", reportGenerationTimeout)
            logger.info("Log level: {}", logLevel)
            logger.info("Features - Caching: {}, Streaming: {}, OpenTelemetry: {}", 
                      enableCaching, enableStreaming, enableOpenTelemetry)
            
        } catch (e: Exception) {
            logger.error("Configuration validation failed", e)
            throw e
        }
    }

    /**
     * Get all configuration as a map (excluding sensitive values)
     */
    fun toMap(): Map<String, Any> {
        return mapOf(
            "maxArticlesPerSource" to maxArticlesPerSource,
            "reportGenerationTimeout" to reportGenerationTimeout,
            "logLevel" to logLevel,
            "enableCaching" to enableCaching,
            "enableStreaming" to enableStreaming,
            "enableOpenTelemetry" to enableOpenTelemetry,
            "hasOpenAIKey" to openAIApiKey.isNotEmpty(),
            "hasAnthropicKey" to !anthropicApiKey.isNullOrEmpty(),
            "hasRedditKeys" to (!redditClientId.isNullOrEmpty() && !redditClientSecret.isNullOrEmpty()),
            "hasTwitterKey" to !twitterBearerToken.isNullOrEmpty(),
            "hasDevToKey" to !devToApiKey.isNullOrEmpty(),
            "hasProductHuntKey" to !productHuntApiKey.isNullOrEmpty(),
            "hasTelegramBotToken" to !telegramBotToken.isNullOrEmpty(),
            "hasHuggingFaceToken" to !huggingFaceToken.isNullOrEmpty()
        )
    }
}