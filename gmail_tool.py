import os
import sqlite3
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DB_PATH = 'users.db'

def init_db():
    """Initialize SQLite database for storing user tokens."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            refresh_token TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def store_token(user_id, refresh_token):
    """Store refresh token for a user."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO users (user_id, refresh_token) VALUES (?, ?)', (user_id, refresh_token))
        conn.commit()
        conn.close()
        logger.info(f"Stored token for user {user_id}")
    except Exception as e:
        logger.error(f"Error storing token for user {user_id}: {e}")
        raise

def get_token(user_id):
    """Retrieve refresh token for a user."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT refresh_token FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error retrieving token for user {user_id}: {e}")
        return None

def get_oauth_url(user_id, redirect_uri='urn:ietf:wg:oauth:2.0:oob'):
    """Generate OAuth authorization URL for a user using out-of-band flow."""
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/gmail.readonly'],
            redirect_uri=redirect_uri
        )
        auth_url, _ = flow.authorization_url(state=user_id, prompt='consent')
        logger.info(f"Generated OAuth URL for user {user_id}")
        return auth_url
    except Exception as e:
        logger.error(f"Error generating OAuth URL for user {user_id}: {e}")
        raise

def exchange_code_for_token(code, user_id, redirect_uri='urn:ietf:wg:oauth:2.0:oob'):
    """Exchange authorization code for credentials and store refresh token."""
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/gmail.readonly'],
            redirect_uri=redirect_uri
        )
        flow.fetch_token(code=code)
        creds = flow.credentials
        store_token(user_id, creds.refresh_token)
        logger.info(f"Exchanged code and stored token for user {user_id}")
        return creds
    except Exception as e:
        logger.error(f"Error exchanging code for user {user_id}: {e}")
        raise

def get_credentials(user_id):
    """Get valid credentials for a user, refreshing if necessary."""
    refresh_token = get_token(user_id)
    if not refresh_token:
        raise ValueError(f"No refresh token found for user {user_id}. Please authorize first.")

    try:
        creds = Credentials.from_authorized_user_info({
            'refresh_token': refresh_token,
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'scopes': ['https://www.googleapis.com/auth/gmail.readonly']
        })

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            logger.info(f"Refreshed credentials for user {user_id}")

        return creds
    except Exception as e:
        logger.error(f"Error getting credentials for user {user_id}: {e}")
        raise

def scan_emails(creds, keywords=['job', 'hiring'], max_results=10, timeout=30, batch_size=5):
    """Scan Gmail for emails containing job-related keywords with timeout and memory management."""
    try:
        import time
        from googleapiclient.http import build_http

        # Create HTTP client with timeout to prevent hanging
        http = build_http()
        http.timeout = timeout

        service = build('gmail', 'v1', credentials=creds, http=http)
        query = ' OR '.join(f'"{kw}"' for kw in keywords)

        # Add timeout to message list request
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            logger.info("No messages found matching the query")
            return []

        job_emails = []
        processed_count = 0
        error_count = 0

        # Process messages in batches to manage memory usage
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            batch_results = []

            for msg in batch:
                try:
                    # Add timeout to individual message retrieval and use metadata-only format
                    msg_data = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',  # Only get metadata to reduce memory usage
                        metadataHeaders=['Subject', 'From']
                    ).execute()

                    payload = msg_data['payload']
                    headers = payload['headers']

                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), '')

                    # Get body only if we need full content, otherwise use snippet
                    if any(kw.lower() in subject.lower() for kw in keywords):
                        # Get full message for body analysis
                        full_msg_data = service.users().messages().get(
                            userId='me',
                            id=msg['id'],
                            format='full'
                        ).execute()
                        body = get_email_body(full_msg_data['payload'])
                    else:
                        body = msg_data.get('snippet', '')

                    if any(kw.lower() in (subject + body).lower() for kw in keywords):
                        batch_results.append({
                            'id': msg['id'],
                            'subject': subject,
                            'sender': sender,
                            'body': body,
                            'snippet': msg_data.get('snippet', '')
                        })

                    processed_count += 1

                except Exception as msg_error:
                    error_count += 1
                    logger.warning(f"Error processing message {msg['id']}: {msg_error}")
                    continue

            job_emails.extend(batch_results)

            # Add small delay between batches to prevent rate limiting
            if i + batch_size < len(messages):
                time.sleep(0.1)

        logger.info(f"Scanned {len(job_emails)} job-related emails from {processed_count} messages ({error_count} errors)")
        return job_emails

    except Exception as e:
        logger.error(f"Error scanning emails: {e}")
        # Return empty list instead of raising to allow workflow to continue
        return []

def get_email_body(payload):
    """Extract email body from payload."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                return part['body'].get('data', '')
    elif payload['mimeType'] == 'text/plain':
        return payload['body'].get('data', '')
    return ''

# Initialize DB on import
init_db()