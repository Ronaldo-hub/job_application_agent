#!/usr/bin/env python3
"""
Generate Fresh Gmail OAuth URL
"""

from gmail_tool import get_oauth_url

def main():
    print("🔐 Generating Fresh Gmail OAuth Authorization URL...")
    print("="*60)

    try:
        auth_url = get_oauth_url('test_user', 'urn:ietf:wg:oauth:2.0:oob')
        print("✅ Authorization URL Generated Successfully!")
        print("\n🔗 FRESH AUTHORIZATION URL:")
        print("="*60)
        print(auth_url)
        print("="*60)
        print("\n📋 Instructions:")
        print("1. Copy the URL above")
        print("2. Paste it in your browser")
        print("3. Sign in with your Gmail account")
        print("4. Grant Gmail API access")
        print("5. Copy the NEW authorization code")
        print("6. Send me the new code")

    except Exception as e:
        print(f"❌ Error generating OAuth URL: {e}")

if __name__ == "__main__":
    main()