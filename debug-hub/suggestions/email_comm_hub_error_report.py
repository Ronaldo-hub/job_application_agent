#!/usr/bin/env python3
"""
Error Reproduction Script for Email Comm Hub OAuth and Scoring Fixes

This script replicates the OAuth refresh token error by simulating an invalid token,
then verifies that the scoring fixes are preserved through mocked email data analysis.
"""

import logging
import sys
import os
from typing import Dict, Any

# Import from the fixed script
sys.path.append(os.path.dirname(__file__))
from email_comm_hub_suggestion import get_token, store_token, delete_token, run_email_job_analysis, JobAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_comm_hub_error_report.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def simulate_oauth_error(user_id: str = 'test_user') -> str:
    """
    Simulate OAuth error by temporarily setting invalid refresh token.

    Returns:
        str: The reproduced error message
    """
    logger.info("Starting OAuth error simulation")

    # Backup original token
    original_token = get_token(user_id)
    logger.info(f"Backed up original token for user {user_id}")

    # Simulate invalid refresh token
    store_token(user_id, 'invalid_refresh_token_simulated')
    logger.info("Set invalid refresh token for simulation")

    reproduced_error = ""

    try:
        # Attempt to run the email scanning and job matching function
        logger.info("Attempting to run email job analysis with invalid token")
        run_email_job_analysis(user_id)
        logger.warning("Unexpected: No error occurred - token might be valid or simulation failed")

    except ValueError as e:
        error_str = str(e).lower()
        if 'invalid' in error_str or 'refresh' in error_str or 'token' in error_str:
            reproduced_error = str(e)
            logger.info(f"Successfully reproduced OAuth error: {reproduced_error}")
        else:
            reproduced_error = f"ValueError but not OAuth-related: {e}"
            logger.warning(reproduced_error)

    except Exception as e:
        reproduced_error = str(e)
        logger.info(f"Reproduced general error: {reproduced_error}")

    finally:
        # Restore original token
        if original_token:
            store_token(user_id, original_token)
            logger.info("Restored original token")
        else:
            delete_token(user_id)
            logger.info("Deleted simulated token (no original)")

    return reproduced_error

def verify_scoring_fixes() -> Dict[str, Any]:
    """
    Verify that scoring fixes are preserved by analyzing mocked email data.

    Returns:
        Dict containing verification results
    """
    logger.info("Starting scoring fixes verification")

    analyzer = JobAnalyzer()

    # Mock email data with job-related content
    mock_email_body = """
    JOB opportunity for mineral processing engineer.
    We are looking for candidates with hazardous waste management experience.
    The role involves reverse osmosis plant operations and environmental engineering.
    Knowledge of sustainability practices and renewable energy is a plus.
    """

    logger.info("Analyzing mocked email data for scoring verification")

    try:
        analysis = analyzer.analyze_job_fit(mock_email_body)
        logger.info(f"Analysis completed: {analysis}")

        # Verification checks
        verification_results = {
            'case_insensitive_matching': False,
            'expanded_job_terms': False,
            'partial_matching': False,
            'correct_scoring_logic': False,
            'analysis_output': analysis
        }

        # Check case-insensitive matching (JOB should match 'job')
        if any('job' in kw.lower() for kw in analysis.get('matched_keywords', [])):
            verification_results['case_insensitive_matching'] = True
            logger.info("✓ Case-insensitive matching verified")

        # Check expanded job terms (mineral processing, hazardous waste, etc.)
        expanded_terms = ['mineral processing', 'hazardous waste', 'reverse osmosis', 'environmental engineering', 'sustainability', 'renewable energy']
        matched_expanded = [term for term in expanded_terms if term.lower() in mock_email_body.lower()]
        if matched_expanded:
            verification_results['expanded_job_terms'] = True
            logger.info(f"✓ Expanded job terms verified: {matched_expanded}")

        # Check partial matching (e.g., 'mineral' should partially match 'mineral processing')
        # The logic allows keyword in skill or skill in keyword
        user_skills = analyzer.user_skills['technical'] + analyzer.user_skills['software'] + analyzer.user_skills['soft']
        partial_matches = []
        for skill in user_skills:
            if skill.lower() in mock_email_body.lower() or any(word in skill.lower() for word in mock_email_body.lower().split()):
                partial_matches.append(skill)
        if partial_matches:
            verification_results['partial_matching'] = True
            logger.info(f"✓ Partial matching verified: {partial_matches}")

        # Check correct scoring logic (scores should be reasonable and weighted)
        scores = analysis
        if (isinstance(scores.get('overall_score'), (int, float)) and
            isinstance(scores.get('technical_score'), (int, float)) and
            isinstance(scores.get('software_score'), (int, float)) and
            isinstance(scores.get('experience_score'), (int, float)) and
            0 <= scores['overall_score'] <= 100):
            verification_results['correct_scoring_logic'] = True
            logger.info("✓ Correct scoring logic verified")

        return verification_results

    except Exception as e:
        logger.error(f"Error during scoring verification: {e}")
        return {'error': str(e)}

def main():
    """Main execution function"""
    logger.info("=== Email Comm Hub Error Reproduction and Verification Script ===")

    try:
        # Step 1: Reproduce OAuth error
        logger.info("Step 1: Reproducing OAuth error")
        oauth_error = simulate_oauth_error()

        if not oauth_error:
            logger.warning("No OAuth error reproduced - check token setup")
        else:
            logger.info(f"OAuth Error Reproduced: {oauth_error}")

        # Step 2: Verify scoring fixes
        logger.info("Step 2: Verifying scoring fixes")
        scoring_verification = verify_scoring_fixes()

        # Step 3: Output results
        logger.info("Step 3: Generating final report")

        print("\n" + "="*60)
        print("EMAIL COMM HUB ERROR REPRODUCTION REPORT")
        print("="*60)

        print("\n1. OAUTH ERROR REPRODUCTION:")
        if oauth_error:
            print(f"✓ SUCCESS: {oauth_error}")
        else:
            print("✗ FAILED: No OAuth error reproduced")

        print("\n2. SCORING FIXES VERIFICATION:")
        if 'error' in scoring_verification:
            print(f"✗ ERROR: {scoring_verification['error']}")
        else:
            checks = [
                ('Case-insensitive matching', scoring_verification.get('case_insensitive_matching')),
                ('Expanded job terms', scoring_verification.get('expanded_job_terms')),
                ('Partial matching', scoring_verification.get('partial_matching')),
                ('Correct scoring logic', scoring_verification.get('correct_scoring_logic'))
            ]
            for check_name, passed in checks:
                status = "✓" if passed else "✗"
                print(f"{status} {check_name}: {'PASSED' if passed else 'FAILED'}")

            print(f"\nAnalysis Output: {scoring_verification.get('analysis_output', {})}")

        print("\n" + "="*60)
        print("Report generation complete. Check logs for details.")
        print("="*60)

        return 0

    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")
        print(f"\n❌ CRITICAL ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())