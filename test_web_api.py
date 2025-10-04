#!/usr/bin/env python3
"""
Test the web API report generation
"""
import requests
import json
import time

def test_report_generation():
    """Test the report generation API"""
    print("🧪 Testing Web API Report Generation")
    print("=" * 50)
    
    # API endpoint
    api_url = "http://localhost:8000/reports/generate"
    
    # Test data
    test_data = {
        "topics": ["MCP", "AI for software developers"],
        "days_back": 7
    }
    
    print(f"📋 Testing with topics: {test_data['topics']}")
    print(f"🔍 Sending request to: {api_url}")
    
    try:
        # Send request
        print("⏳ Generating report...")
        start_time = time.time()
        
        response = requests.post(
            api_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Request completed in {duration:.1f} seconds")
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Report generated successfully!")
            print(f"📄 Report ID: {result.get('report_id')}")
            print(f"📈 Stats: {result.get('stats', {})}")
            
            # Test fetching the report
            report_id = result.get('report_id')
            if report_id:
                print(f"\\n🔍 Fetching generated report...")
                report_response = requests.get(f"http://localhost:8000/reports/{report_id}")
                
                if report_response.status_code == 200:
                    report_data = report_response.json()
                    print("✅ Report fetched successfully!")
                    print(f"📝 Content length: {len(report_data.get('content', ''))} characters")
                    print(f"📅 Created: {report_data.get('created_at')}")
                    
                    # Show preview of content
                    content = report_data.get('content', '')
                    if content:
                        lines = content.split('\\n')
                        print(f"\\n📖 Content preview (first 10 lines):")
                        for i, line in enumerate(lines[:10]):
                            if line.strip():
                                print(f"   {line}")
                else:
                    print(f"❌ Failed to fetch report: {report_response.status_code}")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Error: {response.text}")
    
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (>5 minutes)")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - is the API server running on localhost:8000?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_report_generation()