from google_auth_oauthlib.flow import InstalledAppFlow

# OAuth 2.0 configuration
SCOPES = ['https://www.googleapis.com/auth/adwords']
CLIENT_SECRETS_FILE = 'client_secrets.json'

def get_refresh_token():
    # Create the flow using the client secrets file
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES
    )
    
    # Run the local server flow with consent prompt
    credentials = flow.run_local_server(
        port=8080,
        prompt='consent',
        access_type='offline'
    )
    
    # Print the refresh token
    print("\nRefresh Token:", credentials.refresh_token)
    print("\nCopy this token and add it to your google-ads.yaml file")

if __name__ == "__main__":
    get_refresh_token()