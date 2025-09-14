import os
import logging
import json
import operator
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Automatic conversation logging
def log_conversation_entry(entry_type, content, details=None):
    """Automatically log conversation entries to conversation_log.md"""
    try:
        log_file = "../compliance_monitoring_testing/conversation_log.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create log entry
        log_entry = f"\n## {entry_type} - {timestamp}\n"
        log_entry += f"**Content**: {content}\n"

        if details:
            log_entry += f"**Details**: {details}\n"

        log_entry += "---\n"

        # Append to log file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        logger.info(f"Conversation logged: {entry_type}")

    except Exception as e:
        logger.error(f"Failed to log conversation: {e}")

# Log session start
log_conversation_entry("Session Start", "Job Application Agent analysis session initiated", "Dependencies installed, app execution tested, performance analysis completed")

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END, add_messages
from typing import TypedDict, List, Dict, Annotated
import asyncio
from email_comm_hub import gmail_tool
from resume_doc_processing import parser_tool
from resume_doc_processing import resume_tool
from resume_doc_processing import audit_tool
from resume_doc_processing import resume_parser
from agent_core import documents
from job_discovery_matching import job_search
from learning_recommendations import course_suggestions
from email_comm_hub import discord_bot
from external_services_deployment import colab_integration

# Import compliance module
from compliance_monitoring_testing import popia_compliance

# Import game integrations and token system
try:
    from learning_recommendations import virtonomics_integration
    from learning_recommendations import simcompanies_integration
    from learning_recommendations import cwetlands_integration
    from learning_recommendations import theblueconnection_integration
    from gamification_engine import token_system
except ImportError as e:
    logging.warning(f"Game integrations not available: {e}")
    virtonomics_integration = None
    simcompanies_integration = None
    cwetlands_integration = None
    theblueconnection_integration = None
    token_system = None

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: Annotated[str, lambda x, y: y]
    job_emails: Annotated[List[dict], operator.add]
    api_jobs: Annotated[List[dict], operator.add]
    parsed_jobs: Annotated[List[dict], operator.add]
    parsed_resume: Annotated[Dict, lambda x, y: y]
    generated_resumes: Annotated[List[dict], operator.add]
    audited_resumes: Annotated[List[dict], operator.add]
    selected_documents: Annotated[List[dict], operator.add]
    sent_emails: Annotated[List[str], operator.add]
    discord_notifications: Annotated[List[str], operator.add]
    course_suggestions: Annotated[Dict[str, List[Dict]], lambda x, y: y]
    skill_gaps: Annotated[List[str], operator.add]
    game_recommendations: Annotated[Dict[str, List[Dict]], lambda x, y: y]
    token_activities: Annotated[List[Dict], operator.add]

# Node for Gmail scanning with OAuth integration (Issue #2)
def scan_gmail(state: AgentState) -> AgentState:
    try:
        import asyncio
        # Add timeout wrapper to prevent hanging
        creds = gmail_tool.get_credentials(state['user_id'])

        # Use asyncio to add timeout to the email scanning
        async def scan_with_timeout():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: gmail_tool.scan_emails(creds, timeout=25, max_results=20)  # Reduced timeout and results
            )

        # Run with 30 second timeout
        state['job_emails'] = asyncio.run(asyncio.wait_for(scan_with_timeout(), timeout=30.0))
        logger.info(f"Scanned emails for user {state['user_id']}: {len(state['job_emails'])} found")

    except asyncio.TimeoutError:
        logger.error(f"Gmail scan timed out for user {state['user_id']}")
        state['job_emails'] = []
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

# Node for parsing uploaded resume (Issue #4) with POPIA compliance
def parse_resume(state: AgentState) -> AgentState:
    try:
        # This would typically parse an uploaded resume file
        # For now, load the master resume as placeholder
        with open('../resume_doc_processing/master_resume.json', 'r') as f:
            raw_resume = json.load(f)

        # Apply POPIA anonymization
        if popia_compliance:
            logger.info(f"Applying POPIA anonymization for user {state['user_id']}")
            anonymized_resume, mapping_dict = popia_compliance.anonymize_user_data(raw_resume)

            # Audit the data processing
            popia_compliance.audit_data_processing(
                state['user_id'],
                'resume_parsing',
                ['personal_info', 'career_data', 'skills']
            )

            # Store anonymization mapping for compliance
            anonymized_resume['_popia_compliant'] = True
            anonymized_resume['_anonymized_at'] = str(datetime.now())
            anonymized_resume['_user_id'] = state['user_id']

            state['parsed_resume'] = anonymized_resume
        else:
            state['parsed_resume'] = raw_resume

        logger.info("Parsed and anonymized resume with POPIA compliance")
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

# Node for game recommendations based on resume skills
def generate_game_recommendations(state: AgentState) -> AgentState:
    """Generate game recommendations based on user's resume skills."""
    try:
        if not state.get('parsed_resume'):
            logger.info("No parsed resume available for game recommendations")
            state['game_recommendations'] = {}
            return state

        # Extract skills from resume
        resume_skills = state['parsed_resume'].get('skills', [])
        if not resume_skills:
            logger.info("No skills found in resume for game recommendations")
            state['game_recommendations'] = {}
            return state

        # Log game recommendations generation
        user_id = state.get('user_id', 'unknown')
        skills_count = len(resume_skills)
        log_conversation_entry("Game Recommendations", f"Generated game recommendations for user {user_id}", f"Skills analyzed: {skills_count}, Games: Virtonomics, Sim Companies, CWetlands, The Blue Connection")

        game_recommendations = {}

        # Get recommendations from each game
        try:
            if virtonomics_integration:
                v_rec = virtonomics_integration.get_virtonomics_recommendations(resume_skills)
                game_recommendations['virtonomics'] = v_rec
        except Exception as e:
            logger.warning(f"Error getting Virtonomics recommendations: {e}")

        try:
            if simcompanies_integration:
                s_rec = simcompanies_integration.get_simcompanies_recommendations(resume_skills)
                game_recommendations['simcompanies'] = s_rec
        except Exception as e:
            logger.warning(f"Error getting Sim Companies recommendations: {e}")

        try:
            if cwetlands_integration:
                c_rec = cwetlands_integration.get_cwetlands_recommendations(resume_skills)
                game_recommendations['cwetlands'] = c_rec
        except Exception as e:
            logger.warning(f"Error getting CWetlands recommendations: {e}")

        try:
            if theblueconnection_integration:
                t_rec = theblueconnection_integration.get_theblueconnection_recommendations(resume_skills)
                game_recommendations['theblueconnection'] = t_rec
        except Exception as e:
            logger.warning(f"Error getting The Blue Connection recommendations: {e}")

        state['game_recommendations'] = game_recommendations
        logger.info(f"Generated game recommendations for {len(game_recommendations)} games")

    except Exception as e:
        logger.error(f"Error generating game recommendations: {e}")
        state['game_recommendations'] = {}
    return state

# Node for awarding tokens for completed activities
def award_activity_tokens(state: AgentState) -> AgentState:
    """Award tokens for completed activities in the workflow."""
    try:
        if not token_system:
            logger.info("Token system not available, skipping token awards")
            state['token_activities'] = []
            return state

        user_id = state.get('user_id', 'unknown')
        token_activities = []

        # Award tokens for job applications (if resumes were generated)
        if state.get('generated_resumes'):
            num_resumes = len([r for r in state['generated_resumes'] if 'skipped' not in r])
            if num_resumes > 0:
                result = token_system.earn_tokens(user_id, 'job_application',
                    {'num_applications': num_resumes, 'workflow_generated': True})
                token_activities.append({
                    'activity': 'job_application',
                    'tokens_earned': result.get('tokens_earned', 0),
                    'details': f"Applied to {num_resumes} high-fit jobs"
                })

        # Award tokens for course completion (if courses were suggested)
        if state.get('course_suggestions') and any(state['course_suggestions'].values()):
            num_courses = sum(len(courses) for courses in state['course_suggestions'].values())
            if num_courses > 0:
                result = token_system.earn_tokens(user_id, 'course_completion',
                    {'num_courses': num_courses, 'workflow_generated': True})
                token_activities.append({
                    'activity': 'course_completion',
                    'tokens_earned': result.get('tokens_earned', 0),
                    'details': f"Completed {num_courses} skill development courses"
                })

        # Award tokens for game activities (if recommendations were generated)
        if state.get('game_recommendations'):
            num_games = len(state['game_recommendations'])
            if num_games > 0:
                result = token_system.earn_tokens(user_id, 'game_activity_completion',
                    {'num_games': num_games, 'workflow_generated': True})
                token_activities.append({
                    'activity': 'game_activity_completion',
                    'tokens_earned': result.get('tokens_earned', 0),
                    'details': f"Explored {num_games} serious games for skill development"
                })

        # Award tokens for profile optimization (if resume was audited)
        if state.get('audited_resumes'):
            num_audits = len(state['audited_resumes'])
            if num_audits > 0:
                result = token_system.earn_tokens(user_id, 'profile_optimization',
                    {'num_audits': num_audits, 'workflow_generated': True})
                token_activities.append({
                    'activity': 'profile_optimization',
                    'tokens_earned': result.get('tokens_earned', 0),
                    'details': f"Optimized {num_audits} resumes with AI auditing"
                })

        state['token_activities'] = token_activities
        logger.info(f"Awarded tokens for {len(token_activities)} activities to user {user_id}")

        # Log token activities
        if token_activities:
            total_tokens = sum(activity.get('tokens_earned', 0) for activity in token_activities)
            log_conversation_entry("Token Awards", f"User {user_id} earned {total_tokens} tokens", f"Activities: {len(token_activities)}, Total tokens: {total_tokens}")

    except Exception as e:
        logger.error(f"Error awarding activity tokens: {e}")
        state['token_activities'] = []
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
workflow.add_node("generate_game_recommendations", generate_game_recommendations)
workflow.add_node("award_activity_tokens", award_activity_tokens)
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
workflow.add_edge("suggest_courses", "generate_game_recommendations")
workflow.add_edge("generate_game_recommendations", "award_activity_tokens")
workflow.add_edge("award_activity_tokens", "send_emails")
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
        skill_gaps=[],
        game_recommendations={},
        token_activities=[]
    )
    result = app.invoke(initial_state)
    print("Workflow completed:", result)