# Digest Agent - Koog Migration

This document describes the migration from LangChain (Python) to Koog (Kotlin) for the Weekly Intelligence Agent.

## Migration Overview

The original Python/LangChain implementation used LangGraph for workflow orchestration. The new Koog implementation leverages:

- **Koog AIAgent**: Replaces LangGraph's StateGraph with a more flexible agent-based approach
- **@KoogTool**: Replaces Python `@tool` decorators with Kotlin annotations
- **Kotlin Coroutines**: Replaces Python asyncio for concurrency
- **Built-in History Compression**: Replaces manual memory management

## Key Changes

### 1. Project Structure

```
src/main/kotlin/com/digestagent/
├── agent/                    # Main AI agent
│   └── WeeklyIntelAgent.kt
├── model/                    # Data models
│   └── WeeklyIntelState.kt
├── tools/                    # Koog tools
│   ├── DataIngestionTools.kt
│   ├── ContentProcessingTools.kt
│   └── ReportGenerationTools.kt
├── sources/                  # Data source implementations
│   └── SourceManager.kt
├── config/                   # Configuration management
│   └── Configuration.kt
└── Main.kt                   # Application entry point
```

### 2. LangChain → Koog Mapping

| LangChain | Koog | Implementation |
|-----------|------|---------------|
| `StateGraph` | `AIAgent` | Single agent with tools |
| `@tool` | `@KoogTool` | Kotlin annotations |
| `ChatOpenAI` | `simpleOpenAIExecutor()` | Built-in OpenAI support |
| `ConversationBufferMemory` | Built-in history compression | Automatic |
| Python asyncio | Kotlin coroutines | `suspend` functions |

### 3. Workflow Changes

**Before (LangGraph):**
```python
workflow = StateGraph(WeeklyIntelState)
workflow.add_node("ingest", self._ingest_node)
workflow.add_node("enrich", self._enrich_node)
# ... more nodes
workflow.add_edge("ingest", "enrich")
# ... more edges
```

**After (Koog):**
```kotlin
val agent = AIAgent(
    executor = simpleOpenAIExecutor(apiKey),
    systemPrompt = "You are a Weekly Intelligence Agent...",
    tools = listOf(
        dataIngestionTools::ingestArticlesForTopics,
        contentProcessingTools::enrichArticles,
        // ... more tools
    )
)

// Agent automatically orchestrates tool usage
val report = agent.run(prompt)
```

## Setup Instructions

### 1. Prerequisites

- Kotlin 1.9.20+
- Gradle 8.0+
- Java 17+
- OpenAI API Key

### 2. Configuration

1. Copy `env.example` to `.env`
2. Set your OpenAI API key:
   ```
   OPENAI_API_KEY=your_key_here
   ```

### 3. Build and Run

```bash
# Build the project
./gradlew build

# Run the agent
./gradlew run

# Run with custom topics
./gradlew run --args="'AI startups' 'fintech innovations'"
```

## Usage Examples

### Basic Usage

```kotlin
val agent = WeeklyIntelAgent(openAIApiKey)
val report = agent.runWeeklyIntel(listOf("AI", "machine learning"))
println(report)
```

### Streaming Reports

```kotlin
agent.runWeeklyIntelWithStreaming(topics) { chunk ->
    println("Update: $chunk")
}
```

### Focused Analysis

```kotlin
val report = agent.runFocusedAnalysis(
    topics = listOf("AI", "startups"),
    focusArea = "investment trends",
    maxArticles = 20
)
```

## Benefits of Migration

1. **Type Safety**: Kotlin's type system prevents runtime errors
2. **Performance**: Better performance than Python for concurrent operations
3. **Memory Management**: Koog's built-in history compression
4. **Multiplatform**: Can run on JVM, Android, iOS, and Native
5. **Enterprise Ready**: Better monitoring and observability support
6. **Simplified Architecture**: Single agent replaces complex graph workflows

## Tool Implementations

### Data Ingestion Tools
- `ingestArticlesForTopics`: Fetch from all sources
- `filterArticlesByDate`: Filter by recency
- `deduplicateArticles`: Remove duplicates

### Content Processing Tools
- `enrichArticles`: Add metadata and scores
- `rankArticlesByRelevance`: Rank by importance
- `extractKeyInsights`: Identify trends

### Report Generation Tools
- `generateSummaryInsights`: Create structured summaries
- `composeFinalReport`: Generate final report
- `createReportSections`: Structure for different formats

## Migration Checklist

- [x] Set up Kotlin project with Gradle
- [x] Add Koog dependencies
- [x] Convert Python tools to @KoogTool functions
- [x] Replace LangGraph with AIAgent
- [x] Implement source managers with Ktor HTTP client
- [x] Create configuration management
- [x] Set up main application entry point
- [x] Add environment variable support
- [ ] Test with real API keys
- [ ] Performance optimization
- [ ] Add comprehensive error handling
- [ ] Implement database persistence (optional)
- [ ] Add monitoring and metrics

## Next Steps

1. **Test the Implementation**: Run with real data and API keys
2. **Add Database Support**: Implement PostgreSQL integration if needed
3. **Performance Tuning**: Optimize for large datasets
4. **Monitoring**: Add OpenTelemetry support
5. **Documentation**: Complete API documentation
6. **CI/CD**: Set up automated testing and deployment

## Troubleshooting

### Common Issues

1. **Missing API Key**: Ensure `OPENAI_API_KEY` is set in `.env`
2. **Dependency Issues**: Run `./gradlew clean build` to refresh dependencies
3. **Memory Issues**: Increase JVM heap size in `gradle.properties`

### Performance Tips

1. Use `maxArticles` parameter to limit data processing
2. Enable caching with `ENABLE_CACHING=true`
3. Use streaming for long-running reports
4. Monitor memory usage with JVM profiling tools