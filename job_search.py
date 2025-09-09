import os
import asyncio
import logging
import httpx
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Free-tier API Keys only
ADZUNA_APP_ID = os.getenv('ADZUNA_APP_ID')
ADZUNA_APP_KEY = os.getenv('ADZUNA_APP_KEY')
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')  # Free tier available
CAREERJET_API_KEY = os.getenv('CAREERJET_API_KEY')  # Free public access
UPWORK_CLIENT_ID = os.getenv('UPWORK_CLIENT_ID')  # Free tier
UPWORK_CLIENT_SECRET = os.getenv('UPWORK_CLIENT_SECRET')
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')  # Free tier available

async def search_jobs_async(search_params: Dict) -> List[Dict]:
    """Search jobs from multiple APIs asynchronously."""
    keywords = search_params.get('keywords', '')
    location = search_params.get('location', '')
    max_age_days = search_params.get('max_age_days', 30)
    salary_min = search_params.get('salary_min')
    salary_max = search_params.get('salary_max')

    # List of FREE-TIER API search functions only
    search_functions = [
        search_adzuna,        # Free tier: ~100-250 calls/month
        search_careerjet,     # Free public access
        search_upwork,        # Free tier for basic searches
        search_serapi_google, # Free tier available
        search_rapidapi_jobs  # Free tier available
    ]

    # Run all searches in parallel
    tasks = []
    for func in search_functions:
        task = asyncio.create_task(func(keywords, location, salary_min, salary_max))
        tasks.append(task)

    # Wait for all to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Flatten results and filter out exceptions
    all_jobs = []
    for result in results:
        if isinstance(result, list):
            all_jobs.extend(result)
        elif isinstance(result, Exception):
            logger.error(f"API search failed: {result}")

    # Remove duplicates based on title and company
    unique_jobs = remove_duplicates(all_jobs)

    # Apply location and date filters
    filtered_jobs = apply_filters(unique_jobs, location, max_age_days)

    logger.info(f"Found {len(unique_jobs)} unique jobs, {len(filtered_jobs)} after filtering from {len(search_functions)} APIs")
    return filtered_jobs

def remove_duplicates(jobs: List[Dict]) -> List[Dict]:
    """Remove duplicate jobs based on title and company."""
    seen = set()
    unique_jobs = []

    for job in jobs:
        key = (job.get('title', '').lower(), job.get('company', '').lower())
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs

async def search_adzuna(keywords: str, location: str, salary_min: Optional[int], salary_max: Optional[int]) -> List[Dict]:
    """Search jobs using Adzuna API."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logger.warning("Adzuna API keys not configured")
        return []

    try:
        url = f"https://api.adzuna.com/v1/api/jobs/us/search/1"
        params = {
            'app_id': ADZUNA_APP_ID,
            'app_key': ADZUNA_APP_KEY,
            'what': keywords,
            'where': 'Cape Town, South Africa',
            'distance': 50,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'results_per_page': 10
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            jobs = []
            for result in data.get('results', []):
                job = {
                    'title': result.get('title', ''),
                    'company': result.get('company', {}).get('display_name', ''),
                    'location': result.get('location', {}).get('display_name', ''),
                    'description': result.get('description', ''),
                    'salary': result.get('salary_min', ''),
                    'url': result.get('redirect_url', ''),
                    'requirements': extract_keywords(result.get('description', '')),
                    'source': 'Adzuna'
                }
                jobs.append(job)
            return jobs
        else:
            logger.error(f"Adzuna API error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Adzuna search failed: {e}")
        return []

async def search_indeed(keywords: str, location: str, salary_min: Optional[int], salary_max: Optional[int]) -> List[Dict]:
    """Search jobs using Indeed API."""
    if not INDEED_API_KEY:
        logger.warning("Indeed API key not configured")
        return []

    try:
        url = "https://api.indeed.com/ads/apisearch"
        params = {
            'publisher': INDEED_API_KEY,
            'q': keywords,
            'l': location,
            'limit': 10,
            'format': 'json'
        }

        if salary_min:
            params['salary'] = f"{salary_min}+"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            jobs = []
            for result in data.get('results', []):
                job = {
                    'title': result.get('jobtitle', ''),
                    'company': result.get('company', ''),
                    'location': result.get('formattedLocation', ''),
                    'description': result.get('snippet', ''),
                    'salary': result.get('formattedSalary', ''),
                    'url': result.get('url', ''),
                    'requirements': extract_keywords(result.get('snippet', '')),
                    'source': 'Indeed'
                }
                jobs.append(job)
            return jobs
        else:
            logger.error(f"Indeed API error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Indeed search failed: {e}")
        return []

async def search_google_jobs(keywords: str, location: str, salary_min: Optional[int], salary_max: Optional[int]) -> List[Dict]:
    """Search jobs using Google Cloud Talent Solution."""
    if not GOOGLE_CLOUD_API_KEY:
        logger.warning("Google Cloud API key not configured")
        return []

    try:
        url = f"https://jobs.googleapis.com/v3/projects/job-application-agent/jobs:search"
        headers = {'Authorization': f'Bearer {GOOGLE_CLOUD_API_KEY}'}
        payload = {
            'requestMetadata': {
                'userId': 'user1',
                'sessionId': 'session1'
            },
            'jobQuery': {
                'query': keywords,
                'locationFilters': [{'address': 'Cape Town, South Africa', 'distanceInKm': 50}]
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            jobs = []
            for result in data.get('matchingJobs', []):
                job = result.get('job', {})
                job_data = {
                    'title': job.get('title', ''),
                    'company': job.get('companyName', ''),
                    'location': job.get('addresses', [''])[0],
                    'description': job.get('description', ''),
                    'salary': '',
                    'url': '',
                    'requirements': extract_keywords(job.get('description', '')),
                    'source': 'Google Talent'
                }
                jobs.append(job_data)
            return jobs
        else:
            logger.error(f"Google Talent API error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Google Talent search failed: {e}")
        return []

async def search_serapi_google(keywords: str, location: str, salary_min: Optional[int], salary_max: Optional[int]) -> List[Dict]:
    """Search jobs using SerpApi Google Jobs."""
    if not SERPAPI_API_KEY:
        logger.warning("SerpApi key not configured")
        return []

    try:
        url = "https://serpapi.com/search.json"
        params = {
            'engine': 'google_jobs',
            'q': keywords,
            'location': 'Cape Town, South Africa',
            'radius': 50,
            'api_key': SERPAPI_API_KEY
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            jobs = []
            for result in data.get('jobs_results', []):
                job = {
                    'title': result.get('title', ''),
                    'company': result.get('company_name', ''),
                    'location': result.get('location', ''),
                    'description': result.get('description', ''),
                    'salary': result.get('salary', ''),
                    'url': result.get('related_links', [{}])[0].get('link', ''),
                    'requirements': extract_keywords(result.get('description', '')),
                    'source': 'SerpApi Google'
                }
                jobs.append(job)
            return jobs
        else:
            logger.error(f"SerpApi error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"SerpApi search failed: {e}")
        return []

async def search_theirstack(keywords: str, location: str, salary_min: Optional[int], salary_max: Optional[int]) -> List[Dict]:
    """Search jobs using TheirStack API."""
    if not THEIRSTACK_API_KEY:
        logger.warning("TheirStack API key not configured")
        return []

    try:
        url = "https://api.theirstack.com/v1/jobs/search"
        headers = {'Authorization': f'Bearer {THEIRSTACK_API_KEY}'}
        params = {
            'query': keywords,
            'location': location,
            'limit': 10
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            jobs = []
            for result in data.get('jobs', []):
                job = {
                    'title': result.get('title', ''),
                    'company': result.get('company', ''),
                    'location': result.get('location', ''),
                    'description': result.get('description', ''),
                    'salary': result.get('salary', ''),
                    'url': result.get('url', ''),
                    'requirements': result.get('skills', []),
                    'source': 'TheirStack'
                }
                jobs.append(job)
            return jobs
        else:
            logger.error(f"TheirStack API error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"TheirStack search failed: {e}")
        return []

async def search_coresignal(keywords: str, location: str, salary_min: Optional[int], salary_max: Optional[int]) -> List[Dict]:
    """Search jobs using Coresignal Jobs API."""
    if not CORESIGNAL_API_KEY:
        logger.warning("Coresignal API key not configured")
        return []

    try:
        url = "https://api.coresignal.com/v1/jobs/search"
        headers = {'Authorization': f'Bearer {CORESIGNAL_API_KEY}'}
        payload = {
            'query': keywords,
            'location': location,
            'limit': 10
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            jobs = []
            for result in data.get('jobs', []):
                job = {
                    'title': result.get('title', ''),
                    'company': result.get('company', ''),
                    'location': result.get('location', ''),
                    'description': result.get('description', ''),
                    'salary': result.get('salary', ''),
                    'url': result.get('url', ''),
                    'requirements': result.get('requirements', []),
                    'source': 'Coresignal'
                }
                jobs.append(job)
            return jobs
        else:
            logger.error(f"Coresignal API error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Coresignal search failed: {e}")
        return []

async def search_careerjet(keywords: str, location: str, salary_min: Optional[int], salary_max: Optional[int]) -> List[Dict]:
    """Search jobs using Careerjet API."""
    if not CAREERJET_API_KEY:
        logger.warning("Careerjet API key not configured")
        return []

    try:
        url = "https://public-api.careerjet.net/search"
        params = {
            'keywords': keywords,
            'location': 'Cape Town, South Africa',
            'radius': 50,
            'affid': CAREERJET_API_KEY,
            'pagesize': 10
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            jobs = []
            for result in data.get('jobs', []):
                job = {
                    'title': result.get('title', ''),
                    'company': result.get('company', ''),
                    'location': result.get('locations', ''),
                    'description': result.get('description', ''),
                    'salary': result.get('salary', ''),
                    'url': result.get('url', ''),
                    'requirements': extract_keywords(result.get('description', '')),
                    'source': 'Careerjet'
                }
                jobs.append(job)
            return jobs
        else:
            logger.error(f"Careerjet API error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Careerjet search failed: {e}")
        return []

async def search_upwork(keywords: str, location: str, salary_min: Optional[int], salary_max: Optional[int]) -> List[Dict]:
    """Search jobs using Upwork API."""
    if not UPWORK_CLIENT_ID or not UPWORK_CLIENT_SECRET:
        logger.warning("Upwork credentials not configured")
        return []

    try:
        # First get access token
        auth_url = "https://www.upwork.com/api/v3/oauth2/token"
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': UPWORK_CLIENT_ID,
            'client_secret': UPWORK_CLIENT_SECRET
        }

        async with httpx.AsyncClient() as client:
            auth_response = await client.post(auth_url, data=auth_data, timeout=10)

        if auth_response.status_code != 200:
            logger.error(f"Upwork auth failed: {auth_response.status_code}")
            return []

        token = auth_response.json().get('access_token')

        # Search jobs
        search_url = "https://www.upwork.com/api/v3/jobs/search"
        headers = {'Authorization': f'Bearer {token}'}
        params = {
            'q': keywords,
            'location': 'Cape Town, South Africa',
            'radius': 50,
            'limit': 10
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            jobs = []
            for result in data.get('jobs', []):
                job = {
                    'title': result.get('title', ''),
                    'company': result.get('client', {}).get('name', ''),
                    'location': result.get('location', ''),
                    'description': result.get('description', ''),
                    'salary': result.get('budget', ''),
                    'url': result.get('url', ''),
                    'requirements': result.get('skills', []),
                    'source': 'Upwork'
                }
                jobs.append(job)
            return jobs
        else:
            logger.error(f"Upwork API error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Upwork search failed: {e}")
        return []

async def search_rapidapi_jobs(keywords: str, location: str, salary_min: Optional[int], salary_max: Optional[int]) -> List[Dict]:
    """Search jobs using RapidAPI Job Search."""
    if not RAPIDAPI_KEY:
        logger.warning("RapidAPI key not configured")
        return []

    try:
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            'X-RapidAPI-Key': RAPIDAPI_KEY,
            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
        }
        params = {
            'query': f"{keywords} in Cape Town, South Africa",
            'radius': 50,
            'num_pages': 1
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            jobs = []
            for result in data.get('data', []):
                job = {
                    'title': result.get('job_title', ''),
                    'company': result.get('employer_name', ''),
                    'location': result.get('job_city', ''),
                    'description': result.get('job_description', ''),
                    'salary': result.get('job_salary', ''),
                    'url': result.get('job_apply_link', ''),
                    'requirements': result.get('job_required_skills', []),
                    'source': 'RapidAPI'
                }
                jobs.append(job)
            return jobs
        else:
            logger.error(f"RapidAPI error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"RapidAPI search failed: {e}")
        return []

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from job description."""
    if not text:
        return []

    # Simple keyword extraction (can be enhanced with NLP)
    words = text.lower().split()
    keywords = []

    # Common tech skills
    tech_skills = ['python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker', 'kubernetes',
                   'machine learning', 'ai', 'data science', 'devops', 'agile', 'scrum']

    for word in words:
        word = word.strip('.,!?()[]{}')
        if word in tech_skills and word not in keywords:
            keywords.append(word)

    return keywords

def apply_filters(jobs: List[Dict], location: str, max_age_days: int) -> List[Dict]:
    """Apply location and date filters to jobs."""
    # For now, just return jobs as filters are applied in individual searches
    return jobs