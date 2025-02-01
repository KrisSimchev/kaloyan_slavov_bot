from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

# Define Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def authenticate_gmail():
    """Authenticate and generate a Gmail API token."""
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)

    # Save credentials for future use
    with open("token.pkl", "wb") as token_file:
        pickle.dump(creds, token_file)

    print("✅ Authentication successful! Token saved as 'token.pkl'.")

authenticate_gmail()
