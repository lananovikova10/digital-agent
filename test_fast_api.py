#!/usr/bin/env python3
"""
Quick test of the optimized API
"""
import requests
import time

def test_fast_generation():
    """Test the optimized report generation"""
    print("⚡ Testing Optimized Report Generation")
    print("=" * 40)
    
    api_url = "http://localhost:8000/reports/generate/fast"
    
    test_data = {
        "topics": ["MCP"],  # Single topic for speed
        "days_back": 3      # Shorter timeframe
    }
    
    print(f"📋 Topic: {test_data['topics'][0]}")
    print("⏳ Starting generation...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            api_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=120  # 2 minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Completed in {duration:.1f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📄 Report ID: {result.get('report_id')}")
            
            stats = result.get('stats', {})
            print(f"📊 Stats:")
            print(f"   • Total articles: {stats.get('total_articles', 0)}")
            print(f"   • Top articles: {stats.get('top_articles', 0)}")
            print(f"   • Sources used: {stats.get('sources_used', 0)}")
            
            if duration < 60:
                print("🚀 Good performance! Under 1 minute")
            elif duration < 120:
                print("⚠️  Acceptable performance (1-2 minutes)")
            else:
                print("🐌 Slow performance (>2 minutes)")
                
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text[:200])
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout (>2 minutes)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_fast_generation()