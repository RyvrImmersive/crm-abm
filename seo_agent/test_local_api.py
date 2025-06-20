#!/usr/bin/env python3
"""
Test script for local Google Ads API keyword research endpoint
"""

import requests
import json
import time

def test_keyword_research_api():
    """Test the keyword research API endpoint"""
    
    # API endpoint
    url = "http://localhost:8000/api/keyword-research"
    
    # Test data
    test_data = {
        "keywords": ["digital marketing", "SEO services"],
        "location_id": 2356,  # United States
        "language_id": 1000   # English
    }
    
    print("🔄 Testing Keyword Research API...")
    print(f"📍 URL: {url}")
    print(f"📝 Request Data: {json.dumps(test_data, indent=2)}")
    print("=" * 50)
    
    try:
        # Make the API request
        print("⏳ Sending request...")
        start_time = time.time()
        
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Response time: {duration:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            data = response.json()
            print(f"📈 Found {len(data)} keyword suggestions")
            
            # Display first 10 results
            print("\n🔍 Top 10 Keyword Suggestions:")
            print("-" * 80)
            print(f"{'Keyword':<30} {'Searches':<12} {'Competition':<15}")
            print("-" * 80)
            
            for i, result in enumerate(data[:10]):
                keyword = result.get('keyword', 'N/A')[:28]
                searches = result.get('avg_monthly_searches', 'N/A')
                competition = result.get('competition', 'N/A')
                print(f"{keyword:<30} {searches:<12} {competition:<15}")
            
            if len(data) > 10:
                print(f"... and {len(data) - 10} more results")
                
        else:
            print("❌ FAILED!")
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (30 seconds)")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - is the server running?")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def test_health_check():
    """Test the health check endpoint"""
    try:
        print("\n🏥 Testing Health Check...")
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Testing Local SEO Agent API")
    print("=" * 50)
    
    # Test health check first
    test_health_check()
    
    # Test keyword research
    test_keyword_research_api()
    
    print("\n" + "=" * 50)
    print("🏁 Testing complete!")
