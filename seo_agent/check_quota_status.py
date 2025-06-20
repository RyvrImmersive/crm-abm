# Save the quota check script

#!/usr/bin/env python3
"""
Check Google Ads API quota and account status
"""

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_account_status():
    """Check Google Ads account status and accessible customers"""
    try:
        client = GoogleAdsClient.load_from_storage("google-ads.yaml")
        
        print("=" * 60)
        print("Google Ads Account Status Check")
        print("=" * 60)
        print(f"Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        # Get customer service
        customer_service = client.get_service("CustomerService")
        
        # List accessible customers
        print("\n📋 Accessible Customer Accounts:")
        accessible_customers = customer_service.list_accessible_customers()
        
        if not accessible_customers.resource_names:
            print("❌ No accessible customer accounts found!")
            return
        
        for i, resource_name in enumerate(accessible_customers.resource_names, 1):
            customer_id = resource_name.split('/')[-1]
            print(f"  {i}. Customer ID: {customer_id}")
            
            # Try to get customer details
            try:
                ga_service = client.get_service("GoogleAdsService")
                query = f"""
                    SELECT 
                        customer.id,
                        customer.descriptive_name,
                        customer.currency_code,
                        customer.time_zone,
                        customer.test_account
                    FROM customer
                    WHERE customer.id = {customer_id}
                    LIMIT 1
                """
                
                response = ga_service.search(customer_id=customer_id, query=query)
                
                for row in response:
                    customer = row.customer
                    print(f"     Name: {customer.descriptive_name or 'N/A'}")
                    print(f"     Currency: {customer.currency_code}")
                    print(f"     Time Zone: {customer.time_zone}")
                    print(f"     Test Account: {'Yes' if customer.test_account else 'No'}")
                    
                    if customer.test_account:
                        print("     ⚠️  WARNING: This is a TEST account with limited functionality!")
                    
            except Exception as e:
                print(f"     ⚠️  Could not fetch details: {str(e)}")
            
            print()
        
        # Check API access level
        print("\n📊 API Access Information:")
        print("  • Standard Access: Full API functionality")
        print("  • Test Account Access: Limited to 15,000 operations/day")
        print("  • Basic Access: Limited to 15,000 operations/day")
        
        print("\n💡 Rate Limit Information:")
        print("  • Keyword Planner: ~1,000 requests per day")
        print("  • Per-method limit: Usually 1-2 requests per second")
        print("  • Daily operation limit: Depends on access level")
        
        print("\n🔧 Troubleshooting Tips:")
        print("  1. Wait 5-10 minutes before retrying")
        print("  2. Reduce request frequency")
        print("  3. Use smaller keyword batches")
        print("  4. Check if using a test account")
        print("  5. Apply for standard access if needed")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking account status: {str(e)}")
        return False

def estimate_quota_reset():
    """Estimate when quota might reset"""
    from datetime import datetime, timedelta
    
    # Google Ads typically resets quota at midnight Pacific Time
    now = datetime.now()
    
    print("\n⏰ Estimated Quota Reset Time:")
    print(f"  Quota typically resets at midnight Pacific Time")
    print(f"  Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Try again in 30-60 minutes if you're hitting rate limits")

if __name__ == "__main__":
    success = check_account_status()
    estimate_quota_reset()
    
    if success:
        print("\n✅ Account check completed successfully")
    else:
        print("\n❌ Account check failed")
