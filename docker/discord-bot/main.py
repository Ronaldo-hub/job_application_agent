"""
FastAPI MCP Server for Discord Bot Service
Implements MCP protocol for Discord bot functionality and notifications
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymongo
from pymongo import MongoClient
import asyncio

# Import existing logic
from email_comm_hub.discord_bot import send_notification
from gamification_engine import token_system
from learning_recommendations import course_suggestions
from job_discovery_matching import job_search
from resume_doc_processing import resume_tool
from learning_recommendations import virtonomics_integration, simcompanies_integration, cwetlands_integration, theblueconnection_integration
from mesa_abm_simulations import run_policy_simulation
from agent_core import conversational_ai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Discord Bot MCP Server",
    description="MCP server for Discord bot functionality",
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

class MCPToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class MCPToolResponse(BaseModel):
    content: List[Dict[str, Any]]
    isError: bool = False

# MCP Tools
MCP_TOOLS = [
    {
        "name": "send_discord_notification",
        "description": "Send notification to Discord user",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Discord user ID"},
                "message": {"type": "string", "description": "Notification message"},
                "embed_data": {"type": "object", "description": "Embed data for rich notification"}
            },
            "required": ["user_id", "message"]
        }
    },
    {
        "name": "search_jobs_discord",
        "description": "Search jobs and send results to Discord",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Discord user ID"},
                "keywords": {"type": "string", "description": "Job search keywords"},
                "location": {"type": "string", "description": "Job location"},
                "max_age_days": {"type": "integer", "description": "Maximum job age in days", "default": 30}
            },
            "required": ["user_id", "keywords"]
        }
    },
    {
        "name": "get_game_recommendations_discord",
        "description": "Get game recommendations and send to Discord",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Discord user ID"},
                "skills": {"type": "array", "description": "User skills"},
                "game": {"type": "string", "description": "Specific game to focus on"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "run_policy_simulation_discord",
        "description": "Run policy simulation and send results to Discord",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Discord user ID"},
                "simulation_type": {"type": "string", "description": "Type of simulation"},
                "parameters": {"type": "object", "description": "Simulation parameters"}
            },
            "required": ["user_id", "simulation_type"]
        }
    },
    {
        "name": "check_user_tokens_discord",
        "description": "Check user's token balance and send to Discord",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Discord user ID"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "award_tokens_discord",
        "description": "Award tokens and notify user on Discord",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Discord user ID"},
                "activity_type": {"type": "string", "description": "Activity type"},
                "metadata": {"type": "object", "description": "Activity metadata"}
            },
            "required": ["user_id", "activity_type"]
        }
    },
    {
        "name": "chat_with_ai_discord",
        "description": "Have conversational AI chat and send response to Discord",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Discord user ID"},
                "message": {"type": "string", "description": "User message"},
                "context": {"type": "object", "description": "User context"}
            },
            "required": ["user_id", "message"]
        }
    },
    {
        "name": "get_course_suggestions_discord",
        "description": "Get course suggestions and send to Discord",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Discord user ID"},
                "skill_gaps": {"type": "array", "description": "Skill gaps to address"}
            },
            "required": ["user_id", "skill_gaps"]
        }
    }
]

# MCP Resources
MCP_RESOURCES = [
    {
        "uri": "mongodb://job_application_agent/discord_notifications",
        "name": "Discord Notifications",
        "description": "Access to Discord notification history",
        "mimeType": "application/json"
    },
    {
        "uri": "mongodb://job_application_agent/discord_interactions",
        "name": "Discord Interactions",
        "description": "Access to Discord user interactions",
        "mimeType": "application/json"
    }
]

# MCP Prompts
MCP_PROMPTS = [
    {
        "name": "discord_notification_template",
        "description": "Template for Discord notifications",
        "arguments": [
            {"name": "notification_type", "description": "Type of notification", "required": True}
        ]
    }
]

# MCP Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Discord Bot MCP Server", "version": "1.0.0"}

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
async def call_tool(tool_call: MCPToolCall):
    """Execute MCP tool"""
    try:
        tool_name = tool_call.name
        arguments = tool_call.arguments

        if tool_name == "send_discord_notification":
            return await send_discord_notification_tool(arguments)
        elif tool_name == "search_jobs_discord":
            return await search_jobs_discord_tool(arguments)
        elif tool_name == "get_game_recommendations_discord":
            return await get_game_recommendations_discord_tool(arguments)
        elif tool_name == "run_policy_simulation_discord":
            return await run_policy_simulation_discord_tool(arguments)
        elif tool_name == "check_user_tokens_discord":
            return await check_user_tokens_discord_tool(arguments)
        elif tool_name == "award_tokens_discord":
            return await award_tokens_discord_tool(arguments)
        elif tool_name == "chat_with_ai_discord":
            return await chat_with_ai_discord_tool(arguments)
        elif tool_name == "get_course_suggestions_discord":
            return await get_course_suggestions_discord_tool(arguments)
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
        if uri == "mongodb://job_application_agent/discord_notifications":
            # Return recent Discord notifications
            notifications = list(db.discord_notifications.find().sort("timestamp", -1).limit(20))
            return {"content": [{"type": "text", "text": json.dumps(notifications, default=str)}]}
        elif uri == "mongodb://job_application_agent/discord_interactions":
            # Return recent Discord interactions
            interactions = list(db.discord_interactions.find().sort("timestamp", -1).limit(20))
            return {"content": [{"type": "text", "text": json.dumps(interactions, default=str)}]}
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
async def send_discord_notification_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Send Discord notification"""
    user_id = arguments["user_id"]
    message = arguments["message"]
    embed_data = arguments.get("embed_data")

    try:
        # This would integrate with actual Discord bot
        # For now, simulate sending notification
        notification_doc = {
            "user_id": user_id,
            "message": message,
            "embed_data": embed_data,
            "timestamp": datetime.now(),
            "status": "sent"
        }
        db.discord_notifications.insert_one(notification_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Discord notification sent to user {user_id}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error sending Discord notification: {str(e)}"}],
            isError=True
        )

async def search_jobs_discord_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Search jobs and send to Discord"""
    user_id = arguments["user_id"]
    keywords = arguments["keywords"]
    location = arguments.get("location")
    max_age_days = arguments.get("max_age_days", 30)

    try:
        # Search jobs
        search_params = {
            'keywords': keywords,
            'location': location,
            'max_age_days': max_age_days
        }
        jobs = await job_search.search_jobs_async(search_params)

        # Analyze fit for top jobs
        master_resume = resume_tool.load_master_resume()
        high_fit_jobs = []

        for job in jobs[:5]:  # Top 5 jobs
            fit_score = resume_tool.calculate_fit_score(master_resume, job)
            if fit_score >= 70:  # High fit threshold
                high_fit_jobs.append({
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "fit_score": fit_score
                })

        # Send notification
        if high_fit_jobs:
            message = f"Found {len(high_fit_jobs)} high-fit jobs for '{keywords}'!"
            embed_data = {
                "title": "High-Fit Job Matches",
                "description": f"Jobs matching your profile for '{keywords}'",
                "fields": [
                    {
                        "name": f"{job['title']} at {job['company']}",
                        "value": f"Fit Score: {job['fit_score']:.1f}%",
                        "inline": False
                    } for job in high_fit_jobs[:3]
                ]
            }
        else:
            message = f"No high-fit jobs found for '{keywords}'. Try broader search terms."
            embed_data = None

        # Log interaction
        interaction_doc = {
            "user_id": user_id,
            "interaction_type": "job_search",
            "keywords": keywords,
            "results_count": len(jobs),
            "high_fit_count": len(high_fit_jobs),
            "timestamp": datetime.now()
        }
        db.discord_interactions.insert_one(interaction_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Job search completed for user {user_id}: {len(jobs)} jobs found, {len(high_fit_jobs)} high-fit"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error in Discord job search: {str(e)}"}],
            isError=True
        )

async def get_game_recommendations_discord_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Get game recommendations for Discord"""
    user_id = arguments["user_id"]
    skills = arguments.get("skills", [])
    game = arguments.get("game")

    try:
        recommendations = {}

        if game:
            # Specific game recommendation
            if game.lower() == 'virtonomics' and virtonomics_integration:
                recommendations = virtonomics_integration.get_virtonomics_recommendations(skills)
            elif game.lower() == 'simcompanies' and simcompanies_integration:
                recommendations = simcompanies_integration.get_simcompanies_recommendations(skills)
            elif game.lower() == 'cwetlands' and cwetlands_integration:
                recommendations = cwetlands_integration.get_cwetlands_recommendations(skills)
            elif game.lower() == 'theblueconnection' and theblueconnection_integration:
                recommendations = theblueconnection_integration.get_theblueconnection_recommendations(skills)
        else:
            # Get from all games
            if virtonomics_integration:
                recommendations['virtonomics'] = virtonomics_integration.get_virtonomics_recommendations(skills)
            if simcompanies_integration:
                recommendations['simcompanies'] = simcompanies_integration.get_simcompanies_recommendations(skills)

        # Log interaction
        interaction_doc = {
            "user_id": user_id,
            "interaction_type": "game_recommendation",
            "skills": skills,
            "game": game,
            "recommendations_count": len(recommendations),
            "timestamp": datetime.now()
        }
        db.discord_interactions.insert_one(interaction_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Game recommendations generated for user {user_id}: {len(recommendations)} games"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error getting game recommendations: {str(e)}"}],
            isError=True
        )

async def run_policy_simulation_discord_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Run policy simulation for Discord"""
    user_id = arguments["user_id"]
    simulation_type = arguments["simulation_type"]
    parameters = arguments.get("parameters", {})

    try:
        result = run_policy_simulation(simulation_type, parameters)

        if 'error' in result:
            return MCPToolResponse(
                content=[{"type": "text", "text": f"Simulation error: {result['error']}"}],
                isError=True
            )

        effectiveness = result.get('final_metrics', {}).get('policy_effectiveness', 0)

        # Log interaction
        interaction_doc = {
            "user_id": user_id,
            "interaction_type": "policy_simulation",
            "simulation_type": simulation_type,
            "effectiveness": effectiveness,
            "timestamp": datetime.now()
        }
        db.discord_interactions.insert_one(interaction_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Policy simulation completed for user {user_id}: {simulation_type} with {effectiveness:.1f}% effectiveness"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error running policy simulation: {str(e)}"}],
            isError=True
        )

async def check_user_tokens_discord_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Check user tokens for Discord"""
    user_id = arguments["user_id"]

    try:
        stats = token_system.get_user_stats(user_id)

        # Log interaction
        interaction_doc = {
            "user_id": user_id,
            "interaction_type": "token_check",
            "current_tokens": stats.get('current_tokens', 0),
            "level": stats.get('level', 1),
            "timestamp": datetime.now()
        }
        db.discord_interactions.insert_one(interaction_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Token check for user {user_id}: {stats.get('current_tokens', 0)} tokens, Level {stats.get('level', 1)}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error checking tokens: {str(e)}"}],
            isError=True
        )

async def award_tokens_discord_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Award tokens for Discord"""
    user_id = arguments["user_id"]
    activity_type = arguments["activity_type"]
    metadata = arguments.get("metadata", {})

    try:
        result = token_system.earn_tokens(user_id, activity_type, metadata)

        # Log interaction
        interaction_doc = {
            "user_id": user_id,
            "interaction_type": "token_award",
            "activity_type": activity_type,
            "tokens_earned": result.get('tokens_earned', 0),
            "timestamp": datetime.now()
        }
        db.discord_interactions.insert_one(interaction_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Tokens awarded to user {user_id}: +{result.get('tokens_earned', 0)} for {activity_type}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error awarding tokens: {str(e)}"}],
            isError=True
        )

async def chat_with_ai_discord_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Chat with AI for Discord"""
    user_id = arguments["user_id"]
    message = arguments["message"]
    context = arguments.get("context", {})

    try:
        if conversational_ai:
            response = conversational_ai.chat_with_user(user_id, message, context)
        else:
            response = "AI assistant is currently unavailable."

        # Log interaction
        interaction_doc = {
            "user_id": user_id,
            "interaction_type": "ai_chat",
            "user_message": message,
            "ai_response": response,
            "timestamp": datetime.now()
        }
        db.discord_interactions.insert_one(interaction_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"AI chat completed for user {user_id}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error in AI chat: {str(e)}"}],
            isError=True
        )

async def get_course_suggestions_discord_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Get course suggestions for Discord"""
    user_id = arguments["user_id"]
    skill_gaps = arguments["skill_gaps"]

    try:
        suggestions = await course_suggestions.get_course_suggestions(skill_gaps)

        # Log interaction
        interaction_doc = {
            "user_id": user_id,
            "interaction_type": "course_suggestion",
            "skill_gaps": skill_gaps,
            "suggestions_count": len(suggestions),
            "timestamp": datetime.now()
        }
        db.discord_interactions.insert_one(interaction_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Course suggestions generated for user {user_id}: {len(suggestions)} skill gaps addressed"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error getting course suggestions: {str(e)}"}],
            isError=True
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)