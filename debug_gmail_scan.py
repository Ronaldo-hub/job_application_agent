#!/usr/bin/env python3
"""
Debug Gmail scanning to see why emails are not being found
"""

import sys
from gmail_tool import get_credentials, scan_emails
from googleapiclient.discovery import build
from googleapiclient.http import build_http
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_scan_emails(creds, keywords=['job', 'hiring', 'Our recommendation:'], max_results=20):
    """Debug version of scan_emails with detailed logging"""
    try:
        import time
        from googleapiclient.http import build_http

        print(f"\n🔍 DEBUG: Keywords to search: {keywords}")

        # Create HTTP client with timeout
        http = build_http()
        http.timeout = 30

        service = build('gmail', 'v1', credentials=creds)

        # Build search query
        query = ' OR '.join(f'"{kw}"' for kw in keywords)
        print(f"🔍 DEBUG: Gmail search query: {query}")

        # Search for messages
        print("🔍 DEBUG: Executing Gmail search...")
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        print(f"🔍 DEBUG: Gmail found {len(messages)} messages matching query")

        if not messages:
            print("🔍 DEBUG: No messages found. Trying broader search...")

            # Try a broader search to see if there are any messages at all
            broad_results = service.users().messages().list(
                userId='me',
                maxResults=5
            ).execute()

            broad_messages = broad_results.get('messages', [])
            print(f"🔍 DEBUG: Total messages in inbox: {len(broad_messages)}")

            if broad_messages:
                print("🔍 DEBUG: Checking recent message subjects...")
                for i, msg in enumerate(broad_messages[:3]):
                    try:
                        msg_data = service.users().messages().get(
                            userId='me',
                            id=msg['id'],
                            format='metadata',
                            metadataHeaders=['Subject', 'From']
                        ).execute()

                        payload = msg_data['payload']
                        headers = payload['headers']

                        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')

                        print(f"🔍 DEBUG: Recent message {i+1}: '{subject}' from {sender}")

                        # Check if this message contains our keywords
                        subject_lower = subject.lower()
                        for kw in keywords:
                            if kw.lower() in subject_lower:
                                print(f"🔍 DEBUG: ✅ Found keyword '{kw}' in subject: '{subject}'")
                                break

                    except Exception as e:
                        print(f"🔍 DEBUG: Error reading message {msg['id']}: {e}")

            return []

        job_emails = []
        processed_count = 0

        print(f"🔍 DEBUG: Processing {len(messages)} messages...")

        # Process messages
        for i, msg in enumerate(messages):
            try:
                print(f"🔍 DEBUG: Processing message {i+1}/{len(messages)}: {msg['id']}")

                # Get message metadata
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['Subject', 'From']
                ).execute()

                payload = msg_data['payload']
                headers = payload['headers']

                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '')

                print(f"🔍 DEBUG: Subject: '{subject}'")
                print(f"🔍 DEBUG: Sender: '{sender}'")

                # Check keyword matching
                subject_lower = subject.lower()
                body = msg_data.get('snippet', '')

                matched_keywords = []
                for kw in keywords:
                    if kw.lower() in subject_lower or kw.lower() in body.lower():
                        matched_keywords.append(kw)
                        print(f"🔍 DEBUG: ✅ Matched keyword: '{kw}'")

                if matched_keywords:
                    print(f"🔍 DEBUG: 🎯 Message matches! Keywords: {matched_keywords}")
                    job_emails.append({
                        'id': msg['id'],
                        'subject': subject,
                        'sender': sender,
                        'body': body,
                        'snippet': msg_data.get('snippet', ''),
                        'matched_keywords': matched_keywords
                    })
                else:
                    print(f"🔍 DEBUG: ❌ No keyword match")

                processed_count += 1

            except Exception as msg_error:
                print(f"🔍 DEBUG: Error processing message {msg['id']}: {msg_error}")
                continue

        print(f"🔍 DEBUG: Completed processing. Found {len(job_emails)} job emails")
        return job_emails

    except Exception as e:
        logger.error(f"Error in debug scan: {e}")
        print(f"❌ Debug scan failed: {e}")
        return []

def main():
    print("🐛 DEBUGGING GMAIL SCANNING")
    print("="*50)

    try:
        # Test credential retrieval
        print("1. Retrieving Gmail credentials...")
        creds = get_credentials('test_user')

        if not creds:
            print("❌ Failed to retrieve credentials")
            return 1

        print("✅ Credentials retrieved successfully")

        # Debug scan with detailed logging
        print("\n2. Running debug scan...")
        emails = debug_scan_emails(creds)

        print("\n✅ Debug scan completed!")
        print(f"📧 Found {len(emails)} job-related emails")

        if emails:
            print("\n📨 Found emails:")
            for i, email in enumerate(emails, 1):
                print(f"   {i}. Subject: '{email.get('subject', 'No subject')}'")
                print(f"      Matched: {email.get('matched_keywords', [])}")
                print(f"      From: {email.get('sender', 'Unknown')}")
                print()
        else:
            print("\n📭 No job-related emails found")
            print("🔍 DEBUG: Check the debug output above for clues")

        return 0

    except Exception as e:
        logger.error(f"❌ Debug test failed: {e}")
        print(f"\n❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())