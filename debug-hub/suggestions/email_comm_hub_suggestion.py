import os
import json
import sqlite3
import logging
import re
import base64
from typing import List, Dict, Any
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
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

def delete_token(user_id):
    """Delete refresh token for a user."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        logger.info(f"Deleted token for user {user_id}")
    except Exception as e:
        logger.error(f"Error deleting token for user {user_id}: {e}")
        raise

def get_oauth_url(user_id, redirect_uri='http://localhost:8080'):
    """Generate OAuth authorization URL for a user using local server flow."""
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

def exchange_code_for_token(code, user_id, redirect_uri='http://localhost:8080'):
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
    # Try to load from token.json file first
    try:
        with open('token.json', 'r') as f:
            token_data = json.load(f)

        creds = Credentials.from_authorized_user_info(token_data)

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info(f"Refreshed credentials for user {user_id}")
            except RefreshError as e:
                if 'invalid_grant' in str(e):
                    logger.warning(f"Refresh token invalid for user {user_id}. Need re-authorization.")
                    raise ValueError(f"Refresh token invalid for user {user_id}. Please re-authorize.")
                else:
                    raise

        return creds

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load token.json: {e}. Trying database...")

    # Fallback to database
    refresh_token = get_token(user_id)
    if not refresh_token:
        raise ValueError(f"No refresh token found for user {user_id}. Please authorize first.")

    try:
        creds = Credentials.from_authorized_user_info({
            'refresh_token': refresh_token,
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'token_uri': 'https://oauth2.googleapis.com/token',
            'scopes': ['https://www.googleapis.com/auth/gmail.readonly']
        })

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info(f"Refreshed credentials for user {user_id}")
            except RefreshError as e:
                if 'invalid_grant' in str(e):
                    logger.warning(f"Refresh token invalid for user {user_id}. Need re-authorization.")
                    # Remove invalid token from database
                    delete_token(user_id)
                    raise ValueError(f"Refresh token invalid for user {user_id}. Please re-authorize.")
                else:
                    raise

        return creds
    except Exception as e:
        logger.error(f"Error getting credentials for user {user_id}: {e}")
        raise

def scan_emails(creds, job_terms=['job', 'hiring', 'employment', 'career', 'vacancy', 'position', 'opportunity', 'recruitment', 'mineral processing', 'hazardous waste', 'reverse osmosis', 'water treatment', 'environmental engineering', 'sustainability', 'renewable energy', 'Our recommendation:'], max_results=10, timeout=30, batch_size=5):
    """Scan Gmail for emails containing job-related keywords with timeout and memory management."""
    try:
        import time
        from googleapiclient.http import build_http

        # Create HTTP client with timeout to prevent hanging
        http = build_http()
        http.timeout = timeout

        service = build('gmail', 'v1', credentials=creds)
        query = ' OR '.join(job_terms)

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
                    if any(term.lower() in subject.lower() for term in job_terms):
                        # Get full message for body analysis
                        full_msg_data = service.users().messages().get(
                            userId='me',
                            id=msg['id'],
                            format='full'
                        ).execute()
                        body = get_email_body(full_msg_data['payload'])
                    else:
                        body = msg_data.get('snippet', '')

                    if any(term.lower() in (subject + body).lower() for term in job_terms):
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

class JobAnalyzer:
    def __init__(self):
        # User's resume skills and experience keywords
        self.user_skills = {
            'technical': [
                'chemical engineering', 'process engineering', 'mineral processing',
                'hazardous waste management', 'reverse osmosis', 'pyrolysis',
                'heat transfer', 'mass transfer', 'thermodynamics', 'reactor technology',
                'particle technology', 'process control', 'optimization', 'experimental design',
                'numerical methods', 'iso standards', 'environmental compliance'
            ],
            'software': [
                'python', 'matlab', 'polymath', 'microsoft office', 'cis pro',
                'process simulation', 'data analytics', 'fault finding'
            ],
            'soft': [
                'project management', 'problem solving', 'presentations',
                'report writing', 'team management', 'operational oversight'
            ]
        }

        self.user_experience = [
            'chemical engineering intern', 'hazardous waste management',
            'process engineering', 'mineral processing research',
            'reverse osmosis plant maintenance', 'laboratory research'
        ]

    def search_recommendation_emails(self, creds, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for emails with 'Our recommendation' subject"""
        logger.info("🔍 Searching for 'Our recommendation' emails...")

        try:
            # Search specifically for "Our recommendation" emails
            service = build('gmail', 'v1', credentials=creds)

            # Query for emails with subject containing "Our recommendation"
            query = 'subject:"Our recommendation"'
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            logger.info(f"📧 Found {len(messages)} 'Our recommendation' emails")

            recommendation_emails = []
            for msg in messages:
                email_data = self._get_email_details(service, msg['id'])
                if email_data:
                    recommendation_emails.append(email_data)

            return recommendation_emails

        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []

    def _get_email_details(self, service, msg_id: str) -> Dict[str, Any]:
        """Extract detailed information from an email"""
        try:
            msg = service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()

            # Extract headers
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

            # Extract body
            body = self._extract_body(msg['payload'])

            return {
                'id': msg_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'snippet': msg.get('snippet', '')
            }

        except Exception as e:
            logger.error(f"Error getting email details for {msg_id}: {e}")
            return None

    def _extract_body(self, payload: Dict) -> str:
        """Extract text content from email payload"""
        if 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')

        return ""

    def analyze_job_fit(self, email_body: str) -> Dict[str, Any]:
        """Analyze how well a job description fits the user's resume"""
        body_lower = email_body.lower()

        # Extract job requirements from email
        job_keywords = self._extract_job_keywords(body_lower)

        # Calculate compatibility scores
        technical_score = self._calculate_keyword_match(job_keywords, self.user_skills['technical'])
        software_score = self._calculate_keyword_match(job_keywords, self.user_skills['software'])
        experience_score = self._calculate_experience_match(body_lower)

        overall_score = (technical_score * 0.5) + (software_score * 0.3) + (experience_score * 0.2)

        # Determine job category
        job_category = self._categorize_job(body_lower)

        return {
            'overall_score': round(overall_score, 2),
            'technical_score': round(technical_score, 2),
            'software_score': round(software_score, 2),
            'experience_score': round(experience_score, 2),
            'job_category': job_category,
            'matched_keywords': job_keywords,
            'recommendation': self._get_recommendation(overall_score, job_category)
        }

    def _extract_job_keywords(self, text: str) -> List[str]:
        """Extract relevant job keywords from text"""
        # Common job-related keywords
        job_terms = [
            'engineer', 'engineering', 'chemical', 'process', 'technical',
            'analyst', 'scientist', 'technician', 'specialist', 'manager',
            'coordinator', 'supervisor', 'operator', 'maintenance',
            'quality', 'control', 'research', 'development', 'laboratory',
            'environmental', 'compliance', 'safety', 'project'
        ]

        found_keywords = []
        for term in job_terms:
            if term in text:
                found_keywords.append(term)

        return list(set(found_keywords))  # Remove duplicates

    def _calculate_keyword_match(self, job_keywords: List[str], user_skills: List[str]) -> float:
        """Calculate percentage match between job keywords and user skills"""
        if not job_keywords:
            return 0.0

        matches = 0
        for keyword in job_keywords:
            for skill in user_skills:
                if keyword.lower() in skill.lower() or skill.lower() in keyword.lower():
                    matches += 1
                    break

        return (matches / len(job_keywords)) * 100

    def _calculate_experience_match(self, text: str) -> float:
        """Calculate experience match score"""
        experience_matches = 0
        for exp in self.user_experience:
            if exp.lower() in text:
                experience_matches += 1

        return min((experience_matches / len(self.user_experience)) * 100, 100)

    def _categorize_job(self, text: str) -> str:
        """Categorize the job based on content"""
        if any(term in text for term in ['chemical', 'process', 'engineering']):
            return 'Chemical/Process Engineering'
        elif any(term in text for term in ['environmental', 'compliance', 'waste']):
            return 'Environmental/Compliance'
        elif any(term in text for term in ['laboratory', 'research', 'analysis']):
            return 'Research/Laboratory'
        elif any(term in text for term in ['project', 'management', 'coordinator']):
            return 'Project Management'
        elif any(term in text for term in ['quality', 'control', 'assurance']):
            return 'Quality Control'
        else:
            return 'General Technical'

    def _get_recommendation(self, score: float, category: str) -> str:
        """Provide recommendation based on score and category"""
        if score >= 80:
            return f"Excellent match! This {category} position aligns well with your background."
        elif score >= 60:
            return f"Good match. This {category} role has some alignment with your skills."
        elif score >= 40:
            return f"Moderate match. Consider if this {category} position interests you."
        else:
            return f"Limited match. This {category} role may not be the best fit for your expertise."

def run_email_job_analysis(user_id='test_user'):
    """Run the complete email job analysis workflow"""
    logger.info("Starting email job analysis workflow")

    try:
        # Get credentials (will handle refresh automatically)
        creds = get_credentials(user_id)

        # Initialize analyzer
        analyzer = JobAnalyzer()

        # Search for recommendation emails
        emails = analyzer.search_recommendation_emails(creds)

        if not emails:
            logger.info("No 'Our recommendation' emails found")
            return []

        logger.info(f"Analyzing {len(emails)} recommendation emails")

        analyzed_emails = []
        for email in emails:
            analysis = analyzer.analyze_job_fit(email['body'])
            analyzed_emails.append({
                'email': email,
                'analysis': analysis
            })

        # Log summary
        excellent = [e for e in analyzed_emails if e['analysis']['overall_score'] >= 80]
        good = [e for e in analyzed_emails if 60 <= e['analysis']['overall_score'] < 80]

        logger.info(f"Analysis complete: {len(excellent)} excellent matches, {len(good)} good matches")

        return analyzed_emails

    except ValueError as e:
        if "Please re-authorize" in str(e):
            logger.warning(f"Re-authorization needed: {e}")
            # Generate new OAuth URL
            auth_url = get_oauth_url(user_id)
            logger.info(f"Please visit: {auth_url}")
            raise ValueError(f"Re-authorization required. Please visit: {auth_url}")
        else:
            raise
    except Exception as e:
        logger.error(f"Error in email job analysis: {e}")
        raise

# Initialize DB on import
init_db()