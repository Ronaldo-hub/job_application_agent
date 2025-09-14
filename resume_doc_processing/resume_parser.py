import json
import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pdfplumber
from docx import Document

# Import POPIA compliance
try:
    from compliance_monitoring_testing import popia_compliance
except ImportError:
    logging.warning("POPIA compliance module not available")
    popia_compliance = None

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_pdf_resume(file_path: str) -> Dict:
    """Parse PDF resume using pdfplumber."""
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"

        return parse_resume_text(text)
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}")
        raise

def parse_docx_resume(file_path: str) -> Dict:
    """Parse DOCX resume using python-docx."""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"

        return parse_resume_text(text)
    except Exception as e:
        logger.error(f"Error parsing DOCX {file_path}: {e}")
        raise

def parse_resume_text(text: str) -> Dict:
    """Parse resume text to extract structured data."""
    try:
        # Extract header information
        header = extract_header(text)

        # Extract sections
        summary = extract_summary(text)
        skills = extract_skills(text)
        experience = extract_experience(text)
        education = extract_education(text)
        certifications = extract_certifications(text)

        parsed_resume = {
            "personal_info": header,
            "summary": summary,
            "skills": skills,
            "experience": experience,
            "education": education,
            "certifications": certifications
        }

        logger.info("Resume parsed successfully")
        return parsed_resume

    except Exception as e:
        logger.error(f"Error parsing resume text: {e}")
        raise

def extract_header(text: str) -> Dict:
    """Extract personal information from header."""
    header = {
        "name": "",
        "email": "",
        "phone": "",
        "location": ""
    }

    # Extract name (first line or prominent text)
    lines = text.strip().split('\n')
    if lines:
        header["name"] = lines[0].strip()

    # Extract email
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if email_match:
        header["email"] = email_match.group(0)

    # Extract phone
    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_match:
        header["phone"] = phone_match.group(0)

    # Extract location (simple pattern)
    location_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})', text)
    if location_match:
        header["location"] = location_match.group(0)

    return header

def extract_summary(text: str) -> str:
    """Extract professional summary."""
    # Look for summary section
    summary_patterns = [
        r'Summary[:\s]*(.*?)(?:\n\n|\n[A-Z]|$)',
        r'Professional Summary[:\s]*(.*?)(?:\n\n|\n[A-Z]|$)',
        r'Objective[:\s]*(.*?)(?:\n\n|\n[A-Z]|$)',
        r'Profile[:\s]*(.*?)(?:\n\n|\n[A-Z]|$)'
    ]

    for pattern in summary_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

    # Fallback: first paragraph after header
    paragraphs = re.split(r'\n\s*\n', text)
    if len(paragraphs) > 1:
        return paragraphs[1].strip()

    return ""

def extract_skills(text: str) -> List[str]:
    """Extract skills from resume."""
    skills = []

    # Look for skills section
    skills_match = re.search(r'Skills[:\s]*(.*?)(?:\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
    if skills_match:
        skills_text = skills_match.group(1)
        # Split by commas, bullets, or newlines
        skills = re.split(r'[,\n•\-]', skills_text)
        skills = [skill.strip() for skill in skills if skill.strip()]

    return skills

def extract_experience(text: str) -> List[Dict]:
    """Extract work experience."""
    experience = []

    # Look for experience section
    exp_match = re.search(r'Experience[:\s]*(.*?)(?:\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
    if exp_match:
        exp_text = exp_match.group(1)

        # Split into individual experiences (rough approximation)
        exp_entries = re.split(r'\n\s*\n', exp_text)

        for entry in exp_entries:
            if entry.strip():
                # Extract title, company, dates
                lines = entry.strip().split('\n')
                if lines:
                    title_company = lines[0]
                    description = ' '.join(lines[1:]) if len(lines) > 1 else ""

                    exp_item = {
                        "title": title_company,
                        "company": "",
                        "location": "",
                        "start_date": "",
                        "end_date": "",
                        "description": description
                    }
                    experience.append(exp_item)

    return experience

def extract_education(text: str) -> List[Dict]:
    """Extract education information."""
    education = []

    # Look for education section
    edu_match = re.search(r'Education[:\s]*(.*?)(?:\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
    if edu_match:
        edu_text = edu_match.group(1)

        # Split into individual education entries
        edu_entries = re.split(r'\n\s*\n', edu_text)

        for entry in edu_entries:
            if entry.strip():
                lines = entry.strip().split('\n')
                if lines:
                    degree_institution = lines[0]
                    details = ' '.join(lines[1:]) if len(lines) > 1 else ""

                    edu_item = {
                        "degree": degree_institution,
                        "institution": "",
                        "location": "",
                        "graduation_date": "",
                        "gpa": ""
                    }
                    education.append(edu_item)

    return education

def extract_certifications(text: str) -> List[str]:
    """Extract certifications."""
    certifications = []

    # Look for certifications section
    cert_match = re.search(r'Certifications?[:\s]*(.*?)(?:\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
    if cert_match:
        cert_text = cert_match.group(1)
        # Split by commas, bullets, or newlines
        certifications = re.split(r'[,\n•\-]', cert_text)
        certifications = [cert.strip() for cert in certifications if cert.strip()]

    return certifications

def parse_resume_file(file_path: str, user_id: str = None, anonymize: bool = True) -> Dict:
    """Main function to parse resume file (PDF or DOCX) with POPIA compliance."""
    try:
        # Parse the resume
        if file_path.lower().endswith('.pdf'):
            parsed_resume = parse_pdf_resume(file_path)
        elif file_path.lower().endswith('.docx'):
            parsed_resume = parse_docx_resume(file_path)
        else:
            raise ValueError("Unsupported file format. Only PDF and DOCX are supported.")

        # Apply POPIA anonymization if requested
        if anonymize and popia_compliance:
            logger.info(f"Applying POPIA anonymization for user {user_id}")
            anonymized_resume, mapping_dict = popia_compliance.anonymize_user_data(parsed_resume)

            # Store anonymization mapping for potential re-identification
            if user_id and mapping_dict:
                parsed_resume['_anonymization_mapping'] = mapping_dict
                parsed_resume['_anonymized_at'] = str(datetime.now())
                parsed_resume['_user_id'] = user_id

            parsed_resume = anonymized_resume

            # Audit the data processing
            if user_id:
                popia_compliance.audit_data_processing(
                    user_id,
                    'resume_parsing',
                    ['personal_info', 'career_data']
                )

        logger.info("Resume parsed successfully with POPIA compliance")
        return parsed_resume

    except Exception as e:
        logger.error(f"Error parsing resume file {file_path}: {e}")
        return {
            "error": str(e),
            "personal_info": {"name": "", "email": "", "phone": "", "location": ""},
            "summary": "",
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": []
        }

def merge_resume_data(existing_resume: Dict, new_resume: Dict) -> Dict:
    """Merge parsed resume data with existing master resume."""
    try:
        # Update personal info if empty
        for key in existing_resume.get("personal_info", {}):
            if not existing_resume["personal_info"][key] and new_resume.get("personal_info", {}).get(key):
                existing_resume["personal_info"][key] = new_resume["personal_info"][key]

        # Merge skills
        existing_skills = set(existing_resume.get("skills", []))
        new_skills = set(new_resume.get("skills", []))
        existing_resume["skills"] = list(existing_skills.union(new_skills))

        # Merge experience
        existing_resume["experience"].extend(new_resume.get("experience", []))

        # Merge education
        existing_resume["education"].extend(new_resume.get("education", []))

        # Merge certifications
        existing_certs = set(existing_resume.get("certifications", []))
        new_certs = set(new_resume.get("certifications", []))
        existing_resume["certifications"] = list(existing_certs.union(new_certs))

        # Update summary if empty
        if not existing_resume.get("summary") and new_resume.get("summary"):
            existing_resume["summary"] = new_resume["summary"]

        return existing_resume

    except Exception as e:
        logger.error(f"Error merging resume data: {e}")
        return existing_resume