#!/usr/bin/env python3
import os
import subprocess
import logging
from dotenv import load_dotenv

# Instructions:
# 1. Ensure GitHub CLI (`gh`) is installed in Codespaces (`gh --version`).
# 2. Set GH_TOKEN in .env file with a GitHub Personal Access Token (scope: repo, project).
# 3. Run in VS Code terminal: `python setup_github_project.py`.
# 4. Commit and push: `git add setup_github_project.py .gitignore .env.example && git commit -m "Add project setup script #1" && git push origin main`.

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_gh_command(command):
    """Execute a GitHub CLI command and handle errors."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {command}\nError: {e.stderr}")
        raise

def create_github_project(repo, project_name):
    """Create a GitHub Projects board."""
    command = f"gh project create --owner {repo.split('/')[0]} --title \"{project_name}\""
    project_number = run_gh_command(command)
    logger.info(f"Created project: {project_name}, Number: {project_number}")
    return project_number.split()[-1]  # Extract project number

def add_columns(project_number, repo, columns):
    """Add columns to the project board."""
    for column_name in columns:
        command = f"gh project field-create {project_number} --owner {repo.split('/')[0]} --name \"{column_name}\" --data-type SINGLE_SELECT --single-select-options \"{column_name}\""
        run_gh_command(command)
        logger.info(f"Added column: {column_name}")

def create_issues(repo, project_number, issues):
    """Create issues and assign to To Do column."""
    for issue in issues:
        title = issue['title']
        command = f"gh issue create --repo {repo} --title \"{title}\" --body \"Auto-generated issue for agent project\" --label \"To Do\""
        issue_number = run_gh_command(command)
        logger.info(f"Created issue: {title}, Number: {issue_number}")
        # Assign to project
        command = f"gh project item-add {project_number} --owner {repo.split('/')[0]} --url {issue_number}"
        run_gh_command(command)
        logger.info(f"Assigned issue {title} to project")

def main():
    """Automate GitHub Projects setup for job_application_agent."""
    load_dotenv()
    github_token = os.getenv('GH_TOKEN')
    if not github_token:
        raise ValueError("GH_TOKEN not found in .env")

    repo = os.getenv('GITHUB_REPOSITORY', 'your-username/job_application_agent')
    project_name = "Agent Development Board"
    columns = ["To Do", "In Progress", "Done"]
    issues = [
        {"title": "Set up project structure and .env for APIs"},
        {"title": "Implement multi-user Gmail OAuth"},
        {"title": "Code Gmail scanning and job parsing with spaCy"},
        {"title": "Generate ATS-optimized resume with python-docx"},
        {"title": "Add email sending with smtplib"},
        {"title": "Integrate Ayoba chatbot with Flask webhook"},
        {"title": "Test full workflow and handle errors (e.g., API limits)"},
        {"title": "Deploy to Heroku and register with Ayoba developer portal"}
    ]

    try:
        # Create project
        project_number = create_github_project(repo, project_name)
        # Add columns
        add_columns(project_number, repo, columns)
        # Create and assign issues
        create_issues(repo, project_number, issues)
        logger.info("GitHub Projects setup complete")
    except Exception as e:
        logger.error(f"Setup failed: {e}")

if __name__ == "__main__":
    main()