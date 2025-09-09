#!/usr/bin/env python3
"""
Simplified test of the Job Application Agent workflow
Demonstrates Gmail scanning, job parsing, and resume fit analysis
"""

import sys
import json
from gmail_tool import get_credentials, scan_emails
from parser_tool import parse_job_emails
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_simple_fit_score(master_resume, job):
    """Simple fit score calculation without Hugging Face dependency"""
    try:
        # Extract skills from master resume
        resume_skills = set()
        if 'skills' in master_resume:
            resume_skills = set(skill.lower() for skill in master_resume['skills'])

        # Extract requirements from job
        job_requirements = set()
        if 'requirements' in job:
            job_requirements = set(req.lower() for req in job['requirements'])
        if 'skills' in job:
            job_requirements.update(set(skill.lower() for skill in job['skills']))

        # Extract keywords from job description
        job_description = job.get('description', '') or job.get('body', '')
        if job_description:
            # Simple keyword extraction
            common_tech_words = [
                'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker',
                'machine learning', 'ai', 'data science', 'devops', 'agile', 'scrum',
                'chemical', 'engineering', 'process', 'control', 'matlab', 'chemistry'
            ]
            desc_words = set(job_description.lower().split())
            job_requirements.update(desc_words.intersection(set(common_tech_words)))

        if not job_requirements:
            return 0.0

        # Calculate keyword match score
        matching_skills = resume_skills.intersection(job_requirements)
        keyword_score = len(matching_skills) / len(job_requirements) * 100

        return keyword_score

    except Exception as e:
        logger.error(f"Error calculating fit score: {e}")
        return 0.0

def load_master_resume_simple():
    """Load master resume without Hugging Face dependency"""
    try:
        with open('master_resume.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("master_resume.json not found")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing master_resume.json: {e}")
        return {}

def test_workflow_simple():
    """Test the core Job Application Agent workflow"""
    print("🚀 TESTING JOB APPLICATION AGENT WORKFLOW")
    print("="*60)

    try:
        # Step 1: Gmail Scanning
        print("\n📧 STEP 1: Scanning Gmail for job emails...")
        creds = get_credentials('test_user')

        if not creds:
            print("❌ Failed to get Gmail credentials")
            return False

        emails = scan_emails(creds, max_results=10)
        print(f"✅ Found {len(emails)} job-related emails")

        if not emails:
            print("⚠️ No job emails found. Using sample job data for demonstration...")
            # Create sample job data for testing
            sample_job = {
                'id': 'sample_1',
                'subject': 'Our recommendation: Process Controller',
                'sender': 'Pnet <jobs@pnet.co.za>',
                'body': 'We have an exciting opportunity for a Process Controller position. Requirements include process engineering experience, chemical engineering background, knowledge of control systems, MATLAB proficiency, and chemistry laboratory skills.',
                'snippet': 'Process Controller job opportunity requiring chemical engineering and process control skills'
            }
            emails = [sample_job]

        # Step 2: Job Parsing
        print("\n📝 STEP 2: Parsing job descriptions...")
        parsed_jobs = parse_job_emails(emails)
        print(f"✅ Parsed {len(parsed_jobs)} jobs")

        for i, job in enumerate(parsed_jobs[:3], 1):
            print(f"   {i}. {job.get('job_title', 'Unknown Title')}")
            print(f"      Skills: {', '.join(job.get('skills', [])[:5])}")

        # Step 3: Load Master Resume
        print("\n📄 STEP 3: Loading master resume...")
        master_resume = load_master_resume_simple()
        if master_resume:
            print("✅ Master resume loaded")
            print(f"   Skills: {', '.join(master_resume.get('skills', [])[:10])}...")
        else:
            print("❌ Failed to load master resume")
            return False

        # Step 4: Job Fit Analysis
        print("\n🔍 STEP 4: Analyzing job fit...")
        high_fit_jobs = []
        fit_scores = []

        for job in parsed_jobs:
            fit_score = calculate_simple_fit_score(master_resume, job)
            fit_scores.append((job.get('job_title', 'Unknown'), fit_score))
            print(".1f")

            if fit_score >= 90:
                high_fit_jobs.append(job)
                print("      🎯 HIGH FIT - Would generate ATS resume!")
            elif fit_score >= 70:
                print("      📊 GOOD FIT - Consider applying")
            else:
                print("      📉 LOW FIT - May not be suitable")

        # Step 5: Results Summary
        print("\n📊 WORKFLOW RESULTS SUMMARY")
        print("="*60)
        print(f"📧 Gmail Emails Scanned: {len(emails)}")
        print(f"📝 Jobs Parsed: {len(parsed_jobs)}")
        print(f"🔍 High-Fit Jobs (≥90%): {len(high_fit_jobs)}")
        print(f"📄 Resumes Would Be Generated: {len(high_fit_jobs)}")

        if fit_scores:
            print("\n🎯 Job Fit Scores:")
            for title, score in fit_scores[:5]:  # Show top 5
                status = "🎯 HIGH FIT" if score >= 90 else "📊 GOOD FIT" if score >= 70 else "📉 LOW FIT"
                print(".1f")

        if high_fit_jobs:
            print("\n📋 Jobs Qualifying for ATS Resume Generation:")
            for i, job in enumerate(high_fit_jobs, 1):
                print(f"   {i}. {job.get('job_title', 'Unknown Title')}")
                print(f"      Company: {job.get('employer_email', 'Unknown')}")
                print(f"      Fit Score: {job.get('fit_score', 0):.1f}%")
                print(f"      Skills Match: {', '.join(job.get('skills', [])[:3])}")
                print()

        print("✅ WORKFLOW TEST COMPLETED!")
        print("🎉 Your Job Application Agent core functionality is working!")

        # Recommendations
        if high_fit_jobs:
            print(f"\n💡 RECOMMENDATION: {len(high_fit_jobs)} jobs qualify for ATS resume generation!")
            print("   These jobs match ≥90% of your resume skills.")
        else:
            print("\n💡 RECOMMENDATION: No jobs currently qualify for ATS resume generation.")
            print("   Try jobs that match your chemical engineering and process control skills.")

        return True

    except Exception as e:
        logger.error(f"❌ Workflow test failed: {e}")
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_workflow_simple()
    sys.exit(0 if success else 1)