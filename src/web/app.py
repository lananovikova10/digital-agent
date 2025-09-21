"""
Web interface for the Weekly Intelligence Agent
"""
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import json
from datetime import datetime

app = Flask(__name__)
import os
API_BASE = os.getenv("API_BASE", "http://api:8000")

def get_source_color(source):
    """Get color for source badges"""
    colors = {
        'hackernews': 'orange',
        'reddit': 'red', 
        'twitter': 'blue',
        'producthunt': 'purple',
        'yc_launches': 'yellow',
        'techcrunch': 'green'
    }
    return colors.get(source.lower(), 'gray')

def parse_sources_from_content(content):
    """Parse source articles from report content"""
    import re
    
    sources = []
    
    # Find the sources section
    sources_section_match = re.search(r'SOURCE ARTICLES & KEY INSIGHTS:(.*?)$', content, re.DOTALL)
    if not sources_section_match:
        return sources
    
    sources_text = sources_section_match.group(1)
    
    # Split by source entries (look for [number] pattern)
    source_entries = re.split(r'\n\[(\d+)\]\s+', sources_text)[1:]  # Skip first empty part
    
    # Process entries in pairs (number, content)
    for i in range(0, len(source_entries), 2):
        if i + 1 >= len(source_entries):
            break
            
        number = source_entries[i]
        entry_content = source_entries[i + 1]
        
        # Parse the entry content
        lines = entry_content.strip().split('\n')
        
        # Extract title (first line)
        title = lines[0].strip() if lines else ""
        
        # Find source line
        source_line = next((line for line in lines if line.strip().startswith('Source:')), "")
        source_match = re.search(r'Source:\s+(\w+)\s*\|\s*Author:\s*(.+?)\s*\|\s*Published:\s*(.+?)$', source_line)
        
        if not source_match:
            continue
            
        source = source_match.group(1).strip().lower()
        author = source_match.group(2).strip()
        published_at = source_match.group(3).strip()
        
        # Find engagement line
        engagement_line = next((line for line in lines if 'Engagement:' in line), "")
        engagement_match = re.search(r'Engagement:\s*(.+?)\s*\|\s*Quality Score:\s*(.+?)$', engagement_line)
        
        if engagement_match:
            engagement_text = engagement_match.group(1)
            quality_text = engagement_match.group(2)
            
            # Parse engagement numbers
            eng_numbers = re.search(r'(\d+)\s+points?,\s*(\d+)\s+comments?', engagement_text)
            score = int(eng_numbers.group(1)) if eng_numbers else 0
            comments_count = int(eng_numbers.group(2)) if eng_numbers else 0
            
            # Parse quality score
            quality_match = re.search(r'([\d.]+)/1\.0', quality_text)
            ranking_score = float(quality_match.group(1)) if quality_match else 0.0
        else:
            score = 0
            comments_count = 0
            ranking_score = 0.0
        
        # Find URL line
        url_line = next((line for line in lines if line.strip().startswith('URL:')), "")
        url = url_line.replace('URL:', '').strip() if url_line else ""
        
        # Find summary
        summary_start = next((i for i, line in enumerate(lines) if line.strip().startswith('Summary:')), -1)
        if summary_start >= 0:
            summary_lines = []
            for line in lines[summary_start:]:
                if line.strip().startswith('Summary:'):
                    summary_lines.append(line.replace('Summary:', '').strip())
                elif line.strip().startswith('Key Quote:'):
                    break
                elif line.strip() and not line.strip() == '---':
                    summary_lines.append(line.strip())
            summary = ' '.join(summary_lines).strip()
        else:
            summary = ""
        
        # Find key quote
        key_quote_start = next((i for i, line in enumerate(lines) if line.strip().startswith('Key Quote:')), -1)
        if key_quote_start >= 0:
            key_quote_lines = []
            for line in lines[key_quote_start:]:
                if line.strip().startswith('Key Quote:'):
                    key_quote_lines.append(line.replace('Key Quote:', '').strip())
                elif line.strip() == '---':
                    break
                elif line.strip():
                    key_quote_lines.append(line.strip())
            key_quote = ' '.join(key_quote_lines).strip().strip('"')
        else:
            key_quote = ""
        
        # Decode HTML entities in all text fields
        import html
        title = html.unescape(title) if title else ""
        author = html.unescape(author) if author else ""
        summary = html.unescape(summary) if summary else ""
        key_quote = html.unescape(key_quote) if key_quote else ""
        
        sources.append({
            'title': title,
            'source': source,
            'author': author,
            'published_at': published_at,
            'url': url,
            'score': score,
            'comments_count': comments_count,
            'ranking_score': ranking_score,
            'summary': summary,
            'key_quote': key_quote,
            'source_color': get_source_color(source)
        })
    
    return sources

def remove_sources_section_from_content(content):
    """Remove the sources section from report content to avoid duplication"""
    import re
    
    # Find and remove everything from "SOURCE ARTICLES & KEY INSIGHTS:" to the end
    content_without_sources = re.sub(
        r'SOURCE ARTICLES & KEY INSIGHTS:.*$', 
        '', 
        content, 
        flags=re.DOTALL
    ).strip()
    
    return content_without_sources

@app.route('/')
def reports():
    """Display all reports"""
    try:
        response = requests.get(f"{API_BASE}/reports?limit=20")
        if response.status_code == 200:
            reports_data = response.json()
            return render_template('reports.html', reports=reports_data)
        else:
            return render_template('reports.html', reports=[], error="Failed to fetch reports")
    except Exception as e:
        return render_template('reports.html', reports=[], error=str(e))

@app.route('/reports/<report_id>')
def report_detail(report_id):
    """Display detailed report view"""
    try:
        # Get report details
        response = requests.get(f"{API_BASE}/reports/{report_id}")
        if response.status_code != 200:
            return render_template('error.html', message="Report not found"), 404
            
        report = response.json()
        
        # Parse sources from report content
        report['sources'] = parse_sources_from_content(report.get('content', ''))
        
        # Remove the sources section from content to avoid duplication
        report['content'] = remove_sources_section_from_content(report.get('content', ''))
        
        return render_template('report_detail.html', report=report)
        
    except Exception as e:
        return render_template('error.html', message=str(e)), 500

@app.route('/generate')
def generate_form():
    """Show report generation form"""
    return render_template('generate.html')

@app.route('/api/reports/generate', methods=['POST'])
def api_generate_report():
    """Proxy to the main API for report generation"""
    try:
        data = request.get_json()
        response = requests.post(
            f"{API_BASE}/reports/generate",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.template_filter('format_date')
def format_date(date_string):
    """Format date for display"""
    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        return date_string

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)