"""
Colab Integration Module for VS Code
Handles communication between VS Code agent and Google Colab processor
for offloading resource-intensive tasks.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from pathlib import Path

# Google Drive integration
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ColabIntegration:
    def __init__(self):
        self.drive_service = None
        self.shared_folder_id = None
        self.input_folder_id = None
        self.output_folder_id = None
        self.setup_google_drive()

    def setup_google_drive(self):
        """Set up Google Drive API connection."""
        if not GOOGLE_DRIVE_AVAILABLE:
            logger.warning("Google Drive libraries not available")
            return

        try:
            creds = self.get_credentials()
            if creds:
                self.drive_service = build('drive', 'v3', credentials=creds)
                self.setup_shared_folder()
                logger.info("Google Drive integration setup successfully")
            else:
                logger.error("Failed to get Google Drive credentials")
        except Exception as e:
            logger.error(f"Failed to setup Google Drive: {e}")

    def get_credentials(self):
        """Get Google Drive API credentials."""
        try:
            creds = None
            token_path = Path.home() / '.colab_integration' / 'token.json'
            credentials_path = Path('credentials.json')

            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path))

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not credentials_path.exists():
                        logger.error("credentials.json not found")
                        return None

                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_path),
                        ['https://www.googleapis.com/auth/drive.file']
                    )
                    creds = flow.run_local_server(port=0)

                # Save credentials
                token_path.parent.mkdir(exist_ok=True)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            return creds
        except Exception as e:
            logger.error(f"Failed to get credentials: {e}")
            return None

    def setup_shared_folder(self):
        """Set up or find the shared JobAgent folder in Google Drive."""
        try:
            # Check if JobAgent folder exists
            query = "name='JobAgent' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])

            if items:
                self.shared_folder_id = items[0]['id']
                logger.info(f"Found existing JobAgent folder: {self.shared_folder_id}")
            else:
                # Create JobAgent folder
                folder_metadata = {
                    'name': 'JobAgent',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.drive_service.files().create(
                    body=folder_metadata, fields='id'
                ).execute()
                self.shared_folder_id = folder.get('id')
                logger.info(f"Created JobAgent folder: {self.shared_folder_id}")

            # Setup input and output folders
            self.setup_subfolders()

        except Exception as e:
            logger.error(f"Failed to setup shared folder: {e}")

    def setup_subfolders(self):
        """Set up input and output subfolders."""
        try:
            # Input folder
            query = f"name='input' and '{self.shared_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])

            if items:
                self.input_folder_id = items[0]['id']
            else:
                folder_metadata = {
                    'name': 'input',
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.shared_folder_id]
                }
                folder = self.drive_service.files().create(
                    body=folder_metadata, fields='id'
                ).execute()
                self.input_folder_id = folder.get('id')

            # Output folder
            query = f"name='output' and '{self.shared_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])

            if items:
                self.output_folder_id = items[0]['id']
            else:
                folder_metadata = {
                    'name': 'output',
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.shared_folder_id]
                }
                folder = self.drive_service.files().create(
                    body=folder_metadata, fields='id'
                ).execute()
                self.output_folder_id = folder.get('id')

            logger.info("Input and output folders setup successfully")

        except Exception as e:
            logger.error(f"Failed to setup subfolders: {e}")

    def upload_file(self, local_path: str, drive_filename: str, folder_id: str) -> Optional[str]:
        """Upload a file to Google Drive."""
        if not self.drive_service:
            return None

        try:
            file_metadata = {
                'name': drive_filename,
                'parents': [folder_id]
            }

            media = MediaFileUpload(local_path, resumable=True)
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            logger.info(f"Uploaded {drive_filename} to Drive")
            return file.get('id')
        except Exception as e:
            logger.error(f"Failed to upload file {drive_filename}: {e}")
            return None

    def download_file(self, file_id: str, local_path: str) -> bool:
        """Download a file from Google Drive."""
        if not self.drive_service:
            return False

        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            with open(local_path, 'wb') as f:
                f.write(request.execute())
            logger.info(f"Downloaded file to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {e}")
            return False

    def list_files(self, folder_id: str, filename: str = None) -> List[Dict]:
        """List files in a Drive folder."""
        if not self.drive_service:
            return []

        try:
            query = f"'{folder_id}' in parents and trashed=false"
            if filename:
                query += f" and name='{filename}'"

            results = self.drive_service.files().list(
                q=query,
                fields='files(id, name, modifiedTime)'
            ).execute()

            return results.get('files', [])
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []

    def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive."""
        if not self.drive_service:
            return False

        try:
            self.drive_service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted file {file_id} from Drive")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False

    async def submit_task(self, task_type: str, task_data: Dict, timeout_minutes: int = 30) -> Optional[Dict]:
        """Submit a task to Colab processor and wait for results."""
        if not self.drive_service or not self.input_folder_id:
            logger.error("Google Drive not properly configured")
            return None

        try:
            # Create task file
            task_payload = {
                'type': task_type,
                'timestamp': datetime.now().isoformat(),
                'data': task_data
            }

            # Save task to local temp file
            task_filename = f"task_{int(time.time())}.json"
            local_task_path = f"/tmp/{task_filename}"

            with open(local_task_path, 'w') as f:
                json.dump(task_payload, f, indent=2)

            # Upload task to Drive
            task_file_id = self.upload_file(local_task_path, 'task.json', self.input_folder_id)
            if not task_file_id:
                return None

            # Wait for completion
            result = await self.wait_for_completion(task_type, timeout_minutes)

            # Clean up task file
            self.delete_file(task_file_id)
            os.remove(local_task_path)

            return result

        except Exception as e:
            logger.error(f"Failed to submit task {task_type}: {e}")
            return None

    async def wait_for_completion(self, task_type: str, timeout_minutes: int) -> Optional[Dict]:
        """Wait for Colab processor to complete the task."""
        timeout_time = datetime.now() + timedelta(minutes=timeout_minutes)
        completion_filename = f"{task_type}_complete.json"

        while datetime.now() < timeout_time:
            try:
                # Check for completion file
                files = self.list_files(self.output_folder_id, completion_filename)
                if files:
                    # Download result
                    local_result_path = f"/tmp/{completion_filename}"
                    if self.download_file(files[0]['id'], local_result_path):
                        with open(local_result_path, 'r') as f:
                            result = json.load(f)

                        # Clean up
                        self.delete_file(files[0]['id'])
                        os.remove(local_result_path)

                        return result

                # Wait before checking again
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Error checking for completion: {e}")
                await asyncio.sleep(10)

        logger.warning(f"Timeout waiting for {task_type} completion")
        return None

    async def submit_job_search(self, search_params: Dict) -> Optional[List[Dict]]:
        """Submit job search task to Colab."""
        result = await self.submit_task('job_search', {'params': search_params})

        if result and result.get('status') == 'completed':
            # Download job search results
            files = self.list_files(self.output_folder_id, 'job_search_results.json')
            if files:
                local_path = f"/tmp/job_search_results.json"
                if self.download_file(files[0]['id'], local_path):
                    with open(local_path, 'r') as f:
                        jobs = json.load(f)

                    # Clean up
                    self.delete_file(files[0]['id'])
                    os.remove(local_path)

                    return jobs

        return None

    async def submit_fit_analysis(self, jobs: List[Dict], master_resume: Dict) -> Optional[Dict]:
        """Submit fit analysis task to Colab."""
        task_data = {
            'jobs': jobs,
            'master_resume': master_resume
        }

        result = await self.submit_task('fit_analysis', task_data)

        if result and result.get('status') == 'completed':
            # Download fit analysis results
            files = self.list_files(self.output_folder_id, 'fit_analysis_results.json')
            if files:
                local_path = f"/tmp/fit_analysis_results.json"
                if self.download_file(files[0]['id'], local_path):
                    with open(local_path, 'r') as f:
                        analysis = json.load(f)

                    # Clean up
                    self.delete_file(files[0]['id'])
                    os.remove(local_path)

                    return analysis

        return None

    async def submit_resume_generation(self, high_fit_jobs: List[Dict], master_resume: Dict) -> Optional[List[Dict]]:
        """Submit resume generation task to Colab."""
        task_data = {
            'high_fit_jobs': high_fit_jobs,
            'master_resume': master_resume
        }

        result = await self.submit_task('resume_generation', task_data)

        if result and result.get('status') == 'completed':
            # Download generated resumes
            files = self.list_files(self.output_folder_id, 'generated_resumes.json')
            if files:
                local_path = f"/tmp/generated_resumes.json"
                if self.download_file(files[0]['id'], local_path):
                    with open(local_path, 'r') as f:
                        resumes = json.load(f)

                    # Clean up
                    self.delete_file(files[0]['id'])
                    os.remove(local_path)

                    return resumes

        return None

    async def submit_course_suggestions(self, skill_gaps: List[str]) -> Optional[Dict[str, List[Dict]]]:
        """Submit course suggestions task to Colab."""
        result = await self.submit_task('course_suggestions', {'skill_gaps': skill_gaps})

        if result and result.get('status') == 'completed':
            # Download course suggestions
            files = self.list_files(self.output_folder_id, 'course_suggestions.json')
            if files:
                local_path = f"/tmp/course_suggestions.json"
                if self.download_file(files[0]['id'], local_path):
                    with open(local_path, 'r') as f:
                        suggestions = json.load(f)

                    # Clean up
                    self.delete_file(files[0]['id'])
                    os.remove(local_path)

                    return suggestions

        return None

    def get_status(self) -> Optional[Dict]:
        """Get current Colab processor status."""
        if not self.drive_service or not self.shared_folder_id:
            return None

        try:
            files = self.list_files(self.shared_folder_id, 'status.json')
            if files:
                local_path = f"/tmp/status.json"
                if self.download_file(files[0]['id'], local_path):
                    with open(local_path, 'r') as f:
                        status = json.load(f)

                    os.remove(local_path)
                    return status
        except Exception as e:
            logger.error(f"Failed to get status: {e}")

        return None

    def is_colab_available(self) -> bool:
        """Check if Colab processor is available and responding."""
        status = self.get_status()
        if status:
            # Check if status is recent (within last 5 minutes)
            status_time = datetime.fromisoformat(status.get('timestamp', ''))
            time_diff = datetime.now() - status_time
            return time_diff.total_seconds() < 300  # 5 minutes

        return False

# Global instance
colab_integration = ColabIntegration()

async def submit_job_search_task(search_params: Dict) -> Optional[List[Dict]]:
    """Convenience function to submit job search task."""
    return await colab_integration.submit_job_search(search_params)

async def submit_fit_analysis_task(jobs: List[Dict], master_resume: Dict) -> Optional[Dict]:
    """Convenience function to submit fit analysis task."""
    return await colab_integration.submit_fit_analysis(jobs, master_resume)

async def submit_resume_generation_task(high_fit_jobs: List[Dict], master_resume: Dict) -> Optional[List[Dict]]:
    """Convenience function to submit resume generation task."""
    return await colab_integration.submit_resume_generation(high_fit_jobs, master_resume)

async def submit_course_suggestions_task(skill_gaps: List[str]) -> Optional[Dict[str, List[Dict]]]:
    """Convenience function to submit course suggestions task."""
    return await colab_integration.submit_course_suggestions(skill_gaps)

def check_colab_status() -> bool:
    """Check if Colab processor is available."""
    return colab_integration.is_colab_available()

def get_colab_status() -> Optional[Dict]:
    """Get Colab processor status."""
    return colab_integration.get_status()