#!/usr/bin/env python3
"""
Simple script to generate and display reports
"""
import requests
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:8000"

def generate_report(topics):
    """Generate a new report"""
    print(f"Generating report for topics: {', '.join(topics)}")
    
    response = requests.post(
        f"{API_BASE}/reports/generate",
        json={"topics": topics}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Report generated successfully!")
        print(f"Report ID: {result['report_id']}")
        return result['report_id']
    else:
        print(f"❌ Error: {response.text}")
        return None

def get_latest_report():
    """Get the latest report"""
    response = requests.get(f"{API_BASE}/reports?limit=1")
    
    if response.status_code == 200:
        reports = response.json()
        if reports:
            return reports[0]
    return None

def display_report(report):
    """Display a report nicely"""
    print("\n" + "="*80)
    print("WEEKLY INTELLIGENCE REPORT")
    print("="*80)
    print(f"Generated: {report['created_at']}")
    print(f"Topics: {', '.join(report['topics'])}")
    print("\n" + "-"*80)
    print(report['content'])
    print("="*80)

def main():
    if len(sys.argv) > 1:
        # Generate new report with provided topics
        topics = sys.argv[1:]
        report_id = generate_report(topics)
        
        if report_id:
            # Get the generated report
            response = requests.get(f"{API_BASE}/reports/{report_id}")
            if response.status_code == 200:
                report = response.json()
                display_report(report)
    else:
        # Show latest report
        print("Getting latest report...")
        report = get_latest_report()
        
        if report:
            display_report(report)
        else:
            print("No reports found. Generate one with:")
            print("python generate_report.py AI 'machine learning' startup")

if __name__ == "__main__":
    main()