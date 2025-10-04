#!/usr/bin/env python3
"""
Complete web interface for Weekly Intelligence Agent
"""
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import asyncio
import sys
import os
from datetime import datetime
import json
import uuid

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

# In-memory storage for demo
reports_storage = {}

# Base template
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Weekly Intelligence Agent{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-100 min-h-screen">
    <nav class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <a href="/" class="flex items-center">
                        <i class="fas fa-brain text-2xl text-blue-600 mr-3"></i>
                        <span class="text-xl font-bold text-gray-900">Weekly Intelligence Agent</span>
                    </a>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="/" class="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium">
                        <i class="fas fa-list mr-1"></i>Reports
                    </a>
                    <a href="/generate" class="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700">
                        <i class="fas fa-plus mr-1"></i>Generate
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div class="px-4 py-6 sm:px-0">
            {% block content %}{% endblock %}
        </div>
    </main>
</body>
</html>
"""

# Reports listing template
REPORTS_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900 mb-4">
        <i class="fas fa-chart-line mr-2 text-blue-600"></i>
        Intelligence Reports
    </h1>
    <p class="text-gray-600">View and manage your weekly intelligence reports</p>
</div>

{% if reports %}
<div class="grid gap-6">
    {% for report in reports %}
    <div class="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
        <div class="p-6">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="text-xl font-semibold text-gray-900 mb-2">
                        Intelligence Report - {{ report.created_at }}
                    </h3>
                    <div class="flex flex-wrap gap-2 mb-3">
                        {% for topic in report.topics %}
                        <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                            {{ topic }}
                        </span>
                        {% endfor %}
                    </div>
                </div>
                <div class="text-sm text-gray-500">
                    <i class="fas fa-calendar mr-1"></i>
                    {{ report.generated_at }}
                </div>
            </div>
            
            <div class="bg-gray-50 p-4 rounded-lg mb-4">
                <div class="grid grid-cols-3 gap-4 text-sm">
                    <div>
                        <span class="font-medium text-gray-700">Articles:</span>
                        <span class="text-gray-900">{{ report.stats.total_articles }}</span>
                    </div>
                    <div>
                        <span class="font-medium text-gray-700">Top Selected:</span>
                        <span class="text-gray-900">{{ report.stats.top_articles }}</span>
                    </div>
                    <div>
                        <span class="font-medium text-gray-700">Sources:</span>
                        <span class="text-gray-900">{{ report.stats.sources_used }}</span>
                    </div>
                </div>
            </div>
            
            <div class="flex justify-between items-center">
                <div class="text-sm text-gray-500">
                    <i class="fas fa-file-alt mr-1"></i>
                    Report ID: {{ report.id[:8] }}...
                </div>
                <a href="/reports/{{ report.id }}" 
                   class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors">
                    <i class="fas fa-eye mr-1"></i>
                    View Report
                </a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="text-center py-12">
    <i class="fas fa-file-alt text-6xl text-gray-300 mb-4"></i>
    <h3 class="text-xl font-semibold text-gray-900 mb-2">No Reports Yet</h3>
    <p class="text-gray-600 mb-6">Generate your first intelligence report to get started</p>
    <a href="/generate" class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">
        <i class="fas fa-plus mr-2"></i>
        Generate Report
    </a>
</div>
{% endif %}
{% endblock %}
""")

# Generate form template
GENERATE_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<div class="max-w-2xl mx-auto">
    <div class="bg-white rounded-lg shadow-lg p-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-6">
            <i class="fas fa-plus-circle mr-2 text-blue-600"></i>
            Generate New Report
        </h1>
        
        <form id="generateForm" class="space-y-6">
            <div>
                <label for="topics" class="block text-sm font-medium text-gray-700 mb-2">
                    Topics to Analyze
                </label>
                <input type="text" 
                       id="topics" 
                       name="topics" 
                       placeholder="e.g., MCP, AI, machine learning, fintech"
                       class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                       required>
                <p class="text-sm text-gray-500 mt-1">
                    Enter topics separated by commas. The agent will search for relevant articles and generate insights.
                </p>
            </div>

            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 class="font-semibold text-blue-900 mb-2">
                    <i class="fas fa-info-circle mr-1"></i>
                    Demo Mode
                </h3>
                <p class="text-sm text-blue-800 mb-2">
                    This demo uses Hacker News for fast results (under 30 seconds).
                </p>
                <p class="text-sm text-blue-700">
                    <strong>Full version includes 14 sources:</strong> Dev.to, Medium, arXiv, Stack Overflow, Substack, YouTube, RSS feeds, and more.
                </p>
            </div>

            <button type="submit" 
                    id="generateBtn"
                    class="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors font-medium">
                <i class="fas fa-cog mr-2"></i>
                Generate Intelligence Report
            </button>
        </form>

        <div id="progress" class="hidden mt-6">
            <div class="bg-gray-200 rounded-full h-2 mb-4">
                <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: 0%" id="progressBar"></div>
            </div>
            <div class="text-center">
                <div class="inline-flex items-center text-blue-600">
                    <i class="fas fa-spinner fa-spin mr-2"></i>
                    <span id="progressText">Fetching articles...</span>
                </div>
            </div>
        </div>

        <div id="result" class="hidden mt-6"></div>
    </div>
</div>

<script>
document.getElementById('generateForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const topics = document.getElementById('topics').value.split(',').map(t => t.trim()).filter(t => t);
    const generateBtn = document.getElementById('generateBtn');
    const progress = document.getElementById('progress');
    const result = document.getElementById('result');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    // Show progress
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generating...';
    progress.classList.remove('hidden');
    result.classList.add('hidden');
    
    // Animate progress
    let progressValue = 0;
    const progressSteps = [
        'Fetching articles from Hacker News...',
        'Processing and ranking content...',
        'Generating report sections...',
        'Finalizing report...'
    ];
    
    const progressInterval = setInterval(() => {
        if (progressValue < 90) {
            progressValue += Math.random() * 20;
            progressBar.style.width = Math.min(progressValue, 90) + '%';
            const stepIndex = Math.floor((progressValue / 90) * progressSteps.length);
            progressText.textContent = progressSteps[Math.min(stepIndex, progressSteps.length - 1)];
        }
    }, 800);
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topics: topics })
        });
        
        const data = await response.json();
        
        clearInterval(progressInterval);
        progressBar.style.width = '100%';
        progressText.textContent = 'Report generated successfully!';
        
        setTimeout(() => {
            if (response.ok) {
                result.innerHTML = `
                    <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div class="flex items-center mb-2">
                            <i class="fas fa-check-circle text-green-600 mr-2"></i>
                            <h3 class="font-semibold text-green-900">Report Generated Successfully!</h3>
                        </div>
                        <p class="text-green-800 mb-4">Your intelligence report has been created and is ready to view.</p>
                        <div class="flex gap-3">
                            <a href="/reports/${data.report_id}" 
                               class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors">
                                <i class="fas fa-eye mr-1"></i>View Report
                            </a>
                            <a href="/" 
                               class="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors">
                                <i class="fas fa-list mr-1"></i>All Reports
                            </a>
                        </div>
                    </div>
                `;
            } else {
                throw new Error(data.error || 'Failed to generate report');
            }
            result.classList.remove('hidden');
        }, 1000);
        
    } catch (error) {
        clearInterval(progressInterval);
        result.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <div class="flex items-center mb-2">
                    <i class="fas fa-exclamation-circle text-red-600 mr-2"></i>
                    <h3 class="font-semibold text-red-900">Generation Failed</h3>
                </div>
                <p class="text-red-800">${error.message}</p>
            </div>
        `;
        result.classList.remove('hidden');
    } finally {
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-cog mr-2"></i>Generate Intelligence Report';
        setTimeout(() => {
            progress.classList.add('hidden');
        }, 2000);
    }
});
</script>
{% endblock %}
""")

# Report detail template
REPORT_DETAIL_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<div class="mb-6">
    <a href="/" class="text-blue-600 hover:text-blue-800 font-medium">
        <i class="fas fa-arrow-left mr-1"></i>Back to Reports
    </a>
</div>

<div class="bg-white rounded-lg shadow-lg overflow-hidden">
    <div class="px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white">
        <h1 class="text-2xl font-bold">Intelligence Report</h1>
        <p class="text-blue-100">{{ report.generated_at }}</p>
    </div>
    
    <div class="p-6">
        {{ report.content | safe }}
    </div>
</div>
{% endblock %}
""")

@app.route('/')
def reports():
    """Reports listing page"""
    reports_list = list(reports_storage.values())
    reports_list.sort(key=lambda x: x['created_at'], reverse=True)
    return render_template_string(REPORTS_TEMPLATE, reports=reports_list)

@app.route('/generate')
def generate_form():
    """Generate report form"""
    return render_template_string(GENERATE_TEMPLATE)

@app.route('/reports/<report_id>')
def report_detail(report_id):
    """Report detail page"""
    if report_id not in reports_storage:
        return "Report not found", 404
    
    report = reports_storage[report_id]
    return render_template_string(REPORT_DETAIL_TEMPLATE, report=report)

@app.route('/api/generate', methods=['POST'])
def api_generate_report():
    """Generate report API"""
    try:
        data = request.get_json()
        topics = data.get('topics', [])
        
        if not topics:
            return jsonify({"error": "No topics provided"}), 400
        
        # Import and run report generation
        from sources.hackernews import HackerNewsSource
        
        async def fetch_and_generate():
            hn_source = HackerNewsSource()
            all_articles = []
            
            # Fetch from Hacker News
            for topic in topics:
                try:
                    articles = await hn_source.fetch_articles(topic, days_back=3)
                    
                    # Add metadata
                    for article in articles:
                        article['source'] = 'hackernews'
                        article['topic'] = topic
                    
                    all_articles.extend(articles[:15])  # Max 15 per topic
                    
                except Exception as e:
                    print(f"Error fetching {topic}: {e}")
            
            if not all_articles:
                return {"error": "No articles found"}
            
            # Simple ranking
            for article in all_articles:
                score = min(article.get('score', 0) / 100, 1.0)
                article['relevance_score'] = score
            
            all_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            top_articles = all_articles[:12]  # Top 12
            
            return {
                "articles": top_articles,
                "stats": {
                    "total_articles": len(all_articles),
                    "top_articles": len(top_articles),
                    "sources_used": 1
                }
            }
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(fetch_and_generate())
        loop.close()
        
        if "error" in result:
            return jsonify(result), 400
        
        # Generate HTML report
        report_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        articles = result["articles"]
        stats = result["stats"]
        
        # Create beautiful HTML report
        report_html = f"""
        <div class="space-y-8">
            <div class="border-b pb-6">
                <div class="flex items-center justify-between mb-4">
                    <div>
                        <h2 class="text-2xl font-bold text-gray-900">Executive Summary</h2>
                        <p class="text-gray-600">Intelligence analysis for: {', '.join(topics)}</p>
                    </div>
                    <div class="text-right text-sm text-gray-500">
                        <div>Report ID: {report_id[:8]}...</div>
                        <div>{created_at.strftime('%B %d, %Y at %I:%M %p')}</div>
                    </div>
                </div>
                
                <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg">
                    <div class="grid grid-cols-3 gap-6">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-blue-600">{stats['total_articles']}</div>
                            <div class="text-sm text-gray-600">Articles Found</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-indigo-600">{stats['top_articles']}</div>
                            <div class="text-sm text-gray-600">Top Articles</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-purple-600">1</div>
                            <div class="text-sm text-gray-600">Source (Demo)</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div>
                <h3 class="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                    <i class="fas fa-fire mr-2 text-orange-500"></i>
                    Top Articles & Insights
                </h3>
                
                <div class="space-y-6">
        """
        
        for i, article in enumerate(articles, 1):
            content = article.get('content', '')
            summary = content[:200] + '...' if len(content) > 200 else content or 'Trending discussion on Hacker News with significant community engagement.'
            
            report_html += f"""
                    <div class="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                        <div class="flex items-start justify-between mb-4">
                            <div class="flex-1">
                                <h4 class="text-lg font-semibold text-gray-900 mb-2">
                                    {i}. {article['title']}
                                </h4>
                                <div class="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                                    <span class="bg-orange-100 text-orange-800 px-2 py-1 rounded-full font-medium">
                                        📰 Hacker News
                                    </span>
                                    <span>👤 {article.get('author', 'Unknown')}</span>
                                    <span>📊 {article.get('score', 0)} points</span>
                                    <span>💬 {article.get('comments_count', 0)} comments</span>
                                </div>
                            </div>
                            <div class="text-right text-sm text-gray-500">
                                Relevance: {article.get('relevance_score', 0):.1f}
                            </div>
                        </div>
                        
                        <p class="text-gray-700 mb-4 leading-relaxed">{summary}</p>
                        
                        <div class="flex items-center justify-between">
                            <a href="{article['url']}" 
                               target="_blank" 
                               class="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium">
                                <i class="fas fa-external-link-alt mr-1"></i>
                                Read Full Article
                            </a>
                            <div class="text-xs text-gray-400">
                                Topic: {article.get('topic', 'General')}
                            </div>
                        </div>
                    </div>
            """
        
        report_html += """
                </div>
            </div>
            
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-6">
                <h4 class="font-semibold text-gray-900 mb-2">
                    <i class="fas fa-info-circle mr-1 text-blue-500"></i>
                    About This Report
                </h4>
                <p class="text-sm text-gray-600 mb-2">
                    This is a demonstration report using Hacker News as the primary source. 
                    The full Weekly Intelligence Agent includes comprehensive coverage from 14 sources:
                </p>
                <div class="grid grid-cols-2 gap-2 text-xs text-gray-500">
                    <div>
                        <strong>Original Sources:</strong><br>
                        • Hacker News • Reddit • Twitter<br>
                        • Product Hunt • Y Combinator • TechCrunch
                    </div>
                    <div>
                        <strong>New Sources:</strong><br>
                        • Dev.to • Medium • Substack • YouTube<br>
                        • Stack Overflow • Bluesky • arXiv • RSS Feeds
                    </div>
                </div>
            </div>
        </div>
        """
        
        # Store report
        report = {
            'id': report_id,
            'topics': topics,
            'content': report_html,
            'stats': stats,
            'created_at': created_at.isoformat(),
            'generated_at': created_at.strftime('%B %d, %Y at %I:%M %p')
        }
        
        reports_storage[report_id] = report
        
        return jsonify({
            "message": "Report generated successfully",
            "report_id": report_id,
            "stats": stats
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Complete Web Interface")
    print("📍 Open: http://localhost:5002")
    print("✨ Features: Reports listing, generation, and detailed view")
    app.run(debug=True, host='0.0.0.0', port=5002)