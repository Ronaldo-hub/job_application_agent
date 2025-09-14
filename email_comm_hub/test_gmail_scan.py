#!/usr/bin/env python3
"""
Test Gmail scanning functionality specifically
"""

import sys
from gmail_tool import get_credentials, scan_emails
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("🧪 Testing Gmail Scanning Functionality")
    print("="*50)

    try:
        # Test credential retrieval
        print("1. Retrieving Gmail credentials...")
        creds = get_credentials('test_user')

        if not creds:
            print("❌ Failed to retrieve credentials")
            return 1

        print("✅ Credentials retrieved successfully")

        # Test email scanning
        print("\n2. Scanning Gmail for job emails...")
        print("   (This may take a few seconds...)")

        emails = scan_emails(creds, max_results=5)

        print(f"\n✅ Gmail scan completed!")
        print(f"📧 Found {len(emails)} job-related emails")

        if emails:
            print("\n📨 Sample emails found:")
            for i, email in enumerate(emails[:3], 1):
                print(f"   {i}. Subject: {email.get('subject', 'No subject')}")
                print(f"      From: {email.get('sender', 'Unknown')}")
                print(f"      Snippet: {email.get('snippet', 'No snippet')[:100]}...")
                print()
        else:
            print("\n📭 No job-related emails found in recent messages")
            print("   This is normal if you don't have recent job emails")

        print("\n🎉 Gmail scanning test completed successfully!")
        print("✅ OAuth credentials working")
        print("✅ Gmail API access confirmed")
        print("✅ Email scanning functional")

        return 0

    except Exception as e:
        logger.error(f"❌ Gmail scanning test failed: {e}")
        print(f"\n❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())