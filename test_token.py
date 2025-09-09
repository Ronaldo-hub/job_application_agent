#!/usr/bin/env python3
"""
Test token retrieval and create token.json if needed
"""

import os
import json
from dotenv import load_dotenv
from gmail_tool import get_token

def main():
    # Load environment variables
    load_dotenv()

    print("🔍 Testing token retrieval...")

    # Get token from database
    refresh_token = get_token('test_user')

    if refresh_token:
        print("✅ Token found in database!")
        print(f"Token: {refresh_token[:20]}...")

        # Get environment variables
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

        print(f"Client ID: {client_id}")
        print(f"Client Secret: {client_secret[:10] if client_secret else None}...")

        # Create token.json file
        token_data = {
            'user_id': 'test_user',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
            'token_uri': 'https://oauth2.googleapis.com/token'
        }

        with open('token.json', 'w') as f:
            json.dump(token_data, f, indent=2)

        print("✅ Created token.json file")

        # Test credentials creation
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request

            creds = Credentials.from_authorized_user_info(token_data)

            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                print("✅ Credentials refreshed successfully!")

            print("🎉 Gmail OAuth setup is COMPLETE!")
            return True

        except Exception as e:
            print(f"❌ Error testing credentials: {e}")
            return False
    else:
        print("❌ No token found in database")
        return False

if __name__ == "__main__":
    main()