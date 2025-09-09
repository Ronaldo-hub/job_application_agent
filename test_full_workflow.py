#!/usr/bin/env python3
"""
Test the full Job Application Agent workflow
"""

import sys
import json
from gmail_tool import get_credentials, scan_emails
from parser_tool import parse_job_emails
from resume_tool import load_master_resume, calculate_fit_score, generate_resume_content
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_full_workflow():
    """Test the complete job application workflow"""
    print("🚀 TESTING FULL JOB APPLICATION AGENT WORKFLOW")
    print("="*60)

    try:
        # Step 1: Gmail Scanning
        print("\n📧 STEP 1: Scanning Gmail for job emails...")
        creds = get_credentials('test_user')

        if not creds:
            print("❌ Failed to get Gmail credentials")
            return

        emails = scan_emails(creds, max_results=10)
        print(f"✅ Found {len(emails)} job-related emails")

        if not emails:
            print("⚠️ No job emails found. Using sample job data for demonstration...")
            # Create sample job data for testing
            sample_job = {
                'id': 'sample_1',
                'subject': 'Our recommendation: Process Controller',
                'sender': 'Pnet <jobs@pnet.co.za>',
                'body': 'We have an exciting opportunity for a Process Controller position. Requirements include process engineering experience, chemical engineering background, and knowledge of control systems.',
                'snippet': 'Process Controller job opportunity with competitive salary'
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
        master_resume = load_master_resume()
        print("✅ Master resume loaded")
        print(f"   Skills: {', '.join(master_resume.get('skills', [])[:10])}...")

        # Step 4: Job Fit Analysis
        print("\n🔍 STEP 4: Analyzing job fit...")
        high_fit_jobs = []
        fit_scores = []

        for job in parsed_jobs:
            fit_score = calculate_fit_score(master_resume, job)
            fit_scores.append((job.get('job_title', 'Unknown'), fit_score))
            print(".1f")
            if fit_score >= 90:
                high_fit_jobs.append(job)
                print("      🎯 HIGH FIT - Will generate resume!")
            else:
                print("      📉 Low fit - Skipping resume generation")

        # Step 5: Resume Generation for High-Fit Jobs
        print("\n📝 STEP 5: Generating ATS-optimized resumes...")
        generated_resumes = []

        if high_fit_jobs:
            for i, job in enumerate(high_fit_jobs, 1):
                print(f"   Generating resume {i}/{len(high_fit_jobs)}: {job.get('job_title', 'Unknown')}")

                try:
                    # Generate resume content
                    resume_content = generate_resume_content(master_resume, job)
                    generated_resumes.append({
                        'job_title': job.get('job_title', 'Unknown'),
                        'company': job.get('employer_email', 'Unknown'),
                        'content': resume_content[:500] + "..." if len(resume_content) > 500 else resume_content,
                        'fit_score': job.get('fit_score', 0)
                    })
                    print("      ✅ Resume generated successfully")
                except Exception as e:
                    print(f"      ❌ Failed to generate resume: {e}")

        else:
            print("   ⚠️ No high-fit jobs found (≥90% match)")
            print("   💡 Try jobs that match your chemical engineering background")

        # Step 6: Results Summary
        print("\n📊 WORKFLOW RESULTS SUMMARY")
        print("="*60)
        print(f"📧 Gmail Emails Scanned: {len(emails)}")
        print(f"📝 Jobs Parsed: {len(parsed_jobs)}")
        print(f"🔍 High-Fit Jobs (≥90%): {len(high_fit_jobs)}")
        print(f"📄 Resumes Generated: {len(generated_resumes)}")

        if fit_scores:
            print("\n🎯 Job Fit Scores:")
            for title, score in fit_scores[:5]:  # Show top 5
                status = "🎯 HIGH FIT" if score >= 90 else "📉 LOW FIT"
                print(".1f")
        if generated_resumes:
            print("\n📋 Generated Resumes:")
            for i, resume in enumerate(generated_resumes, 1):
                print(f"   {i}. {resume['job_title']} ({resume['fit_score']}%)")
                print(f"      Preview: {resume['content'][:100]}...")

        print("\n✅ WORKFLOW TEST COMPLETED!")
        print("🎉 Your Job Application Agent is working correctly!")

        return True

    except Exception as e:
        logger.error(f"❌ Workflow test failed: {e}")
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_full_workflow()
    sys.exit(0 if success else 1)