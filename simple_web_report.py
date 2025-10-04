#!/usr/bin/env python3
"""
Simple web interface for report generation without database
"""
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template_string, request, jsonify
import asyncio
import sys
import os
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

# Simple HTML template
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Weekly Intelligence Agent</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <div class="max-w-2xl mx-auto">
            <div class="bg-white rounded-lg shadow-lg p-8">
                <h1 class="text-3xl font-bold text-gray-900 mb-6">
                    <i class="fas fa-brain mr-2 text-blue-600"></i>
                    Weekly Intelligence Agent
                </h1>
                
                <form id="generateForm" class="space-y-6">
                    <div>
                        <label for="topics" class="block text-sm font-medium text-gray-700 mb-2">
                            Topics to Analyze
                        </label>
                        <input type="text" 
                               id="topics" 
                               name="topics" 
                               placeholder="e.g., MCP, AI, machine learning"
                               class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                               required>
                    </div>

                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h3 class="font-semibold text-blue-900 mb-2">
                            <i class="fas fa-info-circle mr-1"></i>
                            Fast Mode
                        </h3>
                        <p class="text-sm text-blue-800">
                            This demo uses Hacker News only for fast results (under 30 seconds).
                            Full version includes 14 sources: Dev.to, Medium, arXiv, Stack Overflow, and more.
                        </p>
                    </div>

                    <button type="submit" 
                            id="generateBtn"
                            class="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors font-medium">
                        <i class="fas fa-cog mr-2"></i>
                        Generate Report
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
        const progressInterval = setInterval(() => {
            if (progressValue < 90) {
                progressValue += Math.random() * 20;
                progressBar.style.width = Math.min(progressValue, 90) + '%';
            }
        }, 500);
        
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ topics: topics })
            });
            
            const data = await response.json();
            
            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            progressText.textContent = 'Complete!';
            
            setTimeout(() => {
                if (response.ok) {
                    result.innerHTML = `
                        <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                            <h3 class="font-semibold text-green-900 mb-4">
                                <i class="fas fa-check-circle mr-2"></i>Report Generated!
                            </h3>
                            <div class="prose max-w-none">
                                <div class="bg-white p-6 rounded border">
                                    ${data.report_html}
                                </div>
                            </div>
                            <div class="mt-4 text-sm text-green-700">
                                <strong>Stats:</strong> ${data.stats.total_articles} articles found, ${data.stats.top_articles} selected
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
                    <h3 class="font-semibold text-red-900 mb-2">
                        <i class="fas fa-exclamation-circle mr-2"></i>Generation Failed
                    </h3>
                    <p class="text-red-800">${error.message}</p>
                </div>
            `;
            result.classList.remove('hidden');
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-cog mr-2"></i>Generate Report';
            setTimeout(() => {
                progress.classList.add('hidden');
            }, 2000);
        }
    });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page"""
    return render_template_string(TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate_report():
    """Generate report without database"""
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
                    
                    all_articles.extend(articles[:10])  # Max 10 per topic
                    
                except Exception as e:
                    print(f"Error fetching {topic}: {e}")
            
            if not all_articles:
                return {"error": "No articles found"}
            
            # Simple ranking
            for article in all_articles:
                score = min(article.get('score', 0) / 100, 1.0)
                article['relevance_score'] = score
            
            all_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            top_articles = all_articles[:10]
            
            # Generate HTML report
            report_html = f"""
            <div class="space-y-6">
                <div class="border-b pb-4">
                    <h2 class="text-2xl font-bold text-gray-900">Intelligence Report</h2>
                    <p class="text-gray-600">{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <div class="bg-blue-50 p-4 rounded-lg">
                    <h3 class="font-semibold text-blue-900 mb-2">📊 Summary</h3>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span class="font-medium">Topics:</span> {', '.join(topics)}
                        </div>
                        <div>
                            <span class="font-medium">Articles Found:</span> {len(all_articles)}
                        </div>
                        <div>
                            <span class="font-medium">Top Articles:</span> {len(top_articles)}
                        </div>
                        <div>
                            <span class="font-medium">Source:</span> Hacker News
                        </div>
                    </div>
                </div>
                
                <div>
                    <h3 class="text-xl font-semibold text-gray-900 mb-4">🔥 Top Articles</h3>
                    <div class="space-y-4">
            """
            
            for i, article in enumerate(top_articles, 1):
                content = article.get('content', '')
                summary = content[:150] + '...' if len(content) > 150 else content or 'No summary available.'
                
                report_html += f"""
                        <div class="border rounded-lg p-4 hover:shadow-md transition-shadow">
                            <div class="flex items-start justify-between mb-2">
                                <h4 class="font-semibold text-lg text-gray-900 flex-1">
                                    {i}. {article['title']}
                                </h4>
                                <span class="bg-orange-100 text-orange-800 px-2 py-1 rounded text-sm ml-2">
                                    📰 HN
                                </span>
                            </div>
                            
                            <div class="text-sm text-gray-600 mb-3">
                                <span class="font-medium">👤 {article.get('author', 'Unknown')}</span>
                                <span class="mx-2">•</span>
                                <span>📊 {article.get('score', 0)} points</span>
                                <span class="mx-2">•</span>
                                <span>💬 {article.get('comments_count', 0)} comments</span>
                            </div>
                            
                            <p class="text-gray-700 mb-3">{summary}</p>
                            
                            <a href="{article['url']}" 
                               target="_blank" 
                               class="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium">
                                🔗 Read Article
                                <i class="fas fa-external-link-alt ml-1 text-xs"></i>
                            </a>
                        </div>
                """
            
            report_html += """
                    </div>
                </div>
                
                <div class="bg-gray-50 p-4 rounded-lg text-sm text-gray-600">
                    <p><strong>Note:</strong> This is a demo using Hacker News only. The full version includes 14 sources: Dev.to, Medium, arXiv, Stack Overflow, Substack, YouTube, RSS feeds, and more for comprehensive coverage.</p>
                </div>
            </div>
            """
            
            return {
                "report_html": report_html,
                "stats": {
                    "total_articles": len(all_articles),
                    "top_articles": len(top_articles)
                }
            }
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(fetch_and_generate())
        loop.close()
        
        if "error" in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Simple Web Interface")
    print("📍 Open: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)