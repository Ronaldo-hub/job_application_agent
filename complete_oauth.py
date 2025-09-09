#!/usr/bin/env python3
"""
Complete Gmail OAuth Setup with Authorization Code
"""

import sys
from gmail_tool import exchange_code_for_token, get_credentials, scan_emails
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    auth_code = "4/1AVMBsJibORBskHY1vAYHL1j7FTRTVFZcsJc6QK6_AS0YoeSsrc43T1p_Elw"

    print("🔄 Exchanging authorization code for OAuth tokens...")

    try:
        # Exchange authorization code for tokens
        creds = exchange_code_for_token(auth_code, 'test_user', 'urn:ietf:wg:oauth:2.0:oob')

        if creds:
            print("✅ OAuth tokens obtained successfully!")
            print("✅ Tokens saved to token.json")

            # Test the connection
            print("\n🧪 Testing Gmail connection...")
            test_creds = get_credentials('test_user')

            if test_creds:
                print("✅ Credentials retrieved successfully")

                # Test email scanning
                emails = scan_emails(test_creds, max_results=3)
                print(f"✅ Email scan test successful! Found {len(emails)} emails")

                if emails:
                    print("📧 Sample emails found:")
                    for i, email in enumerate(emails[:2], 1):
                        print(f"   {i}. {email.get('subject', 'No subject')}")

                print("\n🎉 GMAIL OAUTH SETUP COMPLETE!")
                print("✅ Your Job Application Agent can now scan Gmail for job emails!")
                return 0
            else:
                print("❌ Failed to retrieve credentials")
                return 1
        else:
            print("❌ Failed to exchange authorization code")
            return 1

    except Exception as e:
        logger.error(f"❌ OAuth completion failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())