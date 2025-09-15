import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Old limited dictionary (case-sensitive, few terms)
OLD_JOB_TERMS = ['job', 'hiring']

# New improved dictionary (case-insensitive, more terms)
NEW_JOB_TERMS = ['job', 'hiring', 'employment', 'career', 'vacancy', 'position', 'opportunity', 'recruitment', 'mineral processing', 'hazardous waste', 'reverse osmosis', 'water treatment', 'environmental engineering', 'sustainability', 'renewable energy', 'Our recommendation:']

# Sample email content with mixed case keywords
SAMPLE_EMAIL_CONTENT = """
Subject: Job Opportunity in Environmental Engineering

Dear Applicant,

We are Hiring for a position in mineral processing and hazardous waste management. This career opportunity involves reverse osmosis and water treatment technologies. Our recommendation: apply now for this vacancy in sustainability and renewable energy.

Best regards,
HR Department
"""

def old_scan_keywords(content, keywords):
    """Old method: case-sensitive matching with limited terms."""
    found_keywords = []
    for keyword in keywords:
        if keyword in content:  # Case-sensitive
            found_keywords.append(keyword)
        else:
            logger.warning(f"Missed keyword '{keyword}' due to case-sensitivity or absence")
    return found_keywords

def new_scan_keywords(content, keywords):
    """New method: case-insensitive matching with expanded terms."""
    found_keywords = []
    content_lower = content.lower()
    for keyword in keywords:
        if keyword.lower() in content_lower:  # Case-insensitive
            found_keywords.append(keyword)
        else:
            logger.info(f"Keyword '{keyword}' not found in content")
    return found_keywords

def calculate_score(found_keywords, total_keywords_in_content):
    """Calculate detection score as percentage of keywords found."""
    if total_keywords_in_content == 0:
        return 0.0
    return (len(found_keywords) / total_keywords_in_content) * 100

def extract_keywords_from_content(content):
    """Extract all potential job-related keywords from content for scoring."""
    # Simple extraction: find words that match our terms (case-insensitive)
    content_lower = content.lower()
    found = []
    all_terms = set(OLD_JOB_TERMS + NEW_JOB_TERMS)
    for term in all_terms:
        if term.lower() in content_lower:
            found.append(term)
    return found

def reproduce_keyword_matching_errors():
    """Reproduce keyword matching errors and demonstrate fixes."""
    logger.info("Starting keyword matching error reproduction")

    # Extract actual keywords present in sample content
    actual_keywords = extract_keywords_from_content(SAMPLE_EMAIL_CONTENT)
    logger.info(f"Actual job-related keywords in sample email: {actual_keywords}")

    # Old method: limited terms, case-sensitive
    logger.info("Testing old method: limited terms, case-sensitive")
    old_found = old_scan_keywords(SAMPLE_EMAIL_CONTENT, OLD_JOB_TERMS)
    old_score = calculate_score(old_found, len(actual_keywords))
    logger.error(f"Old method found {len(old_found)}/{len(actual_keywords)} keywords: {old_found}")
    logger.error(f"Old method detection score: {old_score:.2f}% (scoring mistake: low score despite perfect match potential)")

    # New method: expanded terms, case-insensitive
    logger.info("Testing new method: expanded terms, case-insensitive")
    new_found = new_scan_keywords(SAMPLE_EMAIL_CONTENT, NEW_JOB_TERMS)
    new_score = calculate_score(new_found, len(actual_keywords))
    logger.info(f"New method found {len(new_found)}/{len(actual_keywords)} keywords: {new_found}")
    logger.info(f"New method detection score: {new_score:.2f}% (improved detection)")

    # Demonstrate specific improvements
    missed_by_old = set(actual_keywords) - set(old_found)
    if missed_by_old:
        logger.warning(f"Keywords missed by old method: {missed_by_old} (due to case-sensitivity and limited terms)")

    additional_found_by_new = set(new_found) - set(old_found)
    if additional_found_by_new:
        logger.info(f"Additional keywords found by new method: {additional_found_by_new}")

    # Specific scoring mistake example
    if old_score < 50.0 and new_score > 80.0:
        logger.error(f"Scoring mistake demonstrated: Old score {old_score:.2f}% vs New score {new_score:.2f}% for same content")

if __name__ == "__main__":
    print("Keyword Matching Error Reproduction Script")
    print("This script demonstrates keyword matching issues and improvements.\n")

    reproduce_keyword_matching_errors()

    print("\nScript execution completed. Check logs for detailed analysis.")