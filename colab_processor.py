"""
Google Colab Processor for Resource-Intensive Tasks
This script runs in Google Colab to handle NLP processing, job fit analysis,
resume generation, and course suggestions to prevent bottlenecks in VS Code.
"""

import os
import json
import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pickle

# Google Colab specific imports
try:
    from google.colab import drive
    from google.colab import userdata
    COLAB_ENV = True
except ImportError:
    COLAB_ENV = False

# Standard ML/NLP imports
import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# API and web imports
import httpx
import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
class Config:
    # Google Drive paths
    DRIVE_MOUNT_PATH = '/content/drive'
    SHARED_FOLDER = f'{DRIVE_MOUNT_PATH}/MyDrive/JobAgent'
    INPUT_FOLDER = f'{SHARED_FOLDER}/input'
    OUTPUT_FOLDER = f'{SHARED_FOLDER}/output'
    STATUS_FILE = f'{SHARED_FOLDER}/status.json'

    # Free-tier API configurations
    ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"
    CAREERJET_BASE_URL = "https://public-api.careerjet.net/search"
    UPWORK_BASE_URL = "https://www.upwork.com/api/v3"
    SERPAPI_BASE_URL = "https://serpapi.com/search.json"
    RAPIDAPI_BASE_URL = "https://jsearch.p.rapidapi.com"

    # Processing limits
    MAX_JOBS_PER_SEARCH = 50
    MAX_RESUMES_PER_BATCH = 10
    NLP_MODEL = 'en_core_web_sm'

class ColabProcessor:
    def __init__(self):
        self.nlp = None
        self.drive_mounted = False
        self.api_keys = self.load_api_keys()

    def setup_colab_environment(self):
        """Set up Google Colab environment with Drive and dependencies."""
        if not COLAB_ENV:
            logger.warning("Not running in Google Colab environment")
            return False

        try:
            # Mount Google Drive
            drive.mount(self.Config.DRIVE_MOUNT_PATH, force_remount=True)
            self.drive_mounted = True
            logger.info("Google Drive mounted successfully")

            # Create necessary directories
            os.makedirs(self.Config.INPUT_FOLDER, exist_ok=True)
            os.makedirs(self.Config.OUTPUT_FOLDER, exist_ok=True)
            logger.info("Input/output directories created")

            # Install dependencies
            self.install_dependencies()

            # Load spaCy model
            self.load_nlp_model()

            return True
        except Exception as e:
            logger.error(f"Failed to setup Colab environment: {e}")
            return False

    def install_dependencies(self):
        """Install required dependencies in Colab."""
        try:
            os.system('pip install -q spacy httpx scikit-learn beautifulsoup4 lxml')
            os.system('python -m spacy download en_core_web_sm')
            logger.info("Dependencies installed successfully")
        except Exception as e:
            logger.error(f"Failed to install dependencies: {e}")

    def load_nlp_model(self):
        """Load spaCy NLP model."""
        try:
            self.nlp = spacy.load(self.Config.NLP_MODEL)
            logger.info("spaCy model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")

    def load_api_keys(self) -> Dict[str, str]:
        """Load API keys from Colab userdata or environment."""
        keys = {}
        if COLAB_ENV:
            try:
                keys = {
                    'adzuna_app_id': userdata.get('ADZUNA_APP_ID'),
                    'adzuna_app_key': userdata.get('ADZUNA_APP_KEY'),
                    'careerjet_key': userdata.get('CAREERJET_API_KEY'),
                    'upwork_client_id': userdata.get('UPWORK_CLIENT_ID'),
                    'upwork_client_secret': userdata.get('UPWORK_CLIENT_SECRET'),
                    'serpapi_key': userdata.get('SERPAPI_API_KEY'),
                    'rapidapi_key': userdata.get('RAPIDAPI_KEY'),
                    'huggingface_key': userdata.get('HUGGINGFACE_API_KEY')
                }
            except Exception as e:
                logger.warning(f"Could not load Colab secrets: {e}")

        # Fallback to environment variables
        for key in keys:
            if not keys[key]:
                env_key = key.upper()
                keys[key] = os.getenv(env_key)

        return keys

    def update_status(self, status: str, progress: float = 0.0, message: str = ""):
        """Update processing status in Google Drive."""
        if not self.drive_mounted:
            return

        status_data = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'progress': progress,
            'message': message
        }

        try:
            with open(self.Config.STATUS_FILE, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update status: {e}")

    async def process_job_search(self, search_params: Dict) -> List[Dict]:
        """Process job search using free-tier APIs."""
        self.update_status("searching", 0.1, "Starting job search")

        keywords = search_params.get('keywords', '')
        location = search_params.get('location', '')

        # Use free-tier APIs only
        search_functions = [
            self.search_adzuna,
            self.search_careerjet,
            self.search_upwork,
            self.search_serpapi_google,
            self.search_rapidapi_jobs
        ]

        # Run searches in parallel
        tasks = []
        for func in search_functions:
            task = asyncio.create_task(func(keywords, location))
            tasks.append(task)

        self.update_status("searching", 0.3, "Querying job APIs")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        all_jobs = []
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)

        # Remove duplicates and limit results
        unique_jobs = self.remove_duplicates(all_jobs)
        final_jobs = unique_jobs[:self.Config.MAX_JOBS_PER_SEARCH]

        self.update_status("searching", 0.8, f"Found {len(final_jobs)} jobs")

        # Save results to Drive
        self.save_to_drive('job_search_results.json', final_jobs)

        self.update_status("completed", 1.0, f"Job search completed with {len(final_jobs)} results")
        return final_jobs

    def analyze_job_fit(self, jobs: List[Dict], master_resume: Dict) -> List[Dict]:
        """Analyze job fit using spaCy and ML models."""
        self.update_status("analyzing", 0.1, "Starting fit analysis")

        analyzed_jobs = []
        total_jobs = len(jobs)

        for i, job in enumerate(jobs):
            try:
                fit_score = self.calculate_fit_score(master_resume, job)
                job['fit_score'] = fit_score
                analyzed_jobs.append(job)

                # Update progress
                progress = 0.1 + (i / total_jobs) * 0.8
                self.update_status("analyzing", progress, f"Analyzed {i+1}/{total_jobs} jobs")

            except Exception as e:
                logger.error(f"Error analyzing job {job.get('title', 'Unknown')}: {e}")
                job['fit_score'] = 0.0
                analyzed_jobs.append(job)

        # Separate high and low fit jobs
        high_fit = [job for job in analyzed_jobs if job['fit_score'] >= 90]
        low_fit = [job for job in analyzed_jobs if job['fit_score'] < 90]

        results = {
            'high_fit_jobs': high_fit,
            'low_fit_jobs': low_fit,
            'skill_gaps': self.analyze_skill_gaps(master_resume, low_fit)
        }

        self.save_to_drive('fit_analysis_results.json', results)
        self.update_status("completed", 1.0, f"Fit analysis completed. High-fit: {len(high_fit)}, Low-fit: {len(low_fit)}")

        return analyzed_jobs

    def calculate_fit_score(self, master_resume: Dict, job_details: Dict) -> float:
        """Calculate fit score between resume and job requirements."""
        try:
            # Extract skills from master resume
            resume_skills = set()
            if 'skills' in master_resume:
                resume_skills = set(skill.lower() for skill in master_resume['skills'])

            # Extract requirements from job
            job_requirements = set()
            if 'requirements' in job_details:
                job_requirements = set(req.lower() for req in job_details['requirements'])
            if 'skills' in job_details:
                job_requirements.update(set(skill.lower() for skill in job_details['skills']))

            # Extract keywords from job description using spaCy
            job_description = job_details.get('description', '')
            if job_description and self.nlp:
                doc = self.nlp(job_description.lower())
                desc_keywords = set()
                for token in doc:
                    if token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and len(token.text) > 2 and not token.is_stop:
                        desc_keywords.add(token.text)
                job_requirements.update(desc_keywords)

            if not job_requirements:
                return 0.0

            # Calculate keyword match score
            matching_skills = resume_skills.intersection(job_requirements)
            keyword_score = len(matching_skills) / len(job_requirements) * 100

            # Calculate TF-IDF similarity for description
            resume_text = ' '.join(master_resume.get('skills', []))
            job_text = job_description

            if resume_text and job_text:
                vectorizer = TfidfVectorizer(stop_words='english')
                try:
                    tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
                    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                    similarity_score = similarity * 100
                except:
                    similarity_score = 0.0
            else:
                similarity_score = 0.0

            # Weighted average
            final_score = (keyword_score * 0.7) + (similarity_score * 0.3)

            return min(final_score, 100.0)

        except Exception as e:
            logger.error(f"Error calculating fit score: {e}")
            return 0.0

    def analyze_skill_gaps(self, master_resume: Dict, low_fit_jobs: List[Dict]) -> List[str]:
        """Analyze skill gaps from low-fit jobs."""
        all_requirements = []
        for job in low_fit_jobs:
            all_requirements.extend(job.get('requirements', []))
            all_requirements.extend(job.get('skills', []))

        # Extract skills from master resume
        resume_skills = set()
        if 'skills' in master_resume:
            resume_skills = set(skill.lower() for skill in master_resume['skills'])

        # Find gaps
        skill_gaps = []
        for req in set(all_requirements):
            req_lower = req.lower()
            if req_lower not in resume_skills:
                # Check for partial matches
                found_match = False
                for skill in resume_skills:
                    if req_lower in skill or skill in req_lower:
                        found_match = True
                        break
                if not found_match:
                    skill_gaps.append(req)

        return skill_gaps[:10]  # Limit to top 10 gaps

    def generate_resumes(self, high_fit_jobs: List[Dict], master_resume: Dict) -> List[Dict]:
        """Generate ATS-optimized resumes for high-fit jobs."""
        self.update_status("generating", 0.1, "Starting resume generation")

        generated_resumes = []
        total_jobs = min(len(high_fit_jobs), self.Config.MAX_RESUMES_PER_BATCH)

        for i, job in enumerate(high_fit_jobs[:total_jobs]):
            try:
                resume = self.generate_single_resume(master_resume, job)
                generated_resumes.append(resume)

                # Update progress
                progress = 0.1 + (i / total_jobs) * 0.8
                self.update_status("generating", progress, f"Generated {i+1}/{total_jobs} resumes")

            except Exception as e:
                logger.error(f"Error generating resume for {job.get('title', 'Unknown')}: {e}")

        self.save_to_drive('generated_resumes.json', generated_resumes)
        self.update_status("completed", 1.0, f"Resume generation completed: {len(generated_resumes)} resumes")

        return generated_resumes

    def generate_single_resume(self, master_resume: Dict, job_details: Dict) -> Dict:
        """Generate a single ATS-optimized resume."""
        # This would integrate with Hugging Face API for resume generation
        # For now, return a placeholder structure
        return {
            'job_title': job_details.get('title', ''),
            'company': job_details.get('company', ''),
            'fit_score': job_details.get('fit_score', 0),
            'content': f"Generated resume for {job_details.get('title', '')}",
            'word_file_path': f"resume_{job_details.get('id', 'unknown')}.docx",
            'pdf_file_path': f"resume_{job_details.get('id', 'unknown')}.pdf"
        }

    def suggest_courses(self, skill_gaps: List[str]) -> Dict[str, List[Dict]]:
        """Generate course suggestions for skill gaps."""
        self.update_status("suggesting", 0.1, "Starting course suggestions")

        suggestions = {}

        for gap in skill_gaps[:5]:  # Limit to 5 gaps
            try:
                courses = self.get_course_suggestions(gap)
                if courses:
                    suggestions[gap] = courses[:3]  # 3 courses per gap
            except Exception as e:
                logger.error(f"Error getting courses for {gap}: {e}")

        self.save_to_drive('course_suggestions.json', suggestions)
        self.update_status("completed", 1.0, f"Course suggestions completed for {len(suggestions)} gaps")

        return suggestions

    def get_course_suggestions(self, skill: str) -> List[Dict]:
        """Get course suggestions for a specific skill."""
        # Free course suggestions
        free_courses = {
            'python': [
                {'title': 'Python for Everybody', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/python', 'duration': '8 weeks'},
                {'title': 'Automate the Boring Stuff with Python', 'platform': 'freeCodeCamp', 'url': 'https://automatetheboringstuff.com/', 'duration': 'Self-paced'},
                {'title': 'Python Programming', 'platform': 'Codecademy', 'url': 'https://www.codecademy.com/learn/learn-python-3', 'duration': '25 hours'}
            ],
            'javascript': [
                {'title': 'JavaScript Algorithms and Data Structures', 'platform': 'freeCodeCamp', 'url': 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/', 'duration': '300 hours'},
                {'title': 'Eloquent JavaScript', 'platform': 'Book/Online', 'url': 'https://eloquentjavascript.net/', 'duration': 'Self-paced'},
                {'title': 'JavaScript30', 'platform': 'Wes Bos', 'url': 'https://javascript30.com/', 'duration': '30 days'}
            ],
            'machine learning': [
                {'title': 'Machine Learning Crash Course', 'platform': 'Google', 'url': 'https://developers.google.com/machine-learning/crash-course', 'duration': '15 hours'},
                {'title': 'Fast.ai Practical Deep Learning', 'platform': 'fast.ai', 'url': 'https://course.fast.ai/', 'duration': 'Self-paced'},
                {'title': 'Andrew Ng ML Course Notes', 'platform': 'Stanford', 'url': 'https://cs229.stanford.edu/', 'duration': 'Self-paced'}
            ]
        }

        return free_courses.get(skill.lower(), [])

    # Free-tier API implementations
    async def search_adzuna(self, keywords: str, location: str) -> List[Dict]:
        """Search jobs using Adzuna API (free tier)."""
        if not self.api_keys.get('adzuna_app_id') or not self.api_keys.get('adzuna_app_key'):
            return []

        try:
            url = f"{self.Config.ADZUNA_BASE_URL}/us/search/1"
            params = {
                'app_id': self.api_keys['adzuna_app_id'],
                'app_key': self.api_keys['adzuna_app_key'],
                'what': keywords,
                'where': location,
                'results_per_page': 10
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                jobs = []
                for result in data.get('results', []):
                    job = {
                        'id': f"adzuna_{result.get('id', '')}",
                        'title': result.get('title', ''),
                        'company': result.get('company', {}).get('display_name', ''),
                        'location': result.get('location', {}).get('display_name', ''),
                        'description': result.get('description', ''),
                        'url': result.get('redirect_url', ''),
                        'requirements': self.extract_keywords(result.get('description', '')),
                        'source': 'Adzuna'
                    }
                    jobs.append(job)
                return jobs
        except Exception as e:
            logger.error(f"Adzuna search failed: {e}")

        return []

    async def search_careerjet(self, keywords: str, location: str) -> List[Dict]:
        """Search jobs using Careerjet API (free)."""
        try:
            params = {
                'keywords': keywords,
                'location': location,
                'pagesize': 10
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(self.Config.CAREERJET_BASE_URL, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                jobs = []
                for result in data.get('jobs', []):
                    job = {
                        'id': f"careerjet_{result.get('id', '')}",
                        'title': result.get('title', ''),
                        'company': result.get('company', ''),
                        'location': result.get('locations', ''),
                        'description': result.get('description', ''),
                        'url': result.get('url', ''),
                        'requirements': self.extract_keywords(result.get('description', '')),
                        'source': 'Careerjet'
                    }
                    jobs.append(job)
                return jobs
        except Exception as e:
            logger.error(f"Careerjet search failed: {e}")

        return []

    async def search_upwork(self, keywords: str, location: str) -> List[Dict]:
        """Search jobs using Upwork API (free tier)."""
        if not self.api_keys.get('upwork_client_id') or not self.api_keys.get('upwork_client_secret'):
            return []

        try:
            # Get access token
            auth_url = f"{self.Config.UPWORK_BASE_URL}/oauth2/token"
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.api_keys['upwork_client_id'],
                'client_secret': self.api_keys['upwork_client_secret']
            }

            async with httpx.AsyncClient() as client:
                auth_response = await client.post(auth_url, data=auth_data, timeout=10)

            if auth_response.status_code != 200:
                return []

            token = auth_response.json().get('access_token')

            # Search jobs
            search_url = f"{self.Config.UPWORK_BASE_URL}/jobs/search"
            headers = {'Authorization': f'Bearer {token}'}
            params = {'q': keywords, 'limit': 10}

            async with httpx.AsyncClient() as client:
                response = await client.get(search_url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                jobs = []
                for result in data.get('jobs', []):
                    job = {
                        'id': f"upwork_{result.get('id', '')}",
                        'title': result.get('title', ''),
                        'company': result.get('client', {}).get('name', ''),
                        'location': result.get('location', ''),
                        'description': result.get('description', ''),
                        'url': result.get('url', ''),
                        'requirements': result.get('skills', []),
                        'source': 'Upwork'
                    }
                    jobs.append(job)
                return jobs
        except Exception as e:
            logger.error(f"Upwork search failed: {e}")

        return []

    async def search_serpapi_google(self, keywords: str, location: str) -> List[Dict]:
        """Search jobs using SerpApi Google Jobs (free tier)."""
        if not self.api_keys.get('serpapi_key'):
            return []

        try:
            params = {
                'engine': 'google_jobs',
                'q': keywords,
                'location': location,
                'api_key': self.api_keys['serpapi_key']
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(self.Config.SERPAPI_BASE_URL, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                jobs = []
                for result in data.get('jobs_results', []):
                    job = {
                        'id': f"serpapi_{hash(result.get('title', ''))}",
                        'title': result.get('title', ''),
                        'company': result.get('company_name', ''),
                        'location': result.get('location', ''),
                        'description': result.get('description', ''),
                        'url': result.get('related_links', [{}])[0].get('link', ''),
                        'requirements': self.extract_keywords(result.get('description', '')),
                        'source': 'SerpApi Google'
                    }
                    jobs.append(job)
                return jobs
        except Exception as e:
            logger.error(f"SerpApi search failed: {e}")

        return []

    async def search_rapidapi_jobs(self, keywords: str, location: str) -> List[Dict]:
        """Search jobs using RapidAPI Job Search (free tier)."""
        if not self.api_keys.get('rapidapi_key'):
            return []

        try:
            url = f"{self.Config.RAPIDAPI_BASE_URL}/search"
            headers = {
                'X-RapidAPI-Key': self.api_keys['rapidapi_key'],
                'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
            }
            params = {
                'query': f"{keywords} in {location}" if location else keywords,
                'num_pages': 1
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                jobs = []
                for result in data.get('data', []):
                    job = {
                        'id': f"rapidapi_{result.get('job_id', '')}",
                        'title': result.get('job_title', ''),
                        'company': result.get('employer_name', ''),
                        'location': result.get('job_city', ''),
                        'description': result.get('job_description', ''),
                        'url': result.get('job_apply_link', ''),
                        'requirements': result.get('job_required_skills', []),
                        'source': 'RapidAPI'
                    }
                    jobs.append(job)
                return jobs
        except Exception as e:
            logger.error(f"RapidAPI search failed: {e}")

        return []

    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text using spaCy."""
        if not text or not self.nlp:
            return []

        doc = self.nlp(text.lower())
        keywords = []

        # Common tech skills to look for
        tech_skills = {
            'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker',
            'kubernetes', 'machine learning', 'ai', 'data science', 'devops',
            'agile', 'scrum', 'git', 'linux', 'api', 'rest', 'graphql'
        }

        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and len(token.text) > 2 and not token.is_stop:
                if token.text in tech_skills:
                    keywords.append(token.text)

        return list(set(keywords))[:10]  # Return unique keywords, max 10

    def remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on title and company."""
        seen = set()
        unique_jobs = []

        for job in jobs:
            key = (job.get('title', '').lower().strip(), job.get('company', '').lower().strip())
            if key not in seen and key[0]:  # Ensure title is not empty
                seen.add(key)
                unique_jobs.append(job)

        return unique_jobs

    def save_to_drive(self, filename: str, data):
        """Save data to Google Drive."""
        if not self.drive_mounted:
            logger.warning("Drive not mounted, cannot save data")
            return

        try:
            filepath = os.path.join(self.Config.OUTPUT_FOLDER, filename)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Data saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save data to Drive: {e}")

    def load_from_drive(self, filename: str):
        """Load data from Google Drive."""
        if not self.drive_mounted:
            return None

        try:
            filepath = os.path.join(self.Config.INPUT_FOLDER, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load data from Drive: {e}")

        return None

async def main():
    """Main function to run the Colab processor."""
    processor = ColabProcessor()

    # Setup environment
    if not processor.setup_colab_environment():
        logger.error("Failed to setup Colab environment")
        return

    logger.info("Colab processor started successfully")

    # Main processing loop
    while True:
        try:
            # Check for new tasks
            task_data = processor.load_from_drive('task.json')
            if task_data:
                task_type = task_data.get('type')

                if task_type == 'job_search':
                    logger.info("Processing job search task")
                    results = await processor.process_job_search(task_data.get('params', {}))
                    processor.save_to_drive('job_search_complete.json', {'status': 'completed', 'results': len(results)})

                elif task_type == 'fit_analysis':
                    logger.info("Processing fit analysis task")
                    jobs = task_data.get('jobs', [])
                    master_resume = task_data.get('master_resume', {})
                    results = processor.analyze_job_fit(jobs, master_resume)
                    processor.save_to_drive('fit_analysis_complete.json', {'status': 'completed'})

                elif task_type == 'resume_generation':
                    logger.info("Processing resume generation task")
                    high_fit_jobs = task_data.get('high_fit_jobs', [])
                    master_resume = task_data.get('master_resume', {})
                    results = processor.generate_resumes(high_fit_jobs, master_resume)
                    processor.save_to_drive('resume_generation_complete.json', {'status': 'completed', 'count': len(results)})

                elif task_type == 'course_suggestions':
                    logger.info("Processing course suggestions task")
                    skill_gaps = task_data.get('skill_gaps', [])
                    results = processor.suggest_courses(skill_gaps)
                    processor.save_to_drive('course_suggestions_complete.json', {'status': 'completed'})

                # Clean up task file
                os.remove(os.path.join(processor.Config.INPUT_FOLDER, 'task.json'))

            # Wait before checking again
            await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error in main processing loop: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())