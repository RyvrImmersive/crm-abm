from google.ads.googleads.client import GoogleAdsClient
from google_auth_oauthlib.flow import InstalledAppFlow
import json

# Replace these with your values
CLIENT_ID = "1009112650822-qnnsvlogb5a0rmjemiju51dlg6lusqrn.apps.googleusercontent.com"
CLIENT_SECRET = "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"
DEVELOPER_TOKEN = "IzxehPn_AorJPPUw0MWQlg"
CUSTOMER_ID = "9860039107"  # Removed hyphens

# Configure the flow
SCOPES = ['https://www.googleapis.com/auth/adwords']
REDIRECT_URI = 'http://localhost:8080'

# Run the OAuth flow
flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uris": [REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=SCOPES
)

# This will open a browser window for authentication
print("Opening browser for authentication...")
credentials = flow.run_local_server(port=8080)

# Print the refresh token
print("\n=== Authentication Successful ===")
print(f"Refresh Token: {credentials.refresh_token}")
print(f"Access Token: {credentials.token}")
print(f"Token Expiry: {credentials.expiry}")

# Save credentials to a file
with open('google-ads-secrets.json', 'w') as f:
    json.dump({
        'refresh_token': credentials.refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'developer_token': DEVELOPER_TOKEN,
        'login_customer_id': CUSTOMER_ID
    }, f, indent=2)

print("\nCredentials saved to google-ads-secrets.json")
print("You can now use these credentials in your .env file")