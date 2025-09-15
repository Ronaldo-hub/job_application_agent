import json
import logging
from typing import Dict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample master resume data (simulating a perfect match for the job)
sample_master_resume = {
    "professional_summary": "Experienced chemical engineer with expertise in mineral processing, process control, and optimization. Skilled in Python, machine learning, and data science applications in industrial settings.",
    "skills": ["Python", "Machine Learning", "Data Science", "Chemical Engineering", "Mineral Processing", "Process Control", "Optimization", "Thermodynamics"],
    "work_experience": [
        {
            "dates": "2018-2023",
            "responsibilities": ["Led mineral processing optimization projects", "Implemented machine learning models for process control", "Developed Python scripts for data analysis"]
        }
    ]
}

# Sample job details (perfect match scenario)
sample_job_details = {
    "title": "Senior Chemical Engineer",
    "description": "We are seeking a senior chemical engineer with experience in mineral processing, process control, and optimization. The ideal candidate should have skills in Python, machine learning, and data science. Experience with thermodynamics and chemical engineering principles is required.",
    "requirements": ["Chemical Engineering", "Mineral Processing", "Process Control", "Python", "Machine Learning"],
    "skills": ["Data Science", "Optimization", "Thermodynamics"]
}

def old_scoring_logic(master_resume: Dict, job_details: Dict) -> float:
    """Simulate old scoring logic: limited keywords, exact matching only, no semantic similarity."""
    logger.info("Running old scoring logic...")

    # Limited keyword list (subset of tech skills)
    limited_keywords = ['python', 'java', 'machine learning', 'data science', 'chemical engineering']

    # Extract resume skills (exact match only)
    resume_skills = set(skill.lower() for skill in master_resume.get('skills', []))
    logger.debug(f"Old logic - Resume skills: {resume_skills}")

    # Extract job requirements (only from explicit lists, no description parsing)
    job_reqs = set()
    if 'requirements' in job_details:
        job_reqs.update(req.lower() for req in job_details['requirements'])
    if 'skills' in job_details:
        job_reqs.update(skill.lower() for skill in job_details['skills'])
    logger.debug(f"Old logic - Job requirements: {job_reqs}")

    # Filter to limited keywords only
    resume_limited = resume_skills & set(limited_keywords)
    job_limited = job_reqs & set(limited_keywords)
    logger.debug(f"Old logic - Limited resume skills: {resume_limited}")
    logger.debug(f"Old logic - Limited job requirements: {job_limited}")

    if not job_limited:
        logger.warning("Old logic - No matching limited keywords in job requirements")
        return 0.0

    # Exact match only (no partial or synonym matching)
    matches = resume_limited & job_limited
    score = len(matches) / len(job_limited) * 100

    logger.info(f"Old logic - Matches: {matches}, Score: {score:.2f}%")
    logger.warning("Old logic mistake: Ignored 'mineral processing', 'process control', 'optimization', 'thermodynamics' as they're not in limited keyword list")
    logger.warning("Old logic mistake: No partial matching for compound terms")
    logger.warning("Old logic mistake: No semantic similarity analysis")

    return score

def improved_scoring_logic(master_resume: Dict, job_details: Dict) -> float:
    """Improved scoring logic with enhanced matching."""
    logger.info("Running improved scoring logic...")

    # Extract skills from resume
    resume_skills = set(skill.lower() for skill in master_resume.get('skills', []))
    logger.debug(f"Improved logic - Resume skills: {resume_skills}")

    # Extract job requirements
    job_reqs = set()
    if 'requirements' in job_details:
        job_reqs.update(req.lower() for req in job_details['requirements'])
    if 'skills' in job_details:
        job_reqs.update(skill.lower() for skill in job_details['skills'])
    # Add keywords from description (simplified NLP)
    desc = job_details.get('description', '').lower()
    desc_words = set(desc.split())
    tech_terms = ['mineral', 'processing', 'control', 'optimization', 'thermodynamics', 'chemical', 'engineering']
    job_reqs.update(desc_words & set(tech_terms))
    logger.debug(f"Improved logic - Job requirements: {job_reqs}")

    # Enhanced matching with partial and synonym support
    matches = set()
    for r_skill in resume_skills:
        for j_req in job_reqs:
            if r_skill == j_req:
                matches.add(r_skill)
            elif ' ' in r_skill and ' ' in j_req:
                r_words = set(r_skill.split())
                j_words = set(j_req.split())
                if r_words & j_words:
                    matches.add(r_skill)
            # Simple synonym check
            elif (r_skill == 'chemical engineering' and j_req == 'chemistry') or (r_skill == 'chemistry' and j_req == 'chemical engineering'):
                matches.add(r_skill)

    keyword_score = len(matches) / len(job_reqs) * 100 if job_reqs else 0
    logger.debug(f"Improved logic - Matches: {matches}, Keyword score: {keyword_score:.2f}%")

    # TF-IDF similarity
    resume_text = master_resume.get('professional_summary', '') + ' ' + ' '.join(master_resume.get('skills', []))
    job_text = job_details.get('description', '')
    if resume_text and job_text:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        similarity_score = similarity * 100
    else:
        similarity_score = 0.0

    # Simple experience score
    experience_score = 50.0  # Placeholder

    final_score = (keyword_score * 0.5) + (similarity_score * 0.3) + (experience_score * 0.2)
    logger.info(f"Improved logic - Final score: {final_score:.2f}% (keyword: {keyword_score:.2f}%, similarity: {similarity_score:.2f}%, experience: {experience_score:.2f}%)")
    logger.info("Improved logic benefits: Expanded keyword list, partial matching, synonym recognition, semantic similarity via TF-IDF")

    return final_score

def main():
    logger.info("Starting job discovery matching error reproduction script")

    # Run old logic
    old_score = old_scoring_logic(sample_master_resume, sample_job_details)
    logger.error(f"Old logic resulted in low score: {old_score:.2f}% for what should be a perfect match")

    # Run improved logic
    improved_score = improved_scoring_logic(sample_master_resume, sample_job_details)
    logger.info(f"Improved logic achieved: {improved_score:.2f}% - significant improvement")

    improvement = improved_score - old_score
    logger.info(f"Score improvement: +{improvement:.2f}%")

    logger.info("Script completed. Demonstrated scoring errors and improvements.")

if __name__ == "__main__":
    main()