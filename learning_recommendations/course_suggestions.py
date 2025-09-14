import os
import logging
import requests
import json
from typing import Dict, List, Set
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Course platforms and their APIs
COURSE_PLATFORMS = {
    'coursera': {
        'api_url': 'https://api.coursera.org/api/courses.v1',
        'search_param': 'q',
        'results_key': 'elements'
    },
    'udemy': {
        'api_url': 'https://www.udemy.com/api-2.0/courses/',
        'headers': {'Authorization': f'Bearer {os.getenv("UDEMY_CLIENT_ID")}'},
        'search_param': 'search',
        'results_key': 'results'
    },
    'edx': {
        'api_url': 'https://www.edx.org/api/v1/catalog/search',
        'search_param': 'query',
        'results_key': 'objects'
    }
}

# Predefined course database (fallback when APIs are unavailable)
PREDEFINED_COURSES = {
    'python': [
        {'title': 'Python for Everybody', 'platform': 'Coursera', 'url': 'https://www.coursera.org/specializations/python', 'duration': '8 months'},
        {'title': 'Complete Python Bootcamp', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/complete-python-bootcamp/', 'duration': '12 hours'},
        {'title': 'Python Programming Fundamentals', 'platform': 'edX', 'url': 'https://www.edx.org/course/python-programming-fundamentals', 'duration': '6 weeks'}
    ],
    'machine learning': [
        {'title': 'Machine Learning by Andrew Ng', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/machine-learning', 'duration': '11 weeks'},
        {'title': 'Machine Learning A-Z', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/machine-learning-az/', 'duration': '40 hours'},
        {'title': 'Introduction to Machine Learning', 'platform': 'edX', 'url': 'https://www.edx.org/course/introduction-to-machine-learning', 'duration': '8 weeks'}
    ],
    'data science': [
        {'title': 'IBM Data Science Professional Certificate', 'platform': 'Coursera', 'url': 'https://www.coursera.org/professional-certificates/ibm-data-science', 'duration': '11 months'},
        {'title': 'Data Science and Machine Learning Bootcamp', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/data-science-and-machine-learning-bootcamp-with-r/', 'duration': '25 hours'},
        {'title': 'Data Science MicroMasters', 'platform': 'edX', 'url': 'https://www.edx.org/micromasters/columbiax-data-science', 'duration': '1 year'}
    ],
    'javascript': [
        {'title': 'JavaScript Algorithms and Data Structures', 'platform': 'freeCodeCamp', 'url': 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/', 'duration': '300 hours'},
        {'title': 'The Modern JavaScript Bootcamp', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/modern-javascript/', 'duration': '30 hours'},
        {'title': 'JavaScript Introduction', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/javascript-introduction', 'duration': '20 hours'}
    ],
    'react': [
        {'title': 'React - The Complete Guide', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/react-the-complete-guide-incl-redux/', 'duration': '40 hours'},
        {'title': 'Front-End Web Development with React', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/front-end-react', 'duration': '4 months'},
        {'title': 'React for Beginners', 'platform': 'Codecademy', 'url': 'https://www.codecademy.com/learn/react-101', 'duration': '10 hours'}
    ],
    'aws': [
        {'title': 'AWS Cloud Practitioner Essentials', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/aws-cloud-practitioner-essentials', 'duration': '4 weeks'},
        {'title': 'AWS Certified Solutions Architect', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/aws-solutions-architect-associate/', 'duration': '20 hours'},
        {'title': 'AWS Fundamentals', 'platform': 'edX', 'url': 'https://www.edx.org/course/aws-fundamentals', 'duration': '8 weeks'}
    ],
    'docker': [
        {'title': 'Docker for Beginners', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/docker-for-beginners/', 'duration': '6 hours'},
        {'title': 'Container Orchestration with Docker', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/container-orchestration-docker', 'duration': '8 weeks'},
        {'title': 'Docker Essentials', 'platform': 'Linux Academy', 'url': 'https://linuxacademy.com/course/docker-essentials/', 'duration': '4 hours'}
    ]
}

def analyze_skill_gaps(master_resume: Dict, job_requirements: List[str]) -> List[str]:
    """Analyze skill gaps between resume and job requirements."""
    try:
        # Extract skills from master resume
        resume_skills = set()
        if 'skills' in master_resume:
            resume_skills = set(skill.lower() for skill in master_resume['skills'])

        # Extract skills from experience and education
        if 'work_experience' in master_resume:
            for exp in master_resume['work_experience']:
                if 'responsibilities' in exp:
                    for resp in exp['responsibilities']:
                        # Simple keyword extraction from responsibilities
                        words = resp.lower().split()
                        for word in words:
                            if len(word) > 3 and word not in ['with', 'from', 'that', 'this', 'have', 'been']:
                                resume_skills.add(word.strip('.,!?()[]{}'))

        # Normalize job requirements
        normalized_requirements = set(req.lower() for req in job_requirements)

        # Find gaps
        skill_gaps = []
        for req in normalized_requirements:
            if req not in resume_skills:
                # Check for partial matches
                found_match = False
                for skill in resume_skills:
                    if req in skill or skill in req:
                        found_match = True
                        break
                if not found_match:
                    skill_gaps.append(req)

        logger.info(f"Found {len(skill_gaps)} skill gaps: {skill_gaps}")
        return skill_gaps

    except Exception as e:
        logger.error(f"Error analyzing skill gaps: {e}")
        return []

async def get_course_suggestions(skill_gaps: List[str]) -> Dict[str, List[Dict]]:
    """Get course suggestions for skill gaps."""
    suggestions = {}

    for gap in skill_gaps[:5]:  # Limit to 5 gaps
        try:
            courses = await search_courses_for_skill(gap)
            if courses:
                suggestions[gap] = courses[:3]  # Limit to 3 courses per gap
        except Exception as e:
            logger.error(f"Error getting courses for {gap}: {e}")
            # Fallback to predefined courses
            if gap in PREDEFINED_COURSES:
                suggestions[gap] = PREDEFINED_COURSES[gap][:3]

    return suggestions

async def search_courses_for_skill(skill: str) -> List[Dict]:
    """Search for courses related to a specific skill."""
    courses = []

    # Try Coursera API
    try:
        coursera_courses = await search_coursera(skill)
        courses.extend(coursera_courses)
    except Exception as e:
        logger.warning(f"Coursera search failed for {skill}: {e}")

    # Try Udemy API
    try:
        udemy_courses = await search_udemy(skill)
        courses.extend(udemy_courses)
    except Exception as e:
        logger.warning(f"Udemy search failed for {skill}: {e}")

    # Try edX API
    try:
        edx_courses = await search_edx(skill)
        courses.extend(edx_courses)
    except Exception as e:
        logger.warning(f"edX search failed for {skill}: {e}")

    # Fallback to predefined courses
    if not courses and skill in PREDEFINED_COURSES:
        courses = PREDEFINED_COURSES[skill]

    return courses

async def search_coursera(skill: str) -> List[Dict]:
    """Search Coursera for courses."""
    try:
        params = {'q': skill, 'limit': 5}
        response = requests.get(COURSE_PLATFORMS['coursera']['api_url'], params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            courses = []
            for course in data.get('elements', []):
                courses.append({
                    'title': course.get('name', ''),
                    'platform': 'Coursera',
                    'url': f"https://www.coursera.org/learn/{course.get('slug', '')}",
                    'duration': course.get('estimatedClassWorkload', 'Unknown')
                })
            return courses
    except Exception as e:
        logger.error(f"Coursera API error: {e}")

    return []

async def search_udemy(skill: str) -> List[Dict]:
    """Search Udemy for courses."""
    try:
        headers = COURSE_PLATFORMS['udemy']['headers']
        params = {'search': skill, 'page_size': 5}
        response = requests.get(COURSE_PLATFORMS['udemy']['api_url'], headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            courses = []
            for course in data.get('results', []):
                courses.append({
                    'title': course.get('title', ''),
                    'platform': 'Udemy',
                    'url': course.get('url', ''),
                    'duration': f"{course.get('estimated_content_length', 0)} hours"
                })
            return courses
    except Exception as e:
        logger.error(f"Udemy API error: {e}")

    return []

async def search_edx(skill: str) -> List[Dict]:
    """Search edX for courses."""
    try:
        params = {'query': skill, 'limit': 5}
        response = requests.get(COURSE_PLATFORMS['edx']['api_url'], params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            courses = []
            for course in data.get('objects', []):
                courses.append({
                    'title': course.get('title', ''),
                    'platform': 'edX',
                    'url': course.get('url', ''),
                    'duration': course.get('duration', 'Unknown')
                })
            return courses
    except Exception as e:
        logger.error(f"edX API error: {e}")

    return []

def calculate_improvement_potential(skill_gaps: List[str], job_requirements: List[str]) -> Dict[str, float]:
    """Calculate potential improvement in fit score after taking courses."""
    # Simple estimation: each course covers one skill gap
    total_requirements = len(set(req.lower() for req in job_requirements))
    covered_gaps = len(skill_gaps)

    if total_requirements == 0:
        return {}

    improvement = (covered_gaps / total_requirements) * 100

    return {gap: improvement for gap in skill_gaps}