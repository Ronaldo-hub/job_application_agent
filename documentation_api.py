"""
Documentation API Module for Job Application Agent
Handles automatic documentation generation and conversation logging
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Keys for documentation services
GITHUB_TOKEN = os.getenv('GH_TOKEN')
README_API_KEY = os.getenv('README_API_KEY')  # For ReadMe.com API
GITBOOK_API_KEY = os.getenv('GITBOOK_API_KEY')  # For GitBook API
NOTION_API_KEY = os.getenv('NOTION_API_KEY')  # For Notion API

class DocumentationAPI:
    """Handles automatic documentation generation and publishing"""

    def __init__(self):
        self.conversation_log = "conversation_log.md"
        self.project_docs = "docs/"
        self.setup_documentation_structure()

    def setup_documentation_structure(self):
        """Create documentation directory structure"""
        try:
            os.makedirs(self.project_docs, exist_ok=True)
            os.makedirs(f"{self.project_docs}/api", exist_ok=True)
            os.makedirs(f"{self.project_docs}/workflows", exist_ok=True)
            os.makedirs(f"{self.project_docs}/performance", exist_ok=True)
            logger.info("Documentation structure created")
        except Exception as e:
            logger.error(f"Failed to create documentation structure: {e}")

    def generate_api_documentation(self) -> str:
        """Generate API documentation from code analysis"""
        try:
            api_doc = "# Job Application Agent API Documentation\n\n"
            api_doc += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            # Document main APIs used
            api_doc += "## External APIs Integrated\n\n"
            api_doc += "### Job Search APIs\n"
            api_doc += "- **SerpApi Google Jobs**: Active and configured\n"
            api_doc += "- **RapidAPI JSearch**: Active and configured\n"
            api_doc += "- **Adzuna**: Not configured (placeholder)\n"
            api_doc += "- **Careerjet**: Not configured (placeholder)\n"
            api_doc += "- **Upwork**: Not configured (placeholder)\n\n"

            api_doc += "### AI/ML APIs\n"
            api_doc += "- **Hugging Face**: Active (Llama 3.1 8B-Instruct)\n"
            api_doc += "- **spaCy**: Active (en_core_web_sm model)\n"
            api_doc += "- **scikit-learn**: Active (TF-IDF, cosine similarity)\n\n"

            api_doc += "### Communication APIs\n"
            api_doc += "- **Gmail API**: Partially configured (OAuth needed)\n"
            api_doc += "- **Discord API**: Configured (bot token available)\n"
            api_doc += "- **SMTP**: Configured (email credentials available)\n\n"

            # Save API documentation
            api_file = f"{self.project_docs}/api/external_apis.md"
            with open(api_file, 'w', encoding='utf-8') as f:
                f.write(api_doc)

            logger.info(f"API documentation generated: {api_file}")
            return api_file

        except Exception as e:
            logger.error(f"Failed to generate API documentation: {e}")
            return ""

    def generate_performance_report(self) -> str:
        """Generate performance analysis documentation"""
        try:
            perf_doc = "# Performance Analysis Report\n\n"
            perf_doc += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            perf_doc += "## Overall Performance Metrics\n\n"
            perf_doc += "| Component | Success Rate | Status |\n"
            perf_doc += "|-----------|-------------|---------|\n"
            perf_doc += "| Gmail Integration | 0% | ❌ Critical Failure |\n"
            perf_doc += "| API Job Search | 40% | ⚠️ Partial Success |\n"
            perf_doc += "| Job Parsing | 0% | ❌ Critical Failure |\n"
            perf_doc += "| Resume Processing | 100% | ✅ Full Success |\n"
            perf_doc += "| Fit Analysis | 50% | ⚠️ Partial Success |\n"
            perf_doc += "| Resume Generation | 0% | ❌ Critical Failure |\n"
            perf_doc += "| Course Suggestions | 100% | ✅ Full Success |\n"
            perf_doc += "| Email Sending | 0% | ❌ Not Implemented |\n"
            perf_doc += "| Notifications | 0% | ❌ Critical Failure |\n\n"

            perf_doc += "## Root Causes\n\n"
            perf_doc += "1. **Gmail OAuth Configuration**: No credentials stored for test user\n"
            perf_doc += "2. **API Key Gaps**: 60% of job search APIs not configured\n"
            perf_doc += "3. **Missing Features**: Email sending functionality incomplete\n"
            perf_doc += "4. **Error Handling**: Limited fallback mechanisms\n\n"

            perf_doc += "## Recommendations\n\n"
            perf_doc += "1. Complete OAuth setup for Gmail integration\n"
            perf_doc += "2. Configure remaining job search APIs\n"
            perf_doc += "3. Implement email sending (Issue #5)\n"
            perf_doc += "4. Add comprehensive error handling\n"
            perf_doc += "5. Create unit tests for all components\n\n"

            # Save performance report
            perf_file = f"{self.project_docs}/performance/analysis.md"
            with open(perf_file, 'w', encoding='utf-8') as f:
                f.write(perf_doc)

            logger.info(f"Performance report generated: {perf_file}")
            return perf_file

        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return ""

    def generate_workflow_documentation(self) -> str:
        """Generate workflow documentation"""
        try:
            workflow_doc = "# Job Application Agent Workflow\n\n"
            workflow_doc += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            workflow_doc += "## LangGraph Workflow Overview\n\n"
            workflow_doc += "```\n"
            workflow_doc += "START → scan_gmail → search_api_jobs → parse_jobs\n"
            workflow_doc += "                        ↓                    ↓\n"
            workflow_doc += "                 parse_resume ← analyze_job_fit\n"
            workflow_doc += "                        ↓\n"
            workflow_doc += "                 generate_resumes → audit_resumes\n"
            workflow_doc += "                        ↓\n"
            workflow_doc += "                 select_documents → suggest_courses\n"
            workflow_doc += "                        ↓\n"
            workflow_doc += "                 send_emails → discord_notifications → END\n"
            workflow_doc += "```\n\n"

            workflow_doc += "## Node Descriptions\n\n"
            workflow_doc += "### 1. scan_gmail\n"
            workflow_doc += "- **Purpose**: Scan Gmail for job-related emails using OAuth\n"
            workflow_doc += "- **Status**: ❌ Failed (OAuth not configured)\n"
            workflow_doc += "- **Output**: job_emails list\n\n"

            workflow_doc += "### 2. search_api_jobs\n"
            workflow_doc += "- **Purpose**: Search multiple job APIs for opportunities\n"
            workflow_doc += "- **Status**: ⚠️ Partial (40% APIs configured)\n"
            workflow_doc += "- **Output**: api_jobs list\n\n"

            workflow_doc += "### 3. parse_jobs\n"
            workflow_doc += "- **Purpose**: Parse job emails using spaCy NLP\n"
            workflow_doc += "- **Status**: ❌ Failed (no emails to parse)\n"
            workflow_doc += "- **Output**: parsed_jobs list\n\n"

            workflow_doc += "### 4. parse_resume\n"
            workflow_doc += "- **Purpose**: Load and parse master resume\n"
            workflow_doc += "- **Status**: ✅ Success\n"
            workflow_doc += "- **Output**: parsed_resume dict\n\n"

            workflow_doc += "### 5. analyze_job_fit\n"
            workflow_doc += "- **Purpose**: Calculate fit scores using TF-IDF\n"
            workflow_doc += "- **Status**: ⚠️ Partial (limited job data)\n"
            workflow_doc += "- **Output**: skill_gaps list\n\n"

            workflow_doc += "### 6. generate_resumes\n"
            workflow_doc += "- **Purpose**: Generate ATS-optimized resumes\n"
            workflow_doc += "- **Status**: ❌ Failed (no high-fit jobs)\n"
            workflow_doc += "- **Output**: generated_resumes list\n\n"

            workflow_doc += "### 7. audit_resumes\n"
            workflow_doc += "- **Purpose**: Audit resumes using Llama 3.1 8B\n"
            workflow_doc += "- **Status**: ❌ Failed (no resumes to audit)\n"
            workflow_doc += "- **Output**: audited_resumes list\n\n"

            workflow_doc += "### 8. suggest_courses\n"
            workflow_doc += "- **Purpose**: Generate course recommendations\n"
            workflow_doc += "- **Status**: ✅ Success\n"
            workflow_doc += "- **Output**: course_suggestions dict\n\n"

            workflow_doc += "### 9. send_emails\n"
            workflow_doc += "- **Purpose**: Send resumes via SMTP\n"
            workflow_doc += "- **Status**: ❌ Not implemented (Issue #5)\n"
            workflow_doc += "- **Output**: sent_emails list\n\n"

            workflow_doc += "### 10. discord_notifications\n"
            workflow_doc += "- **Purpose**: Send Discord notifications\n"
            workflow_doc += "- **Status**: ❌ Failed (no content to notify)\n"
            workflow_doc += "- **Output**: discord_notifications list\n\n"

            # Save workflow documentation
            workflow_file = f"{self.project_docs}/workflows/langgraph_flow.md"
            with open(workflow_file, 'w', encoding='utf-8') as f:
                f.write(workflow_doc)

            logger.info(f"Workflow documentation generated: {workflow_file}")
            return workflow_file

        except Exception as e:
            logger.error(f"Failed to generate workflow documentation: {e}")
            return ""

    def publish_to_github_wiki(self, content: str, title: str) -> bool:
        """Publish documentation to GitHub Wiki (if configured)"""
        if not GITHUB_TOKEN:
            logger.warning("GitHub token not configured for wiki publishing")
            return False

        try:
            # GitHub Wiki API implementation would go here
            logger.info(f"GitHub Wiki publishing not yet implemented for: {title}")
            return False
        except Exception as e:
            logger.error(f"Failed to publish to GitHub Wiki: {e}")
            return False

    def generate_all_documentation(self) -> Dict[str, str]:
        """Generate all documentation automatically"""
        logger.info("Starting automatic documentation generation")

        results = {
            "api_docs": self.generate_api_documentation(),
            "performance_report": self.generate_performance_report(),
            "workflow_docs": self.generate_workflow_documentation()
        }

        # Log documentation generation
        log_entry = f"Automatic documentation generated: {len([r for r in results.values() if r])} files created"
        log_conversation_entry("Documentation Generation", log_entry, f"Files: {', '.join([r for r in results.values() if r])}")

        logger.info("Documentation generation completed")
        return results

# Global instance
docs_api = DocumentationAPI()

def log_conversation_entry(entry_type: str, content: str, details: Optional[str] = None):
    """Log conversation entries to conversation log"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"\n## {entry_type} - {timestamp}\n"
        log_entry += f"**Content**: {content}\n"

        if details:
            log_entry += f"**Details**: {details}\n"

        log_entry += "---\n"

        with open("conversation_log.md", 'a', encoding='utf-8') as f:
            f.write(log_entry)

    except Exception as e:
        logger.error(f"Failed to log conversation: {e}")

if __name__ == "__main__":
    # Generate all documentation when run directly
    docs_api.generate_all_documentation()