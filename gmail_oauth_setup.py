#!/usr/bin/env python3
"""
Gmail OAuth Setup Script for Job Application Agent
This script helps you set up Gmail API access for email scanning functionality.
"""

import os
import json
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GmailOAuthSetup:
    """Handles Gmail OAuth setup and configuration"""

    def __init__(self):
        self.credentials_file = 'credentials.json'
        self.token_file = 'token.json'
        self.env_file = '.env'
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly']

    def check_existing_setup(self):
        """Check if Gmail OAuth is already configured"""
        logger.info("🔍 Checking existing Gmail OAuth setup...")

        # Check for credentials file
        if not os.path.exists(self.credentials_file):
            logger.warning("❌ credentials.json not found")
            return False

        # Check for environment variables
        google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

        if not google_client_id or not google_client_secret:
            logger.warning("❌ GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set in .env")
            return False

        # Check for token file (user authorization)
        if not os.path.exists(self.token_file):
            logger.warning("❌ token.json not found (user not authorized yet)")
            return False

        logger.info("✅ Gmail OAuth appears to be configured")
        return True

    def create_credentials_file(self):
        """Guide user through creating credentials.json"""
        logger.info("📝 Setting up credentials.json...")

        print("\n" + "="*60)
        print("🔐 GMAIL API SETUP - STEP 1: Create Credentials")
        print("="*60)
        print("""
To set up Gmail API access, you need to:

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file
5. Rename downloaded file to 'credentials.json' and place in project root

Your credentials.json should look like this:
{
  "installed": {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "client_secret": "your-client-secret",
    "redirect_uris": ["http://localhost"]
  }
}
        """)

        # Check if credentials file exists
        if os.path.exists(self.credentials_file):
            print(f"✅ Found {self.credentials_file}")
            try:
                with open(self.credentials_file, 'r') as f:
                    creds_data = json.load(f)

                client_id = creds_data.get('installed', {}).get('client_id', '')
                if client_id:
                    print(f"✅ Client ID: {client_id[:50]}...")
                    return True
                else:
                    print("❌ Invalid credentials.json format")
                    return False
            except Exception as e:
                print(f"❌ Error reading credentials.json: {e}")
                return False
        else:
            print(f"❌ {self.credentials_file} not found")
            print("Please create credentials.json as described above, then run this script again.")
            return False

    def update_env_file(self):
        """Update .env file with Google OAuth credentials"""
        logger.info("📝 Updating .env file with Google credentials...")

        if not os.path.exists(self.credentials_file):
            logger.error("❌ credentials.json not found")
            return False

        try:
            with open(self.credentials_file, 'r') as f:
                creds_data = json.load(f)

            client_id = creds_data.get('installed', {}).get('client_id', '')
            client_secret = creds_data.get('installed', {}).get('client_secret', '')

            if not client_id or not client_secret:
                logger.error("❌ Could not extract client_id and client_secret from credentials.json")
                return False

            # Read existing .env file
            env_lines = []
            if os.path.exists(self.env_file):
                with open(self.env_file, 'r') as f:
                    env_lines = f.readlines()

            # Update or add Google credentials
            updated_lines = []
            google_client_id_found = False
            google_client_secret_found = False

            for line in env_lines:
                if line.startswith('GOOGLE_CLIENT_ID='):
                    updated_lines.append(f'GOOGLE_CLIENT_ID={client_id}\n')
                    google_client_id_found = True
                elif line.startswith('GOOGLE_CLIENT_SECRET='):
                    updated_lines.append(f'GOOGLE_CLIENT_SECRET={client_secret}\n')
                    google_client_secret_found = True
                else:
                    updated_lines.append(line)

            # Add missing lines
            if not google_client_id_found:
                updated_lines.append(f'GOOGLE_CLIENT_ID={client_id}\n')
            if not google_client_secret_found:
                updated_lines.append(f'GOOGLE_CLIENT_SECRET={client_secret}\n')

            # Write back to .env file
            with open(self.env_file, 'w') as f:
                f.writelines(updated_lines)

            logger.info("✅ Updated .env file with Google OAuth credentials")
            return True

        except Exception as e:
            logger.error(f"❌ Error updating .env file: {e}")
            return False

    def perform_oauth_flow(self):
        """Perform OAuth authorization flow"""
        logger.info("🔐 Performing OAuth authorization flow...")

        print("\n" + "="*60)
        print("🔐 GMAIL API SETUP - STEP 2: OAuth Authorization")
        print("="*60)
        print("""
This step will open your browser for Gmail authorization.

1. Sign in with the Google account you want to scan
2. Grant permission for "Gmail API" access
3. Copy the authorization code from the browser
4. Paste it back here when prompted

⚠️  IMPORTANT: Only grant access to the Gmail account you want to scan for job emails.
        """)

        try:
            from gmail_tool import get_oauth_url, exchange_code_for_token

            # Generate authorization URL using out-of-band flow
            auth_url = get_oauth_url('test_user', 'urn:ietf:wg:oauth:2.0:oob')
            print(f"\n🔗 Authorization URL: {auth_url}")
            print("\n📋 Copy this URL and paste it in your browser")
            print("   (This will display the authorization code directly in your browser)")

            # Get authorization code from user
            auth_code = input("\n🔑 Paste the authorization code here: ").strip()

            if not auth_code:
                print("❌ No authorization code provided")
                return False

            # Exchange code for token
            creds = exchange_code_for_token(auth_code, 'test_user')
            if creds:
                print("✅ OAuth authorization successful!")
                print("✅ Token saved to token.json")
                return True
            else:
                print("❌ OAuth authorization failed")
                return False

        except Exception as e:
            logger.error(f"❌ OAuth flow failed: {e}")
            return False

    def test_gmail_connection(self):
        """Test Gmail API connection"""
        logger.info("🧪 Testing Gmail API connection...")

        print("\n" + "="*60)
        print("🧪 GMAIL API SETUP - STEP 3: Test Connection")
        print("="*60)

        try:
            from gmail_tool import get_credentials, scan_emails

            # Test credential retrieval
            creds = get_credentials('test_user')
            if not creds:
                print("❌ Could not retrieve credentials")
                return False

            print("✅ Credentials retrieved successfully")

            # Test email scanning (limited to avoid rate limits)
            print("🔍 Testing email scan (max 5 emails)...")
            emails = scan_emails(creds, max_results=5)

            print(f"✅ Email scan successful! Found {len(emails)} emails")
            if emails:
                print("📧 Sample email subjects:")
                for i, email in enumerate(emails[:3], 1):
                    print(f"   {i}. {email.get('subject', 'No subject')}")

            return True

        except Exception as e:
            logger.error(f"❌ Gmail connection test failed: {e}")
            return False

    def run_setup(self):
        """Run complete Gmail OAuth setup"""
        logger.info("🚀 Starting Gmail OAuth setup...")

        print("\n🎯 GMAIL OAUTH SETUP FOR JOB APPLICATION AGENT")
        print("="*60)

        # Check existing setup
        if self.check_existing_setup():
            print("\n✅ Gmail OAuth is already configured!")
            choice = input("Do you want to reconfigure? (y/N): ").strip().lower()
            if choice != 'y':
                return True

        # Step 1: Create credentials file
        if not self.create_credentials_file():
            print("\n❌ Setup failed at Step 1. Please create credentials.json and try again.")
            return False

        # Step 2: Update .env file
        if not self.update_env_file():
            print("\n❌ Setup failed at Step 2. Please check credentials.json format.")
            return False

        # Step 3: Perform OAuth flow
        if not self.perform_oauth_flow():
            print("\n❌ Setup failed at Step 3. Please check authorization and try again.")
            return False

        # Step 4: Test connection
        if not self.test_gmail_connection():
            print("\n❌ Setup failed at Step 4. Please check your Gmail API configuration.")
            return False

        print("\n" + "="*60)
        print("🎉 GMAIL OAUTH SETUP COMPLETE!")
        print("="*60)
        print("✅ Credentials configured")
        print("✅ Environment variables set")
        print("✅ OAuth authorization completed")
        print("✅ Connection test successful")
        print("\n🚀 Your Job Application Agent can now scan Gmail for job emails!")
        print("\n📋 Next steps:")
        print("   1. Run: python main.py")
        print("   2. Check logs for Gmail scanning activity")
        print("   3. Configure remaining job APIs for better coverage")

        return True

def main():
    """Main setup function"""
    try:
        setup = GmailOAuthSetup()
        success = setup.run_setup()

        if success:
            logger.info("🎉 Gmail OAuth setup completed successfully!")
            return 0
        else:
            logger.error("❌ Gmail OAuth setup failed!")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error during setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())