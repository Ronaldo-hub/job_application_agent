import json
import os
import logging
import spacy
from typing import Dict, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    logger.error("spaCy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm'")
    raise

# Load master resume
def load_master_resume() -> Dict:
    """Load the master resume from JSON file."""
    try:
        # Get the directory of this module
        module_dir = os.path.dirname(os.path.abspath(__file__))
        master_resume_path = os.path.join(module_dir, 'master_resume.json')
        with open(master_resume_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("master_resume.json not found")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing master_resume.json: {e}")
        raise

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from job description."""
    if not text:
        logger.debug("extract_keywords: No text provided")
        return []

    logger.debug(f"extract_keywords: Input text length: {len(text)}")

    # Simple keyword extraction (can be enhanced with NLP)
    words = text.lower().split()
    logger.debug(f"extract_keywords: Extracted {len(words)} words from text")

    keywords = []

    # Common tech skills and domain-specific terms
    tech_skills = ['python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker', 'kubernetes',
                   'machine learning', 'ai', 'data science', 'devops', 'agile', 'scrum',
                   'mineral processing', 'hazardous waste', 'reverse osmosis', 'pyrolysis', 'heat transfer',
                   'mass transfer', 'thermodynamics', 'reactor technology', 'particle technology', 'process control',
                   'optimization', 'experimental design', 'numerical methods', 'iso standards']

    for word in words:
        word = word.strip('.,!?()[]{}')
        if word in tech_skills and word not in keywords:
            keywords.append(word)

    logger.debug(f"extract_keywords: Found {len(keywords)} matching keywords: {keywords}")
    return keywords

def calculate_fit_score(master_resume: Dict, job_details: Dict) -> float:
    """Calculate fit score between resume and job requirements."""
    try:
        logger.debug(f"calculate_fit_score: Starting for job {job_details.get('title', 'Unknown')}")

        # Extract skills from master resume
        resume_skills = set()
        if 'skills' in master_resume:
            resume_skills = set(skill.lower() for skill in master_resume['skills'])
        logger.debug(f"calculate_fit_score: Resume skills: {resume_skills}")

        # Extract requirements from job
        job_requirements = set()
        if 'requirements' in job_details:
            job_requirements = set(req.lower() for req in job_details['requirements'])
        if 'skills' in job_details:
            job_requirements.update(set(skill.lower() for skill in job_details['skills']))
        logger.debug(f"calculate_fit_score: Initial job requirements: {job_requirements}")

        # Extract keywords from job description with better filtering
        job_description = job_details.get('description', '')
        if job_description:
            doc = nlp(job_description.lower())
            desc_keywords = set()
            for token in doc:
                # More selective keyword extraction - focus on technical terms
                if (token.pos_ in ['NOUN', 'PROPN'] and len(token.text) > 3 and not token.is_stop and
                    not token.text.isdigit() and token.text not in ['company', 'position', 'candidate', 'team']):
                    desc_keywords.add(token.text)
            job_requirements.update(desc_keywords)
        logger.debug(f"calculate_fit_score: Final job requirements: {job_requirements}")

        if not job_requirements:
            logger.debug("calculate_fit_score: No job requirements found")
            return 0.0

        # Enhanced keyword matching with partial matching
        matching_skills = set()
        for resume_skill in resume_skills:
            for job_req in job_requirements:
                # Exact match
                if resume_skill == job_req:
                    matching_skills.add(resume_skill)
                # Partial match for compound terms
                elif (' ' in resume_skill or ' ' in job_req):
                    resume_words = set(resume_skill.split())
                    job_words = set(job_req.split())
                    if resume_words & job_words:  # Intersection of words
                        matching_skills.add(resume_skill)
                # Synonym matching for common terms
                elif _is_synonym_match(resume_skill, job_req):
                    matching_skills.add(resume_skill)

        keyword_score = len(matching_skills) / len(job_requirements) * 100 if job_requirements else 0
        logger.debug(f"calculate_fit_score: Enhanced matching skills: {matching_skills}, keyword_score: {keyword_score:.2f}%")

        # Improved TF-IDF similarity using professional summary and experience
        resume_text_parts = []
        if 'professional_summary' in master_resume:
            resume_text_parts.append(master_resume['professional_summary'])
        if 'skills' in master_resume:
            resume_text_parts.append(' '.join(master_resume['skills']))
        if 'work_experience' in master_resume:
            for exp in master_resume['work_experience'][:3]:  # Top 3 experiences
                if 'responsibilities' in exp:
                    resume_text_parts.append(' '.join(exp['responsibilities']))

        resume_text = ' '.join(resume_text_parts)
        job_text = job_description
        logger.debug(f"calculate_fit_score: Enhanced resume text length: {len(resume_text)}, job text length: {len(job_text)}")

        if resume_text and job_text:
            vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))  # Include bigrams
            try:
                tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                similarity_score = similarity * 100
                logger.debug(f"calculate_fit_score: Enhanced TF-IDF similarity: {similarity:.4f}, similarity_score: {similarity_score:.2f}%")
            except Exception as e:
                logger.error(f"calculate_fit_score: TF-IDF error: {e}")
                similarity_score = 0.0
        else:
            similarity_score = 0.0
            logger.debug("calculate_fit_score: No text for TF-IDF similarity")

        # Add experience matching score
        experience_score = _calculate_experience_match(master_resume, job_details)
        logger.debug(f"calculate_fit_score: Experience score: {experience_score:.2f}%")

        # Weighted average with experience component
        final_score = (keyword_score * 0.5) + (similarity_score * 0.3) + (experience_score * 0.2)
        logger.info(f"Fit score for {job_details.get('title', 'Unknown')}: {final_score:.1f}% (keyword: {keyword_score:.1f}%, similarity: {similarity_score:.1f}%, experience: {experience_score:.1f}%)")
        return final_score

    except Exception as e:
        logger.error(f"Error calculating fit score: {e}")
        return 0.0

def _is_synonym_match(skill1: str, skill2: str) -> bool:
    """Check if two skills are synonyms."""
    synonym_pairs = [
        ('chemistry', 'chemical engineering'),
        ('chemical engineering', 'chemistry'),
        ('process control', 'control systems'),
        ('control systems', 'process control'),
        ('mineral processing', 'hydrometallurgy'),
        ('hydrometallurgy', 'mineral processing'),
        ('data science', 'machine learning'),
        ('machine learning', 'data science'),
        ('ai', 'artificial intelligence'),
        ('artificial intelligence', 'ai'),
    ]

    for pair in synonym_pairs:
        if (skill1 == pair[0] and skill2 == pair[1]) or (skill1 == pair[1] and skill2 == pair[0]):
            return True
    return False

def _calculate_experience_match(master_resume: Dict, job_details: Dict) -> float:
    """Calculate experience matching score."""
    try:
        # Extract years of experience from resume
        resume_experience_years = 0
        if 'work_experience' in master_resume:
            for exp in master_resume['work_experience']:
                if 'dates' in exp:
                    # Simple year extraction - could be improved
                    dates = exp['dates']
                    if '-' in dates:
                        try:
                            start_year = int(dates.split('-')[0].strip()[:4])
                            end_year = int(dates.split('-')[1].strip()[:4])
                            resume_experience_years += max(0, end_year - start_year)
                        except:
                            pass

        # Extract required experience from job description
        job_description = job_details.get('description', '').lower()
        required_years = 0

        # Look for patterns like "3 years", "5+ years", etc.
        import re
        year_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'experience\s*(?:of\s*)?(\d+)\+?\s*years',
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience'
        ]

        for pattern in year_patterns:
            matches = re.findall(pattern, job_description)
            if matches:
                required_years = max(required_years, int(matches[0]))

        if required_years == 0:
            return 50.0  # Neutral score if no experience requirement specified

        # Calculate match score
        if resume_experience_years >= required_years:
            return 100.0
        elif resume_experience_years >= required_years * 0.8:
            return 80.0
        elif resume_experience_years >= required_years * 0.5:
            return 60.0
        else:
            return 30.0

    except Exception as e:
        logger.error(f"Error calculating experience match: {e}")
        return 50.0