import os
import logging
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List
import gmail_tool
import parser_tool
import resume_tool
import audit_tool
import resume_parser
import documents

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for required environment variables
required_vars = [
    'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'AYOBA_API_TOKEN',
    'SMTP_USER', 'SMTP_PASS', 'XAI_API_KEY', 'HUGGINGFACE_API_KEY'
]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Define AgentState
class AgentState(TypedDict):
    messages: List[BaseMessage]
    user_id: str
    job_emails: List[dict]
    parsed_jobs: List[dict]
    parsed_resume: Dict
    generated_resumes: List[dict]
    audited_resumes: List[dict]
    selected_documents: List[dict]
    sent_emails: List[str]
    ayoba_responses: List[str]

# Node for Gmail scanning with OAuth integration (Issue #2)
def scan_gmail(state: AgentState) -> AgentState:
    try:
        creds = gmail_tool.get_credentials(state['user_id'])
        state['job_emails'] = gmail_tool.scan_emails(creds)
        logger.info(f"Scanned emails for user {state['user_id']}: {len(state['job_emails'])} found")
    except Exception as e:
        logger.error(f"Error scanning Gmail for user {state['user_id']}: {e}")
        state['job_emails'] = []
    return state

# Node for job parsing using spaCy (Issue #3)
def parse_jobs(state: AgentState) -> AgentState:
    try:
        state['parsed_jobs'] = parser_tool.parse_job_emails(state['job_emails'])
        logger.info(f"Parsed {len(state['parsed_jobs'])} jobs from emails")
    except Exception as e:
        logger.error(f"Error parsing jobs: {e}")
        state['parsed_jobs'] = []
    return state

# Node for resume generation using Grok 3 (Issue #4)
def generate_resumes(state: AgentState) -> AgentState:
    try:
        state['generated_resumes'] = resume_tool.generate_resumes_for_jobs(state['parsed_jobs'])
        logger.info(f"Generated {len(state['generated_resumes'])} resumes")
    except Exception as e:
        logger.error(f"Error generating resumes: {e}")
        state['generated_resumes'] = []
    return state

# Node for resume auditing using Llama 3.1 8B
def audit_resumes(state: AgentState) -> AgentState:
    try:
        state['audited_resumes'] = audit_tool.audit_resumes(state['generated_resumes'])
        logger.info(f"Audited {len(state['audited_resumes'])} resumes")
    except Exception as e:
        logger.error(f"Error auditing resumes: {e}")
        state['audited_resumes'] = []
    return state

# Node for parsing uploaded resume (Issue #4)
def parse_resume(state: AgentState) -> AgentState:
    try:
        # This would typically parse an uploaded resume file
        # For now, load the master resume as placeholder
        with open('master_resume.json', 'r') as f:
            state['parsed_resume'] = json.load(f)
        logger.info("Parsed master resume")
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        state['parsed_resume'] = {}
    return state

# Node for selecting job-relevant documents (Issue #4)
def select_documents(state: AgentState) -> AgentState:
    try:
        # Select documents relevant to the first parsed job
        if state['parsed_jobs']:
            job_details = state['parsed_jobs'][0]  # Use first job for selection
            state['selected_documents'] = documents.select_relevant_documents(job_details)
            logger.info(f"Selected {len(state['selected_documents'])} relevant documents")
        else:
            state['selected_documents'] = []
    except Exception as e:
        logger.error(f"Error selecting documents: {e}")
        state['selected_documents'] = []
    return state

# Placeholder node for email sending (Issue #5)
def send_emails(state: AgentState) -> AgentState:
    # TODO: Send resumes via smtplib
    # Issue #5: Implement email sending functionality
    state['sent_emails'] = []  # Placeholder
    return state

# Placeholder node for Ayoba integration (Issue #6)
def ayoba_integration(state: AgentState) -> AgentState:
    # TODO: Integrate with Ayoba chatbot API for responses
    # Issue #6: Add Ayoba API integration
    state['ayoba_responses'] = []  # Placeholder
    return state

# Build the LangGraph workflow
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("scan_gmail", scan_gmail)
workflow.add_node("parse_jobs", parse_jobs)
workflow.add_node("parse_resume", parse_resume)
workflow.add_node("generate_resumes", generate_resumes)
workflow.add_node("audit_resumes", audit_resumes)
workflow.add_node("select_documents", select_documents)
workflow.add_node("send_emails", send_emails)
workflow.add_node("ayoba_integration", ayoba_integration)

# Add edges
workflow.add_edge(START, "scan_gmail")
workflow.add_edge("scan_gmail", "parse_jobs")
workflow.add_edge("parse_jobs", "parse_resume")
workflow.add_edge("parse_resume", "generate_resumes")
workflow.add_edge("generate_resumes", "audit_resumes")
workflow.add_edge("audit_resumes", "select_documents")
workflow.add_edge("select_documents", "send_emails")
workflow.add_edge("send_emails", "ayoba_integration")
workflow.add_edge("ayoba_integration", END)

# Compile the graph
app = workflow.compile()

if __name__ == "__main__":
    # Test the agent workflow
    initial_state = AgentState(
        messages=[],
        user_id="test_user",
        job_emails=[],
        parsed_jobs=[],
        parsed_resume={},
        generated_resumes=[],
        audited_resumes=[],
        selected_documents=[],
        sent_emails=[],
        ayoba_responses=[]
    )
    result = app.invoke(initial_state)
    print("Workflow completed:", result)