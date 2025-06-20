#!/usr/bin/env python3
"""
Test script for Google Ads API keyword research functionality
"""

from keyword_research import get_keyword_ideas_for_langflow
import json
import sys

def test_basic_functionality():
    """Test basic keyword research functionality"""
    print("=" * 60)
    print("Testing Google Ads Keyword Research")
    print("=" * 60)
    
    # Test keywords
    test_keywords = [
        "digital marketing",
        "seo services",
        "web development"
    ]
    
    print(f"\nTesting with keywords: {', '.join(test_keywords)}")
    print(f"Location: India (ID: 2356)")
    print(f"Language: English (ID: 1000)")
    print("-" * 60)
    
    try:
        # Call the function
        results = get_keyword_ideas_for_langflow(
            keywords=test_keywords,
            location_id=2356,  # India
            language_id=1000   # English
        )
        
        # Display results
        print(f"\n✅ SUCCESS! Found {len(results)} keyword ideas\n")
        
        # Show first 10 results
        for i, result in enumerate(results[:10], 1):
            print(f"{i}. {result['keyword']}")
            print(f"   Monthly Searches: {result['avg_monthly_searches']:,}")
            print(f"   Competition: {result['competition']}")
            print()
        
        if len(results) > 10:
            print(f"... and {len(results) - 10} more results")
        
        # Save full results to file
        with open('keyword_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Full results saved to: keyword_results.json")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        print("\nPossible issues to check:")
        print("1. Is google-ads.yaml configured correctly?")
        print("2. Do you have valid API credentials?")
        print("3. Is the customer ID accessible?")
        print("4. Do you have Keyword Planner access?")
        return False

def test_error_handling():
    """Test error handling with invalid inputs"""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    # Test with empty keywords
    print("\nTesting with empty keywords list...")
    try:
        results = get_keyword_ideas_for_langflow(keywords=[])
        print(f"Result: {len(results)} ideas (might be 0)")
    except Exception as e:
        print(f"Error (expected): {type(e).__name__}: {str(e)}")
    
    # Test with invalid location
    print("\nTesting with invalid location ID...")
    try:
        results = get_keyword_ideas_for_langflow(
            keywords=["test"],
            location_id=99999999  # Invalid location
        )
        print(f"Result: {len(results)} ideas")
    except Exception as e:
        print(f"Error (expected): {type(e).__name__}: {str(e)}")

def check_configuration():
    """Check if Google Ads configuration file exists"""
    print("\n" + "=" * 60)
    print("Checking Configuration")
    print("=" * 60)
    
    import os
    
    config_file = "google-ads.yaml"
    if os.path.exists(config_file):
        print(f"✅ Configuration file '{config_file}' found")
        
        # Check file contents (without revealing secrets)
        with open(config_file, 'r') as f:
            content = f.read()
            required_fields = [
                'developer_token',
                'client_id', 
                'client_secret',
                'refresh_token'
            ]
            
            print("\nRequired fields:")
            for field in required_fields:
                if field in content:
                    print(f"  ✅ {field}: Present")
                else:
                    print(f"  ❌ {field}: Missing")
                    
            # Check optional fields
            if 'login_customer_id' in content:
                print(f"  ℹ️  login_customer_id: Present (optional)")
            else:
                print(f"  ℹ️  login_customer_id: Not set (optional)")
                
    else:
        print(f"❌ Configuration file '{config_file}' not found!")
        print("\nCreate a google-ads.yaml file with this structure:")
        print("""
developer_token: YOUR_DEVELOPER_TOKEN
client_id: YOUR_CLIENT_ID
client_secret: YOUR_CLIENT_SECRET  
refresh_token: YOUR_REFRESH_TOKEN
# login_customer_id: YOUR_LOGIN_CUSTOMER_ID  # Optional
""")

if __name__ == "__main__":
    # Check configuration first
    check_configuration()
    
    # Test basic functionality
    print("\n" + "=" * 60)
    success = test_basic_functionality()
    
    # Test error handling if basic test passed
    if success:
        test_error_handling()
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)