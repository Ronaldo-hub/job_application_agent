"""
FastAPI MCP Server for Core Orchestrator Service
Implements MCP protocol for job application workflow orchestration
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymongo
from pymongo import MongoClient
import asyncio

# Import existing logic
from agent_core.main import AgentState, scan_gmail, search_api_jobs, parse_jobs, parse_resume, analyze_job_fit, generate_resumes, audit_resumes, suggest_courses, discord_notifications, generate_game_recommendations, award_activity_tokens
from agent_core import conversational_ai
from resume_doc_processing import resume_tool
from job_discovery_matching import job_search
from learning_recommendations import course_suggestions
from gamification_engine import token_system

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Core Orchestrator MCP Server",
    description="MCP server for job application workflow orchestration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:password@mongodb:27017/job_application_agent')
client = MongoClient(mongo_uri)
db = client.job_application_agent

# Pydantic models for MCP
class MCPTool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class MCPResource(BaseModel):
    uri: str
    name: str
    description: str
    mimeType: str

class MCPPrompt(BaseModel):
    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]]] = None

class MCPListRequest(BaseModel):
    cursor: Optional[str] = None

class MCPToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class MCPToolResponse(BaseModel):
    content: List[Dict[str, Any]]
    isError: bool = False

# MCP Tools
MCP_TOOLS = [
    {
        "name": "run_job_application_workflow",
        "description": "Run the complete job application workflow for a user",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "keywords": {"type": "string", "description": "Job search keywords"},
                "location": {"type": "string", "description": "Job location"},
                "max_age_days": {"type": "integer", "description": "Maximum job age in days", "default": 30}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "scan_gmail_for_jobs",
        "description": "Scan Gmail for job-related emails",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "search_jobs_api",
        "description": "Search for jobs using external APIs",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keywords": {"type": "string", "description": "Job search keywords"},
                "location": {"type": "string", "description": "Job location"},
                "max_age_days": {"type": "integer", "description": "Maximum job age in days", "default": 30}
            },
            "required": ["keywords"]
        }
    },
    {
        "name": "analyze_job_fit",
        "description": "Analyze job fit against user's resume",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "job_data": {"type": "object", "description": "Job details"}
            },
            "required": ["user_id", "job_data"]
        }
    },
    {
        "name": "generate_optimized_resume",
        "description": "Generate ATS-optimized resume for a job",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "job_data": {"type": "object", "description": "Job details"}
            },
            "required": ["user_id", "job_data"]
        }
    },
    {
        "name": "suggest_learning_courses",
        "description": "Suggest courses for skill gaps",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "skill_gaps": {"type": "array", "description": "List of skill gaps"}
            },
            "required": ["user_id", "skill_gaps"]
        }
    },
    {
        "name": "get_game_recommendations",
        "description": "Get game recommendations based on user skills",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "skills": {"type": "array", "description": "User skills"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "award_tokens",
        "description": "Award tokens for completed activities",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "activity_type": {"type": "string", "description": "Activity type"},
                "metadata": {"type": "object", "description": "Activity metadata"}
            },
            "required": ["user_id", "activity_type"]
        }
    }
]

# MCP Resources
MCP_RESOURCES = [
    {
        "uri": "mongodb://job_application_agent/workflows",
        "name": "Workflow Results",
        "description": "Access to workflow execution results",
        "mimeType": "application/json"
    },
    {
        "uri": "mongodb://job_application_agent/user_profiles",
        "name": "User Profiles",
        "description": "Access to user profile data",
        "mimeType": "application/json"
    }
]

# MCP Prompts
MCP_PROMPTS = [
    {
        "name": "job_application_workflow",
        "description": "Prompt for running job application workflow",
        "arguments": [
            {"name": "user_id", "description": "User identifier", "required": True},
            {"name": "keywords", "description": "Job search keywords", "required": False}
        ]
    }
]

# MCP Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Core Orchestrator MCP Server", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        db.command('ping')
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/mcp/tools")
async def list_tools():
    """List available MCP tools"""
    return {"tools": MCP_TOOLS}

@app.get("/mcp/resources")
async def list_resources():
    """List available MCP resources"""
    return {"resources": MCP_RESOURCES}

@app.get("/mcp/prompts")
async def list_prompts():
    """List available MCP prompts"""
    return {"prompts": MCP_PROMPTS}

@app.post("/mcp/tools/call")
async def call_tool(tool_call: MCPToolCall, background_tasks: BackgroundTasks):
    """Execute MCP tool"""
    try:
        tool_name = tool_call.name
        arguments = tool_call.arguments

        if tool_name == "run_job_application_workflow":
            return await run_workflow(arguments, background_tasks)
        elif tool_name == "scan_gmail_for_jobs":
            return await scan_gmail_tool(arguments)
        elif tool_name == "search_jobs_api":
            return await search_jobs_tool(arguments)
        elif tool_name == "analyze_job_fit":
            return await analyze_fit_tool(arguments)
        elif tool_name == "generate_optimized_resume":
            return await generate_resume_tool(arguments)
        elif tool_name == "suggest_learning_courses":
            return await suggest_courses_tool(arguments)
        elif tool_name == "get_game_recommendations":
            return await game_recommendations_tool(arguments)
        elif tool_name == "award_tokens":
            return await award_tokens_tool(arguments)
        else:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

    except HTTPException:
        # Re-raise HTTP exceptions to maintain proper status codes
        raise
    except Exception as e:
        logger.error(f"Error calling tool {tool_call.name}: {e}")
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error: {str(e)}"}],
            isError=True
        )

@app.get("/mcp/resources/{uri:path}")
async def read_resource(uri: str):
    """Read MCP resource"""
    try:
        if uri == "mongodb://job_application_agent/workflows":
            # Return recent workflow results
            workflows = list(db.workflows.find().sort("timestamp", -1).limit(10))
            return {"content": [{"type": "text", "text": json.dumps(workflows, default=str)}]}
        elif uri == "mongodb://job_application_agent/user_profiles":
            # Return user profiles (anonymized)
            profiles = list(db.user_profiles.find({}, {"_id": 0, "personal_info": 0}))
            return {"content": [{"type": "text", "text": json.dumps(profiles, default=str)}]}
        else:
            raise HTTPException(status_code=404, detail=f"Resource {uri} not found")
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/prompts/{name}")
async def get_prompt(name: str):
    """Get MCP prompt"""
    prompt = next((p for p in MCP_PROMPTS if p["name"] == name), None)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt {name} not found")
    return {"prompt": prompt}

# Tool implementations
async def run_workflow(arguments: Dict[str, Any], background_tasks: BackgroundTasks) -> MCPToolResponse:
    """Run the complete job application workflow"""
    user_id = arguments["user_id"]
    keywords = arguments.get("keywords", "software engineer")
    location = arguments.get("location", "remote")
    max_age_days = arguments.get("max_age_days", 30)

    try:
        # Initialize state
        state = AgentState(
            messages=[],
            user_id=user_id,
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

        # Run workflow steps asynchronously
        background_tasks.add_task(run_workflow_async, state, keywords, location, max_age_days)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Workflow started for user {user_id}. Check workflow status for results."
            }]
        )

    except Exception as e:
        logger.error(f"Error starting workflow: {e}")
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error starting workflow: {str(e)}"}],
            isError=True
        )

async def run_workflow_async(state: AgentState, keywords: str, location: str, max_age_days: int):
    """Run workflow asynchronously"""
    try:
        # Step 1: Parse resume
        state = parse_resume(state)

        # Step 2: Search jobs
        search_params = {
            'keywords': keywords,
            'location': location,
            'max_age_days': max_age_days
        }
        state['api_jobs'] = await job_search.search_jobs_async(search_params)

        # Step 3: Analyze fit
        state = analyze_job_fit(state)

        # Step 4: Generate resumes for high-fit jobs
        state = generate_resumes(state)

        # Step 5: Audit resumes
        state = audit_resumes(state)

        # Step 6: Suggest courses
        state = suggest_courses(state)

        # Step 7: Generate game recommendations
        state = generate_game_recommendations(state)

        # Step 8: Award tokens
        state = award_activity_tokens(state)

        # Step 9: Send notifications
        state = discord_notifications(state)

        # Save workflow results to MongoDB
        workflow_result = {
            "user_id": state["user_id"],
            "timestamp": datetime.now(),
            "keywords": keywords,
            "location": location,
            "jobs_found": len(state["api_jobs"]),
            "high_fit_jobs": len([j for j in state["parsed_jobs"] if j.get("fit_score", 0) >= 90]),
            "resumes_generated": len(state["generated_resumes"]),
            "skill_gaps": state["skill_gaps"],
            "course_suggestions": state["course_suggestions"],
            "game_recommendations": state["game_recommendations"],
            "tokens_awarded": sum(a.get("tokens_earned", 0) for a in state["token_activities"])
        }

        db.workflows.insert_one(workflow_result)
        logger.info(f"Workflow completed for user {state['user_id']}")

    except Exception as e:
        logger.error(f"Error in workflow execution: {e}")

async def scan_gmail_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Scan Gmail for jobs"""
    user_id = arguments["user_id"]

    try:
        state = AgentState(
            messages=[],
            user_id=user_id,
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

        state = scan_gmail(state)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Found {len(state['job_emails'])} job emails for user {user_id}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error scanning Gmail: {str(e)}"}],
            isError=True
        )

async def search_jobs_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Search jobs using APIs"""
    keywords = arguments["keywords"]
    location = arguments.get("location")
    max_age_days = arguments.get("max_age_days", 30)

    try:
        search_params = {
            'keywords': keywords,
            'location': location,
            'max_age_days': max_age_days
        }

        jobs = await job_search.search_jobs_async(search_params)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Found {len(jobs)} jobs for '{keywords}'"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error searching jobs: {str(e)}"}],
            isError=True
        )

async def analyze_fit_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Analyze job fit"""
    user_id = arguments["user_id"]
    job_data = arguments["job_data"]

    try:
        # Load master resume (should be user's resume)
        master_resume = resume_tool.load_master_resume()
        fit_score = resume_tool.calculate_fit_score(master_resume, job_data)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Job fit score: {fit_score:.1f}% for user {user_id}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error analyzing fit: {str(e)}"}],
            isError=True
        )

async def generate_resume_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Generate optimized resume"""
    user_id = arguments["user_id"]
    job_data = arguments["job_data"]

    try:
        resume = resume_tool.generate_resume(job_data)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Resume generated for {job_data.get('title', 'Unknown')} with fit score {resume.get('fit_score', 0):.1f}%"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error generating resume: {str(e)}"}],
            isError=True
        )

async def suggest_courses_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Suggest learning courses"""
    user_id = arguments["user_id"]
    skill_gaps = arguments["skill_gaps"]

    try:
        suggestions = await course_suggestions.get_course_suggestions(skill_gaps)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Generated course suggestions for {len(skill_gaps)} skill gaps"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error suggesting courses: {str(e)}"}],
            isError=True
        )

async def game_recommendations_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Get game recommendations"""
    user_id = arguments["user_id"]
    skills = arguments.get("skills", [])

    try:
        # This would integrate with game recommendation logic
        recommendations = {
            "virtonomics": "Business simulation game",
            "simcompanies": "Company management game",
            "cwetlands": "Environmental management game"
        }

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Generated game recommendations for user {user_id}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error getting game recommendations: {str(e)}"}],
            isError=True
        )

async def award_tokens_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Award tokens for activities"""
    user_id = arguments["user_id"]
    activity_type = arguments["activity_type"]
    metadata = arguments.get("metadata", {})

    try:
        result = token_system.earn_tokens(user_id, activity_type, metadata)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Awarded {result.get('tokens_earned', 0)} tokens to user {user_id}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error awarding tokens: {str(e)}"}],
            isError=True
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)