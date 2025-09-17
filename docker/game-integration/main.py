"""
FastAPI MCP Server for Game Integration Service
Implements MCP protocol for gamification and learning integrations
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
from gamification_engine import token_system
from learning_recommendations import course_suggestions
from learning_recommendations import virtonomics_integration, simcompanies_integration, cwetlands_integration, theblueconnection_integration
from learning_recommendations import game_activity_tracker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Game Integration MCP Server",
    description="MCP server for gamification and learning integrations",
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
        "name": "earn_gamification_tokens",
        "description": "Award tokens for gamification activities",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "activity_type": {"type": "string", "description": "Type of activity"},
                "metadata": {"type": "object", "description": "Activity metadata"}
            },
            "required": ["user_id", "activity_type"]
        }
    },
    {
        "name": "spend_gamification_tokens",
        "description": "Redeem tokens for rewards",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "reward_id": {"type": "string", "description": "Reward to redeem"}
            },
            "required": ["user_id", "reward_id"]
        }
    },
    {
        "name": "get_user_gamification_stats",
        "description": "Get user's gamification statistics",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_game_recommendations",
        "description": "Get game recommendations based on user skills",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "skills": {"type": "array", "description": "User skills"},
                "game": {"type": "string", "description": "Specific game to focus on"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "track_game_activity",
        "description": "Track user activity in serious games",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "game": {"type": "string", "description": "Game name"},
                "activity": {"type": "string", "description": "Activity performed"},
                "metadata": {"type": "object", "description": "Activity metadata"}
            },
            "required": ["user_id", "game", "activity"]
        }
    },
    {
        "name": "get_course_recommendations",
        "description": "Get learning course recommendations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "skill_gaps": {"type": "array", "description": "Skill gaps to address"}
            },
            "required": ["user_id", "skill_gaps"]
        }
    },
    {
        "name": "get_gamification_leaderboard",
        "description": "Get gamification leaderboard",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of top users to return", "default": 10}
            }
        }
    },
    {
        "name": "analyze_user_progress",
        "description": "Analyze user's learning and gaming progress",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"}
            },
            "required": ["user_id"]
        }
    }
]

# MCP Resources
MCP_RESOURCES = [
    {
        "uri": "mongodb://job_application_agent/gamification_stats",
        "name": "Gamification Statistics",
        "description": "Access to gamification user statistics",
        "mimeType": "application/json"
    },
    {
        "uri": "mongodb://job_application_agent/game_activities",
        "name": "Game Activities",
        "description": "Access to tracked game activities",
        "mimeType": "application/json"
    },
    {
        "uri": "mongodb://job_application_agent/course_recommendations",
        "name": "Course Recommendations",
        "description": "Access to learning course recommendations",
        "mimeType": "application/json"
    }
]

# MCP Prompts
MCP_PROMPTS = [
    {
        "name": "gamification_motivation",
        "description": "Prompt for gamification motivation strategies",
        "arguments": [
            {"name": "user_level", "description": "User's current level", "required": True}
        ]
    }
]

# MCP Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Game Integration MCP Server", "version": "1.0.0"}

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

        if tool_name == "earn_gamification_tokens":
            return await earn_gamification_tokens_tool(arguments)
        elif tool_name == "spend_gamification_tokens":
            return await spend_gamification_tokens_tool(arguments)
        elif tool_name == "get_user_gamification_stats":
            return await get_user_gamification_stats_tool(arguments)
        elif tool_name == "get_game_recommendations":
            return await get_game_recommendations_tool(arguments)
        elif tool_name == "track_game_activity":
            return await track_game_activity_tool(arguments)
        elif tool_name == "get_course_recommendations":
            return await get_course_recommendations_tool(arguments)
        elif tool_name == "get_gamification_leaderboard":
            return await get_gamification_leaderboard_tool(arguments)
        elif tool_name == "analyze_user_progress":
            return await analyze_user_progress_tool(arguments)
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
        if uri == "mongodb://job_application_agent/gamification_stats":
            # Return gamification statistics
            stats = list(db.gamification_stats.find().sort("timestamp", -1).limit(20))
            return {"content": [{"type": "text", "text": json.dumps(stats, default=str)}]}
        elif uri == "mongodb://job_application_agent/game_activities":
            # Return game activities
            activities = list(db.game_activities.find().sort("timestamp", -1).limit(50))
            return {"content": [{"type": "text", "text": json.dumps(activities, default=str)}]}
        elif uri == "mongodb://job_application_agent/course_recommendations":
            # Return course recommendations
            recommendations = list(db.course_recommendations.find().sort("timestamp", -1).limit(20))
            return {"content": [{"type": "text", "text": json.dumps(recommendations, default=str)}]}
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
async def earn_gamification_tokens_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Earn gamification tokens"""
    user_id = arguments["user_id"]
    activity_type = arguments["activity_type"]
    metadata = arguments.get("metadata", {})

    try:
        result = token_system.earn_tokens(user_id, activity_type, metadata)

        # Log gamification activity
        activity_doc = {
            "user_id": user_id,
            "activity_type": activity_type,
            "tokens_earned": result.get('tokens_earned', 0),
            "metadata": metadata,
            "timestamp": datetime.now()
        }
        db.gamification_activities.insert_one(activity_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Tokens earned for user {user_id}: +{result.get('tokens_earned', 0)} for {activity_type}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error earning tokens: {str(e)}"}],
            isError=True
        )

async def spend_gamification_tokens_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Spend gamification tokens"""
    user_id = arguments["user_id"]
    reward_id = arguments["reward_id"]

    try:
        result = token_system.spend_tokens(user_id, reward_id)

        if 'error' in result:
            return MCPToolResponse(
                content=[{"type": "text", "text": f"Error redeeming reward: {result['error']}"}],
                isError=True
            )

        # Log reward redemption
        redemption_doc = {
            "user_id": user_id,
            "reward_id": reward_id,
            "cost": result.get('cost', 0),
            "timestamp": datetime.now()
        }
        db.reward_redemptions.insert_one(redemption_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Reward redeemed for user {user_id}: {result.get('reward', 'Unknown')} for {result.get('cost', 0)} tokens"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error spending tokens: {str(e)}"}],
            isError=True
        )

async def get_user_gamification_stats_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Get user gamification stats"""
    user_id = arguments["user_id"]

    try:
        stats = token_system.get_user_stats(user_id)

        # Save stats snapshot
        stats_doc = {
            "user_id": user_id,
            "stats": stats,
            "timestamp": datetime.now()
        }
        db.gamification_stats.insert_one(stats_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Gamification stats for user {user_id}: Level {stats.get('level', 1)}, {stats.get('current_tokens', 0)} tokens, {stats.get('achievements_count', 0)} achievements"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error getting gamification stats: {str(e)}"}],
            isError=True
        )

async def get_game_recommendations_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Get game recommendations"""
    user_id = arguments["user_id"]
    skills = arguments.get("skills", [])
    game = arguments.get("game")

    try:
        recommendations = {}

        if game:
            # Specific game
            if game.lower() == 'virtonomics' and virtonomics_integration:
                recommendations['virtonomics'] = virtonomics_integration.get_virtonomics_recommendations(skills)
            elif game.lower() == 'simcompanies' and simcompanies_integration:
                recommendations['simcompanies'] = simcompanies_integration.get_simcompanies_recommendations(skills)
            elif game.lower() == 'cwetlands' and cwetlands_integration:
                recommendations['cwetlands'] = cwetlands_integration.get_cwetlands_recommendations(skills)
            elif game.lower() == 'theblueconnection' and theblueconnection_integration:
                recommendations['theblueconnection'] = theblueconnection_integration.get_theblueconnection_recommendations(skills)
        else:
            # All games
            if virtonomics_integration:
                recommendations['virtonomics'] = virtonomics_integration.get_virtonomics_recommendations(skills)
            if simcompanies_integration:
                recommendations['simcompanies'] = simcompanies_integration.get_simcompanies_recommendations(skills)
            if cwetlands_integration:
                recommendations['cwetlands'] = cwetlands_integration.get_cwetlands_recommendations(skills)
            if theblueconnection_integration:
                recommendations['theblueconnection'] = theblueconnection_integration.get_theblueconnection_recommendations(skills)

        # Save recommendations
        rec_doc = {
            "user_id": user_id,
            "skills": skills,
            "game": game,
            "recommendations": recommendations,
            "timestamp": datetime.now()
        }
        db.game_recommendations.insert_one(rec_doc)

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

async def track_game_activity_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Track game activity"""
    user_id = arguments["user_id"]
    game = arguments["game"]
    activity = arguments["activity"]
    metadata = arguments.get("metadata", {})

    try:
        if game_activity_tracker:
            result = game_activity_tracker.track_activity(user_id, game, activity, metadata)

            # Save activity
            activity_doc = {
                "user_id": user_id,
                "game": game,
                "activity": activity,
                "metadata": metadata,
                "result": result,
                "timestamp": datetime.now()
            }
            db.game_activities.insert_one(activity_doc)

            tokens_earned = result.get('tokens_earned', 0)
            return MCPToolResponse(
                content=[{
                    "type": "text",
                    "text": f"Game activity tracked for user {user_id}: {activity} in {game}, +{tokens_earned} tokens"
                }]
            )
        else:
            return MCPToolResponse(
                content=[{"type": "text", "text": "Game activity tracker not available"}],
                isError=True
            )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error tracking game activity: {str(e)}"}],
            isError=True
        )

async def get_course_recommendations_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Get course recommendations"""
    user_id = arguments["user_id"]
    skill_gaps = arguments["skill_gaps"]

    try:
        recommendations = await course_suggestions.get_course_suggestions(skill_gaps)

        # Save recommendations
        rec_doc = {
            "user_id": user_id,
            "skill_gaps": skill_gaps,
            "recommendations": recommendations,
            "timestamp": datetime.now()
        }
        db.course_recommendations.insert_one(rec_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Course recommendations generated for user {user_id}: {len(recommendations)} skill gaps addressed"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error getting course recommendations: {str(e)}"}],
            isError=True
        )

async def get_gamification_leaderboard_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Get gamification leaderboard"""
    limit = arguments.get("limit", 10)

    try:
        leaderboard = token_system.get_leaderboard(limit)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Gamification leaderboard retrieved: Top {len(leaderboard)} users"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error getting leaderboard: {str(e)}"}],
            isError=True
        )

async def analyze_user_progress_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Analyze user progress"""
    user_id = arguments["user_id"]

    try:
        if game_activity_tracker:
            progress_report = game_activity_tracker.get_user_progress_report(user_id)

            # Save progress analysis
            progress_doc = {
                "user_id": user_id,
                "progress_report": progress_report,
                "timestamp": datetime.now()
            }
            db.progress_analyses.insert_one(progress_doc)

            total_activities = progress_report.get('total_activities', 0)
            current_level = progress_report.get('current_level', 1)

            return MCPToolResponse(
                content=[{
                    "type": "text",
                    "text": f"User progress analysis for {user_id}: {total_activities} activities, Level {current_level}"
                }]
            )
        else:
            return MCPToolResponse(
                content=[{"type": "text", "text": "Progress tracker not available"}],
                isError=True
            )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error analyzing user progress: {str(e)}"}],
            isError=True
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)