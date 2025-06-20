#!/usr/bin/env python3
"""
Script to verify Google Ads customer ID and credentials
"""

import os
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def verify_customer_access(customer_id: str):
    """Verify if the customer ID is accessible with current credentials"""
    try:
        # Initialize client
        print("🔄 Initializing Google Ads client...")
        client = GoogleAdsClient.load_from_storage("google-ads.yaml")
        print("✅ Client initialized successfully")
        
        # Get Google Ads service
        ga_service = client.get_service("GoogleAdsService")
        
        # Try to get customer info
        print(f"🔄 Verifying access to customer ID: {customer_id}")
        
        # Create a query to verify access
        query = f"""
            SELECT customer.id, customer.descriptive_name, customer.currency_code, customer.time_zone, customer.manager
            FROM customer
            WHERE customer.id = {customer_id}
        """
        
        # Make a simple request to verify access
        response = ga_service.search(request={"query": query, "customer_id": customer_id})
        
        if response.results:
            customer = response.results[0]
            print("✅ Customer access verified!")
            print(f"   Customer ID: {customer.customer.id}")
            print(f"   Descriptive Name: {customer.customer.descriptive_name}")
            print(f"   Currency Code: {customer.customer.currency_code}")
            print(f"   Time Zone: {customer.customer.time_zone}")
            print(f"   Manager: {customer.customer.manager}")
            return True
        else:
            print("❌ Customer access not verified!")
            return False
        
    except GoogleAdsException as ex:
        print("❌ Google Ads API Error:")
        print(f"   Request ID: {ex.request_id}")
        for error in ex.failure.errors:
            print(f"   Error: {error.message}")
            print(f"   Error Code: {error.error_code}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def list_accessible_customers():
    """List all customers accessible with current credentials"""
    try:
        print("\n🔄 Listing all accessible customers...")
        client = GoogleAdsClient.load_from_storage("google-ads.yaml")
        
        customer_service = client.get_service("CustomerService")
        
        # Get list of accessible customers
        accessible_customers = customer_service.list_accessible_customers()
        
        print("✅ Accessible customers:")
        for customer_resource in accessible_customers.resource_names:
            customer_id = customer_resource.split('/')[-1]
            print(f"   Customer ID: {customer_id}")
            
            # Get detailed info for each customer
            try:
                request = client.get_type("GetCustomerRequest")
                request.customer_id = customer_id
                customer = customer_service.get_customer(request=request)
                print(f"      Name: {customer.descriptive_name}")
                print(f"      Manager: {customer.manager}")
                print(f"      Currency: {customer.currency_code}")
                print()
            except Exception as e:
                print(f"      Error getting details: {str(e)}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error listing customers: {str(e)}")
        return False

if __name__ == "__main__":
    # Get customer ID from environment or prompt
    customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    
    if not customer_id:
        customer_id = input("Enter your Google Ads Customer ID (10 digits, no hyphens): ").strip()
    
    print(f"Testing customer ID: {customer_id}")
    print("=" * 50)
    
    # First, list all accessible customers
    list_accessible_customers()
    
    # Then verify the specific customer ID
    if customer_id:
        print("=" * 50)
        verify_customer_access(customer_id)
    
    print("\n" + "=" * 50)
    print("Verification complete!")
