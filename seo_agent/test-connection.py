from google.ads.googleads.client import GoogleAdsClient

client = GoogleAdsClient.load_from_env()
customer_service = client.get_service("CustomerService")
customer = customer_service.get_customer(resource_name=f"customers/{client.login_customer_id}")
print(f"Successfully connected to customer ID: {customer.id}")