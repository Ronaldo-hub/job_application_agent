import spacy
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    logger.error("spaCy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm'")
    raise

def parse_job_email(email_dict):
    """Parse job email content using spaCy to extract job details."""
    try:
        text = email_dict.get('body', '') + ' ' + email_dict.get('subject', '')
        doc = nlp(text)

        job_title = extract_job_title(text)
        skills = extract_skills(doc)
        employer_email = extract_employer_email(email_dict.get('sender', ''), text)

        parsed_job = {
            'job_title': job_title,
            'skills': skills,
            'employer_email': employer_email,
            'email_id': email_dict.get('id', ''),
            'subject': email_dict.get('subject', ''),
            'snippet': email_dict.get('snippet', '')
        }

        logger.info(f"Parsed job: {job_title} from {employer_email}")
        return parsed_job
    except Exception as e:
        logger.error(f"Error parsing email {email_dict.get('id', '')}: {e}")
        return {
            'job_title': 'Error parsing',
            'skills': [],
            'employer_email': 'unknown@example.com',
            'email_id': email_dict.get('id', ''),
            'subject': email_dict.get('subject', ''),
            'snippet': email_dict.get('snippet', '')
        }

def extract_job_title(text):
    """Extract job title from email text using regex patterns."""
    patterns = [
        r'Job Title:\s*(.+?)[\n\r]',
        r'Position:\s*(.+?)[\n\r]',
        r'Role:\s*(.+?)[\n\r]',
        r'Title:\s*(.+?)[\n\r]',
        r'Opening for:\s*(.+?)[\n\r]',
        r'We are hiring:\s*(.+?)[\n\r]'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            title = match.group(1).strip()
            if len(title) < 100:  # Reasonable length
                return title
    # Fallback: first sentence with keywords
    sentences = re.split(r'[.!?]', text)
    for sentence in sentences:
        if any(kw in sentence.lower() for kw in ['job', 'position', 'role', 'hiring']):
            return sentence.strip()
    return "Unknown Job Title"

def extract_skills(doc):
    """Extract potential skills from spaCy doc using POS tagging."""
    skills = []
    for token in doc:
        if token.pos_ in ['NOUN', 'PROPN'] and len(token.text) > 2 and not token.is_stop:
            skills.append(token.text.lower())
    # Remove duplicates and limit
    unique_skills = list(set(skills))
    return unique_skills[:15]  # Limit to 15 skills

def extract_employer_email(sender, text):
    """Extract employer email from sender or email body."""
    # From sender field
    email_match = re.search(r'<(.+@.+\..+)>', sender)
    if email_match:
        return email_match.group(1)

    # From email body
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if email_match:
        return email_match.group(0)

    return "unknown@example.com"

def parse_job_emails(email_list):
    """Parse a list of job emails."""
    return [parse_job_email(email) for email in email_list]