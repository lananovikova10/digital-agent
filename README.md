# Digest Agent (Weekly Intelligence Agent)

An AI-powered agent that sources information from Hacker News, Reddit, X (Twitter), Product Hunt, YC launches, and other sources to generate summarized weekly reports with trends and strategic takeaways.

**🚀 Now powered by Kotlin and Koog AI Framework!**

## Architecture

- **Core**: Kotlin with Koog AI Framework for agentic workflows
- **HTTP Client**: Ktor for robust API integrations  
- **AI Engine**: OpenAI GPT models with Hugging Face fallback
- **Configuration**: Environment-based with dotenv support
- **Concurrency**: Kotlin coroutines for high-performance async processing
- **Notifications**: Telegram integration for report delivery

## Project Structure

```
src/main/kotlin/com/digestagent/
├── agent/                    # Main AI agent implementation
│   └── WeeklyIntelAgent.kt
├── model/                    # Data models and state management
│   └── WeeklyIntelState.kt
├── tools/                    # Koog AI tools for data processing
│   ├── DataIngestionTools.kt
│   ├── ContentProcessingTools.kt
│   └── ReportGenerationTools.kt
├── sources/                  # Data source integrations
│   └── SourceManager.kt
├── services/                 # External service integrations
│   └── HuggingFaceService.kt
├── telegram/                 # Telegram notification service
│   └── TelegramNotifier.kt
├── config/                   # Configuration management
│   └── Configuration.kt
└── Main.kt                   # Application entry point
```

## Quick Start

### Prerequisites

- **Java 17+** (required)
- **Kotlin 2.1.21+** (handled by Gradle)
- **OpenAI API Key** (required)
- **Telegram Bot Token** (optional, for notifications)

### Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd digest-agent

# 2. Copy environment template
cp env.example .env

# 3. Edit .env file with your API keys
# Required: OPENAI_API_KEY
# Optional: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
# Optional: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, TWITTER_BEARER_TOKEN, PRODUCTHUNT_API_KEY

# 4. Build the project
./gradlew build

# 5. Run the agent
./gradlew run
```

### Custom Topics

```bash
# Run with specific topics
./gradlew run --args="'AI startups' 'fintech innovations' 'developer tools'"
```

## Features

### 🔍 **Multi-Source Data Ingestion**
- **Hacker News**: Top stories and discussions (no API key required)
- **Reddit**: Relevant subreddit posts (with API key)
- **TechCrunch**: Latest tech news (RSS feed)
- **YC Launches**: Y Combinator startup launches (web scraping)
- **Dev.to**: Developer community posts (no API key required)
- **Product Hunt**: New product launches (with API key)
- **Twitter/X**: Tech industry tweets (with API key)

### 🧠 **AI-Powered Processing**
- **Koog AI Framework**: Advanced agent orchestration
- **OpenAI Integration**: GPT models for analysis and summarization
- **Hugging Face Fallback**: Qwen models for robust processing
- **Content Ranking**: ML-based scoring and relevance filtering
- **Duplicate Detection**: Automatic deduplication of similar articles
- **Quality Assessment**: Content quality scoring and filtering

### 📊 **Intelligent Report Generation**
- **Weekly Intelligence Reports**: Comprehensive summaries with insights
- **Strategic Analysis**: Business implications and recommendations
- **Trend Identification**: Pattern recognition across sources
- **Customizable Topics**: Focus on specific areas of interest
- **Multiple Formats**: Markdown, JSON output support

### 📱 **Telegram Integration**
- **Automated Notifications**: Reports delivered to Telegram
- **Real-time Updates**: Live report generation status
- **Easy Setup**: Simple bot token configuration

### ⚡ **High Performance**
- **Kotlin Coroutines**: Efficient concurrent processing
- **Ktor HTTP Client**: Fast, reliable API calls
- **Memory Efficient**: Built-in history compression
- **Type Safe**: Compile-time error prevention

## Configuration

### Required Environment Variables

Create a `.env` file with the following:

```bash
# Required
OPENAI_API_KEY=your_openai_key_here

# Optional - Telegram notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional - Enhanced data sources
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
TWITTER_BEARER_TOKEN=your_twitter_token
PRODUCTHUNT_API_KEY=your_producthunt_key

# Optional - Hugging Face (for fallback)
HUGGINGFACE_API_TOKEN=your_hf_token
```

### Topics Configuration

Default topics are: "AI", "machine learning", "developer tools", "startup funding"

Customize via command line:
```bash
./gradlew run --args="'blockchain' 'fintech' 'crypto'"
```

### Getting API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **Telegram Bot**: Message @BotFather on Telegram
- **Reddit**: https://www.reddit.com/prefs/apps
- **Twitter/X**: https://developer.twitter.com/
- **Product Hunt**: https://api.producthunt.com/v2/docs
- **Hugging Face**: https://huggingface.co/settings/tokens

## Usage Examples

### Basic Report Generation

```kotlin
val agent = WeeklyIntelAgent(openAIApiKey)
val report = agent.runWeeklyIntel(listOf("AI", "machine learning"))
println(report)
```

### With Telegram Notifications

```kotlin
val agent = WeeklyIntelAgent(
    openAIApiKey = openAIApiKey,
    telegramBotToken = telegramToken,
    telegramChatId = chatId
)
val report = agent.runWeeklyIntel(topics)
// Report automatically sent to Telegram
```

### Focused Analysis

```kotlin
val report = agent.runFocusedAnalysis(
    topics = listOf("AI", "startups"),
    focusArea = "investment trends",
    maxArticles = 20
)
```

## Available Tasks

```bash
# Build the project
./gradlew build

# Run the main application
./gradlew run

# Run with custom arguments
./gradlew run --args="'topic1' 'topic2'"

# Test Telegram integration
./gradlew testTelegram -PchatId=your_chat_id

# Run tests
./gradlew test

# Clean build
./gradlew clean build
```

## Troubleshooting

### Common Issues

**Build Failures**
```bash
# Clean and rebuild
./gradlew clean build

# Check Java version
java -version  # Should be 17+
```

**Missing API Keys**
- Ensure `OPENAI_API_KEY` is set in `.env`
- Verify `.env` file is in project root
- Check for typos in environment variable names

**No Articles Found**
- Check internet connection
- Verify API keys are correct (for Reddit, Twitter, Product Hunt)
- Try with just Hacker News (no API key required)

**Telegram Not Working**
```bash
# Test your bot token and chat ID
./gradlew testTelegram -PchatId=your_chat_id
```

### Performance Tips

1. **Limit Article Count**: Use `maxArticles` parameter
2. **Focus Topics**: Be specific with topic selection  
3. **Monitor Memory**: Increase JVM heap if needed (`-Xmx2g`)
4. **Enable Logging**: Check logs for detailed debugging

### Getting Help

1. **Check Logs**: Look at console output for detailed error messages
2. **Verify Configuration**: Ensure all required environment variables are set
3. **Test Components**: Use individual Gradle tasks to isolate issues
4. **Migration Guide**: See `README-KOOG-MIGRATION.md` for technical details

## Migration from Python

This project was migrated from Python/LangChain to Kotlin/Koog for:

- **Better Performance**: Kotlin coroutines outperform Python asyncio
- **Type Safety**: Compile-time error checking
- **Enterprise Ready**: JVM ecosystem and tooling
- **Memory Efficiency**: Better resource management
- **Simplified Architecture**: Single agent replaces complex graph workflows

See `README-KOOG-MIGRATION.md` for detailed migration information.

## Development

### Testing

```bash
# Run all tests
./gradlew test

# Run specific test
./gradlew test --tests "MigrationTest"
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[License information here]