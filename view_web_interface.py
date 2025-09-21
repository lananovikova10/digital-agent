#!/usr/bin/env python3
"""
Simple script to test the web interface
"""
import requests
import webbrowser
import time

def test_web_interface():
    """Test the web interface and open it in browser"""
    web_url = "http://localhost:3000"
    
    print("🌐 Testing web interface...")
    
    try:
        # Test if web interface is running
        response = requests.get(web_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Web interface is running at {web_url}")
            
            # Test API endpoints
            api_url = "http://localhost:8000"
            
            # Test reports endpoint
            reports_response = requests.get(f"{api_url}/reports?limit=3")
            if reports_response.status_code == 200:
                reports = reports_response.json()
                print(f"📊 Found {len(reports)} reports")
                
                if reports:
                    latest_report = reports[0]
                    report_id = latest_report['report_id']
                    print(f"📄 Latest report: {report_id}")
                    
                    # Test report detail page
                    report_url = f"{web_url}/reports/{report_id}"
                    print(f"🔗 Report URL: {report_url}")
                    
                    # Open in browser
                    print("🚀 Opening web interface in browser...")
                    webbrowser.open(web_url)
                    
                    return True
            
        else:
            print(f"❌ Web interface not responding: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to web interface: {e}")
        return False

def main():
    print("🎯 Weekly Intelligence Agent - Web Interface Test")
    print("=" * 50)
    
    if test_web_interface():
        print("\n✅ Web interface is ready!")
        print("🌐 Visit: http://localhost:3000")
        print("📊 API: http://localhost:8000")
        print("\n🎉 Your visual intelligence dashboard is operational!")
    else:
        print("\n❌ Web interface test failed")
        print("🔧 Try: docker compose up -d web")

if __name__ == "__main__":
    main()