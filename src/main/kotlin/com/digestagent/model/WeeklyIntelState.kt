package com.digestagent.model

import kotlinx.serialization.Serializable

@Serializable
data class Article(
    val title: String,
    val content: String,
    val url: String,
    val source: String,
    val publishedAt: String,
    val author: String? = null,
    val tags: List<String> = emptyList(),
    val score: Double = 0.0,
    val summary: String? = null,
    val metadata: Map<String, String> = emptyMap()
)

@Serializable
data class Summary(
    val keyInsights: List<String> = emptyList(),
    val trends: List<String> = emptyList(),
    val keyQuotes: List<String> = emptyList(),
    val topSources: List<String> = emptyList(),
    val metadata: Map<String, String> = emptyMap()
)

@Serializable
data class WeeklyIntelState(
    val topics: List<String> = emptyList(),
    val rawArticles: List<Article> = emptyList(),
    val enrichedArticles: List<Article> = emptyList(),
    val rankedArticles: List<Article> = emptyList(),
    val summary: Summary = Summary(),
    val report: String = "",
    val metadata: Map<String, String> = emptyMap()
)