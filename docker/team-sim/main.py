"""
FastAPI MCP Server for Team Simulation Service
Implements MCP protocol for ABM policy simulations
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
from sklearn.cluster import KMeans
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Import existing logic
from mesa_abm_simulations import run_policy_simulation, generate_policy_recommendations

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Team Simulation MCP Server",
    description="MCP server for ABM policy simulations",
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
        "name": "run_policy_simulation",
        "description": "Run ABM policy simulation for social issues",
        "inputSchema": {
            "type": "object",
            "properties": {
                "simulation_type": {"type": "string", "description": "Type of simulation (unemployment, drug_abuse, trafficking, water_scarcity, cape_town_unemployment, cape_town_water_crisis)"},
                "parameters": {"type": "object", "description": "Simulation parameters"},
                "user_id": {"type": "string", "description": "User identifier for logging"}
            },
            "required": ["simulation_type"]
        }
    },
    {
        "name": "compare_policy_scenarios",
        "description": "Compare different policy scenarios using ABM simulation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "simulation_type": {"type": "string", "description": "Type of simulation"},
                "scenarios": {"type": "array", "description": "List of policy scenarios to compare"},
                "user_id": {"type": "string", "description": "User identifier"}
            },
            "required": ["simulation_type", "scenarios"]
        }
    },
    {
        "name": "generate_policy_recommendations",
        "description": "Generate policy recommendations based on simulation results",
        "inputSchema": {
            "type": "object",
            "properties": {
                "simulation_results": {"type": "object", "description": "Results from policy simulation"},
                "user_id": {"type": "string", "description": "User identifier"}
            },
            "required": ["simulation_results"]
        }
    },
    {
        "name": "analyze_simulation_trends",
        "description": "Analyze trends and patterns from simulation data",
        "inputSchema": {
            "type": "object",
            "properties": {
                "simulation_data": {"type": "object", "description": "Simulation results data"},
                "analysis_type": {"type": "string", "description": "Type of analysis (effectiveness, trends, predictions)"},
                "user_id": {"type": "string", "description": "User identifier"}
            },
            "required": ["simulation_data", "analysis_type"]
        }
    },
    {
        "name": "run_cape_town_simulation",
        "description": "Run Cape Town-specific policy simulation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "issue_type": {"type": "string", "description": "Cape Town issue (unemployment, water_crisis)"},
                "parameters": {"type": "object", "description": "Simulation parameters"},
                "user_id": {"type": "string", "description": "User identifier"}
            },
            "required": ["issue_type"]
        }
    },
    {
        "name": "get_simulation_history",
        "description": "Get user's simulation history",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "limit": {"type": "integer", "description": "Maximum number of results", "default": 10}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "extract_team_skills",
        "description": "Extract skills from team members' resumes",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_ids": {"type": "array", "description": "List of user IDs to extract skills from", "items": {"type": "string"}},
                "user_id": {"type": "string", "description": "Requesting user identifier"}
            },
            "required": ["user_ids"]
        }
    },
    {
        "name": "form_teams",
        "description": "Form teams based on skill synergy using clustering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_ids": {"type": "array", "description": "List of user IDs to form teams from", "items": {"type": "string"}},
                "num_teams": {"type": "integer", "description": "Number of teams to form", "default": 3},
                "user_id": {"type": "string", "description": "Requesting user identifier"}
            },
            "required": ["user_ids"]
        }
    },
    {
        "name": "suggest_team_activities",
        "description": "Suggest collaborative activities for teams addressing Cape Town issues",
        "inputSchema": {
            "type": "object",
            "properties": {
                "teams": {"type": "object", "description": "Team composition data"},
                "cape_town_focus": {"type": "boolean", "description": "Focus on Cape Town specific issues", "default": True},
                "user_id": {"type": "string", "description": "Requesting user identifier"}
            },
            "required": ["teams"]
        }
    },
    {
        "name": "create_team_simulation",
        "description": "Create and run complete team formation simulation with activity suggestions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_ids": {"type": "array", "description": "List of user IDs for team simulation", "items": {"type": "string"}},
                "num_teams": {"type": "integer", "description": "Number of teams to form", "default": 3},
                "cape_town_focus": {"type": "boolean", "description": "Focus on Cape Town issues", "default": True},
                "user_id": {"type": "string", "description": "Requesting user identifier"}
            },
            "required": ["user_ids"]
        }
    }
]

# MCP Resources
MCP_RESOURCES = [
    {
        "uri": "mongodb://job_application_agent/simulations",
        "name": "Policy Simulations",
        "description": "Access to policy simulation results",
        "mimeType": "application/json"
    },
    {
        "uri": "mongodb://job_application_agent/policy_recommendations",
        "name": "Policy Recommendations",
        "description": "Access to generated policy recommendations",
        "mimeType": "application/json"
    },
    {
        "uri": "mongodb://job_application_agent/team_simulations",
        "name": "Team Simulations",
        "description": "Access to team formation and activity simulation results",
        "mimeType": "application/json"
    },
    {
        "uri": "mongodb://job_application_agent/team_formations",
        "name": "Team Formations",
        "description": "Access to team formation results",
        "mimeType": "application/json"
    },
    {
        "uri": "mongodb://job_application_agent/team_activities",
        "name": "Team Activities",
        "description": "Access to suggested team activities",
        "mimeType": "application/json"
    }
]

# MCP Prompts
MCP_PROMPTS = [
    {
        "name": "policy_simulation_guide",
        "description": "Guide for running effective policy simulations",
        "arguments": [
            {"name": "simulation_type", "description": "Type of simulation", "required": True}
        ]
    }
]

# MCP Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Team Simulation MCP Server", "version": "1.0.0"}

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

        if tool_name == "run_policy_simulation":
            return await run_policy_simulation_tool(arguments)
        elif tool_name == "compare_policy_scenarios":
            return await compare_policy_scenarios_tool(arguments)
        elif tool_name == "generate_policy_recommendations":
            return await generate_policy_recommendations_tool(arguments)
        elif tool_name == "analyze_simulation_trends":
            return await analyze_simulation_trends_tool(arguments)
        elif tool_name == "run_cape_town_simulation":
            return await run_cape_town_simulation_tool(arguments)
        elif tool_name == "get_simulation_history":
            return await get_simulation_history_tool(arguments)
        elif tool_name == "extract_team_skills":
            return await extract_team_skills_tool(arguments)
        elif tool_name == "form_teams":
            return await form_teams_tool(arguments)
        elif tool_name == "suggest_team_activities":
            return await suggest_team_activities_tool(arguments)
        elif tool_name == "create_team_simulation":
            return await create_team_simulation_tool(arguments)
        else:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

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
        if uri == "mongodb://job_application_agent/simulations":
            # Return recent simulations
            simulations = list(db.simulations.find().sort("timestamp", -1).limit(20))
            return {"content": [{"type": "text", "text": json.dumps(simulations, default=str)}]}
        elif uri == "mongodb://job_application_agent/policy_recommendations":
            # Return recent policy recommendations
            recommendations = list(db.policy_recommendations.find().sort("timestamp", -1).limit(20))
            return {"content": [{"type": "text", "text": json.dumps(recommendations, default=str)}]}
        elif uri == "mongodb://job_application_agent/team_simulations":
            # Return recent team simulations
            team_sims = list(db.team_simulations.find().sort("timestamp", -1).limit(20))
            return {"content": [{"type": "text", "text": json.dumps(team_sims, default=str)}]}
        elif uri == "mongodb://job_application_agent/team_formations":
            # Return recent team formations
            formations = list(db.team_formations.find().sort("timestamp", -1).limit(20))
            return {"content": [{"type": "text", "text": json.dumps(formations, default=str)}]}
        elif uri == "mongodb://job_application_agent/team_activities":
            # Return recent team activities
            activities = list(db.team_activities.find().sort("timestamp", -1).limit(20))
            return {"content": [{"type": "text", "text": json.dumps(activities, default=str)}]}
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

# Team simulation functions
def extract_skills_from_resumes(user_ids: List[str]) -> Dict[str, List[str]]:
    """Extract skills from resumes for given user IDs"""
    skills_data = {}

    for user_id in user_ids:
        # Query resume data from database
        resume_doc = db.resumes.find_one({"user_id": user_id}, sort=[("timestamp", -1)])
        if resume_doc and "parsed_data" in resume_doc:
            parsed_data = resume_doc["parsed_data"]
            skills = parsed_data.get("skills", [])
            if isinstance(skills, list):
                skills_data[user_id] = skills
            else:
                # Handle case where skills might be a string or dict
                skills_data[user_id] = [str(skills)] if skills else []
        else:
            skills_data[user_id] = []

    return skills_data

def form_teams_with_clustering(skills_data: Dict[str, List[str]], num_teams: int = 3) -> Dict[str, List[str]]:
    """Form teams using skill synergy clustering"""
    if not skills_data:
        return {}

    # Prepare data for clustering
    user_ids = list(skills_data.keys())
    all_skills = set()
    for skills in skills_data.values():
        all_skills.update(skills)

    all_skills = list(all_skills)

    # Create skill vectors
    mlb = MultiLabelBinarizer(classes=all_skills)
    skill_vectors = mlb.fit_transform(skills_data.values())

    if len(user_ids) < num_teams:
        num_teams = len(user_ids)

    # Perform clustering
    kmeans = KMeans(n_clusters=num_teams, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(skill_vectors)

    # Group users by cluster
    teams = {}
    for i in range(num_teams):
        team_users = [user_ids[j] for j in range(len(user_ids)) if clusters[j] == i]
        teams[f"team_{i+1}"] = team_users

    return teams

def suggest_collaborative_activities(teams: Dict[str, List[str]], cape_town_focus: bool = True) -> Dict[str, List[str]]:
    """Suggest collaborative activities based on team composition and Cape Town issues"""
    activities = {
        "entrepreneurship": [
            "Start a community co-op business",
            "Develop local tech startup",
            "Create digital skills training program",
            "Launch e-commerce platform for local artisans"
        ],
        "community_gardens": [
            "Establish urban farming cooperative",
            "Water conservation garden project",
            "Community seed bank initiative",
            "Sustainable agriculture training"
        ],
        "water_recycling": [
            "Rainwater harvesting system",
            "Greywater recycling project",
            "Water-saving technology development",
            "Community water education program"
        ],
        "crime_prevention": [
            "Neighborhood watch app development",
            "Community safety training workshops",
            "Youth empowerment programs",
            "Local security cooperative"
        ]
    }

    team_activities = {}

    for team_name, members in teams.items():
        # Analyze team skills to suggest relevant activities
        team_skills = []
        for member in members:
            resume_doc = db.resumes.find_one({"user_id": member}, sort=[("timestamp", -1)])
            if resume_doc and "parsed_data" in resume_doc:
                skills = resume_doc["parsed_data"].get("skills", [])
                team_skills.extend(skills)

        # Suggest activities based on skills and Cape Town focus
        suggested_activities = []

        if cape_town_focus:
            # Prioritize water and crime related activities for Cape Town
            if any(skill.lower() in ['engineering', 'technology', 'programming'] for skill in team_skills):
                suggested_activities.extend(activities["water_recycling"][:2])
                suggested_activities.extend(activities["crime_prevention"][:1])

            if any(skill.lower() in ['business', 'marketing', 'management'] for skill in team_skills):
                suggested_activities.extend(activities["entrepreneurship"][:2])

            if any(skill.lower() in ['agriculture', 'biology', 'environmental'] for skill in team_skills):
                suggested_activities.extend(activities["community_gardens"][:2])

            # Add general activities if no specific matches
            if not suggested_activities:
                suggested_activities = activities["entrepreneurship"][:2] + activities["community_gardens"][:1]

        team_activities[team_name] = list(set(suggested_activities))  # Remove duplicates

    return team_activities

# Tool implementations
async def run_policy_simulation_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Run policy simulation"""
    simulation_type = arguments["simulation_type"]
    parameters = arguments.get("parameters", {})
    user_id = arguments.get("user_id")

    try:
        result = run_policy_simulation(simulation_type, parameters)

        if 'error' in result:
            return MCPToolResponse(
                content=[{"type": "text", "text": f"Simulation error: {result['error']}"}],
                isError=True
            )

        # Save simulation result
        sim_doc = {
            "user_id": user_id,
            "simulation_type": simulation_type,
            "parameters": parameters,
            "result": result,
            "timestamp": datetime.now()
        }
        db.simulations.insert_one(sim_doc)

        effectiveness = result.get('final_metrics', {}).get('policy_effectiveness', 0)
        steps = result.get('steps_run', 0)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Policy simulation completed: {simulation_type}, effectiveness {effectiveness:.1f}%, {steps} steps"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error running simulation: {str(e)}"}],
            isError=True
        )

async def compare_policy_scenarios_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Compare policy scenarios"""
    simulation_type = arguments["simulation_type"]
    scenarios = arguments["scenarios"]
    user_id = arguments.get("user_id")

    try:
        # Import the comparison function
        from mesa_abm_simulations import PolicySimulationRunner

        runner = PolicySimulationRunner()
        comparison_result = runner.compare_policies(simulation_type, scenarios)

        # Save comparison
        comp_doc = {
            "user_id": user_id,
            "simulation_type": simulation_type,
            "scenarios": scenarios,
            "comparison": comparison_result,
            "timestamp": datetime.now()
        }
        db.scenario_comparisons.insert_one(comp_doc)

        best_scenario = comparison_result.get('best_scenario', {})
        best_name = best_scenario.get('scenario_name', 'Unknown')

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Scenario comparison completed. Best scenario: {best_name} with {best_scenario.get('final_metrics', {}).get('policy_effectiveness', 0):.1f}% effectiveness"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error comparing scenarios: {str(e)}"}],
            isError=True
        )

async def generate_policy_recommendations_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Generate policy recommendations"""
    simulation_results = arguments["simulation_results"]
    user_id = arguments.get("user_id")

    try:
        recommendations = generate_policy_recommendations(simulation_results)

        # Save recommendations
        rec_doc = {
            "user_id": user_id,
            "simulation_results": simulation_results,
            "recommendations": recommendations,
            "timestamp": datetime.now()
        }
        db.policy_recommendations.insert_one(rec_doc)

        level = recommendations.get('recommendation_level', 'Unknown')
        priority = recommendations.get('implementation_priority', 'Unknown')

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Policy recommendations generated. Level: {level}, Priority: {priority}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error generating recommendations: {str(e)}"}],
            isError=True
        )

async def analyze_simulation_trends_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Analyze simulation trends"""
    simulation_data = arguments["simulation_data"]
    analysis_type = arguments["analysis_type"]
    user_id = arguments.get("user_id")

    try:
        analysis = {}

        if analysis_type == "effectiveness":
            # Analyze policy effectiveness trends
            metrics = simulation_data.get('final_metrics', {})
            effectiveness = metrics.get('policy_effectiveness', 0)

            if effectiveness > 0.8:
                analysis["trend"] = "Highly Effective"
                analysis["insights"] = "Policy shows strong positive impact"
            elif effectiveness > 0.6:
                analysis["trend"] = "Moderately Effective"
                analysis["insights"] = "Policy shows promising results with room for improvement"
            else:
                analysis["trend"] = "Limited Effectiveness"
                analysis["insights"] = "Policy may need significant adjustments"

        elif analysis_type == "trends":
            # Analyze time series trends
            time_series = simulation_data.get('time_series_data', {})
            employed_trend = time_series.get('employed', [])

            if len(employed_trend) > 1:
                start_avg = sum(employed_trend[:5]) / 5
                end_avg = sum(employed_trend[-5:]) / 5
                trend = "Improving" if end_avg > start_avg else "Declining"
                analysis["employment_trend"] = trend
                analysis["change"] = ((end_avg - start_avg) / start_avg) * 100

        # Save analysis
        analysis_doc = {
            "user_id": user_id,
            "simulation_data": simulation_data,
            "analysis_type": analysis_type,
            "analysis": analysis,
            "timestamp": datetime.now()
        }
        db.simulation_analyses.insert_one(analysis_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Simulation trend analysis completed: {analysis_type} - {analysis.get('trend', 'Analysis complete')}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error analyzing trends: {str(e)}"}],
            isError=True
        )

async def run_cape_town_simulation_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Run Cape Town-specific simulation"""
    issue_type = arguments["issue_type"]
    parameters = arguments.get("parameters", {})
    user_id = arguments.get("user_id")

    try:
        if issue_type == "unemployment":
            simulation_type = "cape_town_unemployment"
        elif issue_type == "water_crisis":
            simulation_type = "cape_town_water_crisis"
        else:
            raise ValueError(f"Unknown Cape Town issue type: {issue_type}")

        result = run_policy_simulation(simulation_type, parameters)

        if 'error' in result:
            return MCPToolResponse(
                content=[{"type": "text", "text": f"Cape Town simulation error: {result['error']}"}],
                isError=True
            )

        # Save Cape Town-specific result
        ct_doc = {
            "user_id": user_id,
            "issue_type": issue_type,
            "simulation_type": simulation_type,
            "parameters": parameters,
            "result": result,
            "timestamp": datetime.now()
        }
        db.cape_town_simulations.insert_one(ct_doc)

        effectiveness = result.get('final_metrics', {}).get('policy_effectiveness', 0)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Cape Town {issue_type} simulation completed with {effectiveness:.1f}% effectiveness"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error running Cape Town simulation: {str(e)}"}],
            isError=True
        )

async def get_simulation_history_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Get simulation history"""
    user_id = arguments["user_id"]
    limit = arguments.get("limit", 10)

    try:
        # Get user's simulation history
        history = list(db.simulations.find(
            {"user_id": user_id},
            {"_id": 0, "simulation_type": 1, "timestamp": 1, "result.final_metrics.policy_effectiveness": 1}
        ).sort("timestamp", -1).limit(limit))

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Found {len(history)} simulation runs for user {user_id}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error getting simulation history: {str(e)}"}],
            isError=True
        )

async def extract_team_skills_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Extract skills from team members' resumes"""
    user_ids = arguments["user_ids"]
    requesting_user = arguments.get("user_id")

    try:
        skills_data = extract_skills_from_resumes(user_ids)

        # Save skill extraction results
        skill_doc = {
            "requesting_user": requesting_user,
            "user_ids": user_ids,
            "skills_data": skills_data,
            "timestamp": datetime.now()
        }
        db.team_skills.insert_one(skill_doc)

        total_skills = sum(len(skills) for skills in skills_data.values())
        users_with_skills = sum(1 for skills in skills_data.values() if skills)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Extracted skills from {len(user_ids)} users. {users_with_skills} users have skills data, total {total_skills} skills identified."
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error extracting team skills: {str(e)}"}],
            isError=True
        )

async def form_teams_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Form teams using skill synergy clustering"""
    user_ids = arguments["user_ids"]
    num_teams = arguments.get("num_teams", 3)
    requesting_user = arguments.get("user_id")

    try:
        # First extract skills
        skills_data = extract_skills_from_resumes(user_ids)

        if not skills_data:
            return MCPToolResponse(
                content=[{"type": "text", "text": "No skill data available for team formation"}],
                isError=True
            )

        # Form teams
        teams = form_teams_with_clustering(skills_data, num_teams)

        # Save team formation results
        team_doc = {
            "requesting_user": requesting_user,
            "user_ids": user_ids,
            "num_teams": num_teams,
            "teams": teams,
            "skills_data": skills_data,
            "timestamp": datetime.now()
        }
        db.team_formations.insert_one(team_doc)

        team_summary = ", ".join([f"{team}: {len(members)} members" for team, members in teams.items()])

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Formed {len(teams)} teams from {len(user_ids)} users: {team_summary}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error forming teams: {str(e)}"}],
            isError=True
        )

async def suggest_team_activities_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Suggest collaborative activities for teams"""
    teams = arguments["teams"]
    cape_town_focus = arguments.get("cape_town_focus", True)
    requesting_user = arguments.get("user_id")

    try:
        activities = suggest_collaborative_activities(teams, cape_town_focus)

        # Save activity suggestions
        activity_doc = {
            "requesting_user": requesting_user,
            "teams": teams,
            "cape_town_focus": cape_town_focus,
            "activities": activities,
            "timestamp": datetime.now()
        }
        db.team_activities.insert_one(activity_doc)

        total_activities = sum(len(acts) for acts in activities.values())

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Suggested {total_activities} collaborative activities for {len(teams)} teams, focusing on Cape Town issues: {', '.join(list(activities.keys()))}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error suggesting activities: {str(e)}"}],
            isError=True
        )

async def create_team_simulation_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Create and run complete team formation simulation"""
    user_ids = arguments["user_ids"]
    num_teams = arguments.get("num_teams", 3)
    cape_town_focus = arguments.get("cape_town_focus", True)
    requesting_user = arguments.get("user_id")

    try:
        # Extract skills
        skills_data = extract_skills_from_resumes(user_ids)

        if not skills_data:
            return MCPToolResponse(
                content=[{"type": "text", "text": "No skill data available for team simulation"}],
                isError=True
            )

        # Form teams
        teams = form_teams_with_clustering(skills_data, num_teams)

        # Suggest activities
        activities = suggest_collaborative_activities(teams, cape_town_focus)

        # Save complete simulation
        simulation_doc = {
            "requesting_user": requesting_user,
            "user_ids": user_ids,
            "num_teams": num_teams,
            "cape_town_focus": cape_town_focus,
            "skills_data": skills_data,
            "teams": teams,
            "activities": activities,
            "timestamp": datetime.now()
        }
        db.team_simulations.insert_one(simulation_doc)

        # Create comprehensive response
        response_text = f"Team simulation completed for {len(user_ids)} users:\n"
        response_text += f"- Formed {len(teams)} teams\n"
        for team_name, members in teams.items():
            response_text += f"- {team_name}: {len(members)} members\n"
        response_text += f"- Suggested activities addressing Cape Town's unemployment, water scarcity, and crime issues"

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": response_text
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error in team simulation: {str(e)}"}],
            isError=True
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)