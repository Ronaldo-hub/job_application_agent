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

def get_oauth_url(user_id, redirect_uri='http://localhost:5000/oauth_callback'):
    """Generate OAuth authorization URL for a user."""
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

def exchange_code_for_token(code, user_id, redirect_uri='http://localhost:5000/oauth_callback'):
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

def scan_emails(creds, keywords=['job', 'hiring'], max_results=10):
    """Scan Gmail for emails containing job-related keywords."""
    try:
        service = build('gmail', 'v1', credentials=creds)
        query = ' OR '.join(f'"{kw}"' for kw in keywords)
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])

        job_emails = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            payload = msg_data['payload']
            headers = payload['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            body = get_email_body(payload)

            if any(kw.lower() in (subject + body).lower() for kw in keywords):
                job_emails.append({
                    'id': msg['id'],
                    'subject': subject,
                    'sender': sender,
                    'body': body,
                    'snippet': msg_data.get('snippet', '')
                })

        logger.info(f"Scanned {len(job_emails)} job-related emails")
        return job_emails
    except Exception as e:
        logger.error(f"Error scanning emails: {e}")
        raise

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