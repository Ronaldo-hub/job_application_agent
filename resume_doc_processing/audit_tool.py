import json
import os
import logging
import requests
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
if not HUGGINGFACE_API_KEY:
    logger.error("HUGGINGFACE_API_KEY not found in environment variables")
    raise ValueError("HUGGINGFACE_API_KEY is required")

def load_master_resume() -> Dict:
    """Load the master resume from JSON file."""
    try:
        with open('master_resume.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("master_resume.json not found")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing master_resume.json: {e}")
        raise

def audit_resume_content(generated_content: str, job_details: Dict) -> Dict:
    """Audit the generated resume for hallucinations using Hugging Face Llama 3.1."""
    try:
        master_resume = load_master_resume()

        prompt = f"""
        You are an expert auditor for resume content. Your task is to analyze the generated resume for accuracy and detect any potential hallucinations.

        MASTER RESUME (Ground Truth):
        {json.dumps(master_resume, indent=2)}

        JOB REQUIREMENTS:
        Title: {job_details.get('job_title', 'Unknown')}
        Skills: {', '.join(job_details.get('skills', []))}

        GENERATED RESUME CONTENT:
        {generated_content}

        ANALYSIS INSTRUCTIONS:
        1. Compare the generated content against the master resume
        2. Check if any skills, experiences, or qualifications are fabricated
        3. Verify that job-specific skills are appropriately highlighted
        4. Look for inconsistencies or exaggerations
        5. Assess overall accuracy and relevance

        Provide your analysis in the following JSON format:
        {{
            "accuracy_score": 0-100 (percentage of accurate content),
            "hallucinations_detected": ["list of potential fabrications"],
            "missing_skills": ["job skills not addressed"],
            "recommendations": ["suggestions for improvement"],
            "approved": true/false (whether resume passes audit)
        }}

        Return only the JSON response.
        """

        # Hugging Face Inference API call
        response = requests.post(
            'https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct',
            headers={
                'Authorization': f'Bearer {HUGGINGFACE_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'inputs': prompt,
                'parameters': {
                    'max_new_tokens': 512,
                    'temperature': 0.1,
                    'do_sample': True
                }
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and result:
                api_response = result[0].get('generated_text', '').strip()
            else:
                raise Exception("Unexpected API response format")

            # Extract JSON from response
            try:
                # Find JSON in the response
                start = api_response.find('{')
                end = api_response.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = api_response[start:end]
                    audit_result = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")

                logger.info(f"Audit completed: Accuracy {audit_result.get('accuracy_score', 0)}%")
                return audit_result

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing audit response: {e}")
                return {
                    "accuracy_score": 50,
                    "hallucinations_detected": ["Unable to parse audit response"],
                    "missing_skills": [],
                    "recommendations": ["Manual review required"],
                    "approved": False
                }
        else:
            logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
            raise Exception(f"Failed to audit resume: {response.status_code}")

    except requests.RequestException as e:
        logger.error(f"Request error during audit: {e}")
        return {
            "accuracy_score": 0,
            "hallucinations_detected": [f"API request failed: {str(e)}"],
            "missing_skills": [],
            "recommendations": ["Retry audit or manual review required"],
            "approved": False
        }
    except Exception as e:
        logger.error(f"Error during audit: {e}")
        return {
            "accuracy_score": 0,
            "hallucinations_detected": [str(e)],
            "missing_skills": [],
            "recommendations": ["Audit failed - manual review required"],
            "approved": False
        }

def audit_resume(resume_data: Dict) -> Dict:
    """Main function to audit a generated resume."""
    try:
        if 'error' in resume_data:
            logger.warning("Skipping audit due to resume generation error")
            return {
                "audit_result": {
                    "accuracy_score": 0,
                    "hallucinations_detected": ["Resume generation failed"],
                    "missing_skills": [],
                    "recommendations": ["Fix resume generation first"],
                    "approved": False
                },
                "job_title": resume_data.get('job_title', ''),
                "employer_email": resume_data.get('employer_email', '')
            }

        content = resume_data.get('content', '')
        job_details = {
            'job_title': resume_data.get('job_title', ''),
            'skills': [],  # This should come from parsed job data
            'employer_email': resume_data.get('employer_email', '')
        }

        audit_result = audit_resume_content(content, job_details)

        return {
            "audit_result": audit_result,
            "job_title": job_details['job_title'],
            "employer_email": job_details['employer_email']
        }

    except Exception as e:
        logger.error(f"Error auditing resume: {e}")
        return {
            "audit_result": {
                "accuracy_score": 0,
                "hallucinations_detected": [str(e)],
                "missing_skills": [],
                "recommendations": ["Audit error occurred"],
                "approved": False
            },
            "job_title": resume_data.get('job_title', ''),
            "employer_email": resume_data.get('employer_email', '')
        }

def audit_resumes(resumes: List[Dict]) -> List[Dict]:
    """Audit multiple resumes."""
    audits = []
    for resume in resumes:
        audit = audit_resume(resume)
        audits.append(audit)
    return audits