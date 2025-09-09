import os
import logging
import json
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List
import asyncio
import gmail_tool
import parser_tool
import resume_tool
import audit_tool
import resume_parser
import documents
import job_search
import course_suggestions
import discord_bot
import colab_integration

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for required environment variables
required_vars = [
    'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'DISCORD_BOT_TOKEN',
    'SMTP_USER', 'SMTP_PASS', 'XAI_API_KEY', 'HUGGINGFACE_API_KEY'
]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.warning(f"Missing optional environment variables: {', '.join(missing_vars)}")
    # Don't raise error, allow partial functionality

# Define AgentState
class AgentState(TypedDict):
    messages: List[BaseMessage]
    user_id: str
    job_emails: List[dict]
    api_jobs: List[dict]
    parsed_jobs: List[dict]
    parsed_resume: Dict
    generated_resumes: List[dict]
    audited_resumes: List[dict]
    selected_documents: List[dict]
    sent_emails: List[str]
    discord_notifications: List[str]
    course_suggestions: Dict[str, List[Dict]]
    skill_gaps: List[str]

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

# Node for resume generation (using Colab for processing)
def generate_resumes(state: AgentState) -> AgentState:
    try:
        # Filter high-fit jobs (fit_score >= 90)
        high_fit_jobs = [job for job in state['parsed_jobs'] if job.get('fit_score', 0) >= 90]

        if not high_fit_jobs:
            logger.info("No high-fit jobs found, skipping resume generation")
            state['generated_resumes'] = []
            return state

        # Use Colab for resume generation if available
        if colab_integration.check_colab_status():
            logger.info("Using Colab for resume generation")
            state['generated_resumes'] = asyncio.run(colab_integration.submit_resume_generation_task(
                high_fit_jobs, state['parsed_resume']
            )) or []
        else:
            logger.info("Colab not available, using local resume generation")
            state['generated_resumes'] = resume_tool.generate_resumes_for_jobs(high_fit_jobs)

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

# Node for job search from APIs (using Colab for processing)
def search_api_jobs(state: AgentState) -> AgentState:
    try:
        # Use search parameters from messages or default
        search_params = {'keywords': 'software engineer', 'location': 'remote'}  # Default

        # Extract from messages if available
        if state['messages']:
            last_message = state['messages'][-1]
            if hasattr(last_message, 'content'):
                content = last_message.content
                # Simple parsing for keywords and location
                if 'keywords:' in content:
                    search_params['keywords'] = content.split('keywords:')[1].split()[0]
                if 'location:' in content:
                    search_params['location'] = content.split('location:')[1].split()[0]

        # Check if Colab is available, otherwise fallback to local processing
        if colab_integration.check_colab_status():
            logger.info("Using Colab for job search")
            state['api_jobs'] = asyncio.run(colab_integration.submit_job_search_task(search_params)) or []
        else:
            logger.info("Colab not available, using local job search")
            state['api_jobs'] = asyncio.run(job_search.search_jobs_async(search_params))

        logger.info(f"Searched {len(state['api_jobs'])} jobs from APIs")
    except Exception as e:
        logger.error(f"Error searching API jobs: {e}")
        state['api_jobs'] = []
    return state

# Node for job fit analysis (using Colab for NLP processing)
def analyze_job_fit(state: AgentState) -> AgentState:
    try:
        all_jobs = state['parsed_jobs'] + state['api_jobs']

        # Use Colab for resource-intensive fit analysis if available
        if colab_integration.check_colab_status():
            logger.info("Using Colab for fit analysis")
            analysis_result = asyncio.run(colab_integration.submit_fit_analysis_task(
                all_jobs, state['parsed_resume']
            ))

            if analysis_result:
                high_fit_jobs = analysis_result.get('high_fit_jobs', [])
                low_fit_jobs = analysis_result.get('low_fit_jobs', [])
                state['skill_gaps'] = analysis_result.get('skill_gaps', [])
                state['parsed_jobs'] = high_fit_jobs + low_fit_jobs
            else:
                # Fallback to local processing
                logger.warning("Colab fit analysis failed, using local processing")
                high_fit, low_fit = resume_tool.filter_high_fit_jobs(all_jobs)
                state['parsed_jobs'] = high_fit + low_fit
                state['skill_gaps'] = course_suggestions.analyze_skill_gaps(
                    state['parsed_resume'],
                    [req for job in low_fit for req in job.get('requirements', [])]
                )
        else:
            logger.info("Colab not available, using local fit analysis")
            high_fit, low_fit = resume_tool.filter_high_fit_jobs(all_jobs)
            state['parsed_jobs'] = high_fit + low_fit
            state['skill_gaps'] = course_suggestions.analyze_skill_gaps(
                state['parsed_resume'],
                [req for job in low_fit for req in job.get('requirements', [])]
            )

        logger.info(f"Analyzed fit for {len(all_jobs)} jobs, found {len(state['skill_gaps'])} skill gaps")
    except Exception as e:
        logger.error(f"Error analyzing job fit: {e}")
        state['skill_gaps'] = []
    return state

# Node for course suggestions (using Colab for processing)
def suggest_courses(state: AgentState) -> AgentState:
    try:
        if not state['skill_gaps']:
            logger.info("No skill gaps found, skipping course suggestions")
            state['course_suggestions'] = {}
            return state

        # Use Colab for course suggestions if available
        if colab_integration.check_colab_status():
            logger.info("Using Colab for course suggestions")
            state['course_suggestions'] = asyncio.run(colab_integration.submit_course_suggestions_task(
                state['skill_gaps']
            )) or {}
        else:
            logger.info("Colab not available, using local course suggestions")
            state['course_suggestions'] = asyncio.run(
                course_suggestions.get_course_suggestions(state['skill_gaps'])
            )

        logger.info(f"Generated course suggestions for {len(state['skill_gaps'])} skill gaps")
    except Exception as e:
        logger.error(f"Error generating course suggestions: {e}")
        state['course_suggestions'] = {}
    return state

# Node for Discord notifications
def discord_notifications(state: AgentState) -> AgentState:
    try:
        notifications = []

        # Notify about generated resumes
        for resume in state['generated_resumes']:
            if 'skipped' not in resume:
                notifications.append(f"Resume generated for {resume.get('job_title', 'Unknown')} at {resume.get('company', 'Unknown')}")

        # Notify about course suggestions
        if state['course_suggestions']:
            notifications.append(f"Found course suggestions for {len(state['course_suggestions'])} skill gaps")

        state['discord_notifications'] = notifications
        logger.info(f"Prepared {len(notifications)} Discord notifications")
    except Exception as e:
        logger.error(f"Error preparing Discord notifications: {e}")
        state['discord_notifications'] = []
    return state

# Build the LangGraph workflow
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("scan_gmail", scan_gmail)
workflow.add_node("search_api_jobs", search_api_jobs)
workflow.add_node("parse_jobs", parse_jobs)
workflow.add_node("parse_resume", parse_resume)
workflow.add_node("analyze_job_fit", analyze_job_fit)
workflow.add_node("generate_resumes", generate_resumes)
workflow.add_node("audit_resumes", audit_resumes)
workflow.add_node("select_documents", select_documents)
workflow.add_node("suggest_courses", suggest_courses)
workflow.add_node("send_emails", send_emails)
workflow.add_node("discord_notifications", discord_notifications)

# Add edges
workflow.add_edge(START, "scan_gmail")
workflow.add_edge("scan_gmail", "search_api_jobs")
workflow.add_edge("scan_gmail", "parse_jobs")
workflow.add_edge("search_api_jobs", "parse_jobs")
workflow.add_edge("parse_jobs", "parse_resume")
workflow.add_edge("parse_resume", "analyze_job_fit")
workflow.add_edge("analyze_job_fit", "generate_resumes")
workflow.add_edge("generate_resumes", "audit_resumes")
workflow.add_edge("audit_resumes", "select_documents")
workflow.add_edge("select_documents", "suggest_courses")
workflow.add_edge("suggest_courses", "send_emails")
workflow.add_edge("send_emails", "discord_notifications")
workflow.add_edge("discord_notifications", END)

# Compile the graph
app = workflow.compile()

if __name__ == "__main__":
    # Test the agent workflow
    initial_state = AgentState(
        messages=[],
        user_id="test_user",
        job_emails=[],
        api_jobs=[],
        parsed_jobs=[],
        parsed_resume={},
        generated_resumes=[],
        audited_resumes=[],
        selected_documents=[],
        sent_emails=[],
        discord_notifications=[],
        course_suggestions={},
        skill_gaps=[]
    )
    result = app.invoke(initial_state)
    print("Workflow completed:", result)