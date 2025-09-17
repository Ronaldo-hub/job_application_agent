"""
FastAPI MCP Server for Job Search Service
Implements MCP protocol for job searching across multiple APIs
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
from job_discovery_matching.job_search import search_jobs_async, remove_duplicates, apply_filters

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Job Search MCP Server",
    description="MCP server for job searching across multiple APIs",
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
        "name": "search_jobs_multi_api",
        "description": "Search for jobs across multiple APIs (Adzuna, Careerjet, Upwork, etc.)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keywords": {"type": "string", "description": "Job search keywords"},
                "location": {"type": "string", "description": "Job location"},
                "max_age_days": {"type": "integer", "description": "Maximum job age in days", "default": 30},
                "salary_min": {"type": "integer", "description": "Minimum salary"},
                "salary_max": {"type": "integer", "description": "Maximum salary"},
                "user_id": {"type": "string", "description": "User identifier for logging"}
            },
            "required": ["keywords"]
        }
    },
    {
        "name": "filter_jobs_by_criteria",
        "description": "Filter job results by location, date, and other criteria",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobs": {"type": "array", "description": "List of job data"},
                "location": {"type": "string", "description": "Filter by location"},
                "max_age_days": {"type": "integer", "description": "Filter by maximum age in days"},
                "salary_min": {"type": "integer", "description": "Filter by minimum salary"},
                "salary_max": {"type": "integer", "description": "Filter by maximum salary"}
            },
            "required": ["jobs"]
        }
    },
    {
        "name": "deduplicate_jobs",
        "description": "Remove duplicate jobs based on title and company",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobs": {"type": "array", "description": "List of job data to deduplicate"}
            },
            "required": ["jobs"]
        }
    },
    {
        "name": "analyze_job_market_trends",
        "description": "Analyze job market trends from search results",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobs": {"type": "array", "description": "List of job data"},
                "keywords": {"type": "string", "description": "Search keywords used"}
            },
            "required": ["jobs", "keywords"]
        }
    },
    {
        "name": "get_job_search_history",
        "description": "Get user's job search history",
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
        "uri": "mongodb://job_application_agent/job_searches",
        "name": "Job Search Results",
        "description": "Access to job search results and history",
        "mimeType": "application/json"
    },
    {
        "uri": "mongodb://job_application_agent/job_market_data",
        "name": "Job Market Data",
        "description": "Access to aggregated job market data",
        "mimeType": "application/json"
    }
]

# MCP Prompts
MCP_PROMPTS = [
    {
        "name": "job_search_strategy",
        "description": "Strategy for effective job searching",
        "arguments": [
            {"name": "keywords", "description": "Job search keywords", "required": True},
            {"name": "location", "description": "Target location", "required": False}
        ]
    }
]

# MCP Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Job Search MCP Server", "version": "1.0.0"}

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

        if tool_name == "search_jobs_multi_api":
            return await search_jobs_multi_api_tool(arguments)
        elif tool_name == "filter_jobs_by_criteria":
            return await filter_jobs_by_criteria_tool(arguments)
        elif tool_name == "deduplicate_jobs":
            return await deduplicate_jobs_tool(arguments)
        elif tool_name == "analyze_job_market_trends":
            return await analyze_job_market_trends_tool(arguments)
        elif tool_name == "get_job_search_history":
            return await get_job_search_history_tool(arguments)
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
        if uri == "mongodb://job_application_agent/job_searches":
            # Return recent job search results
            searches = list(db.job_searches.find().sort("timestamp", -1).limit(20))
            return {"content": [{"type": "text", "text": json.dumps(searches, default=str)}]}
        elif uri == "mongodb://job_application_agent/job_market_data":
            # Return aggregated job market data
            market_data = list(db.job_market_data.find().sort("timestamp", -1).limit(10))
            return {"content": [{"type": "text", "text": json.dumps(market_data, default=str)}]}
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
async def search_jobs_multi_api_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Search jobs across multiple APIs"""
    keywords = arguments["keywords"]
    location = arguments.get("location")
    max_age_days = arguments.get("max_age_days", 30)
    salary_min = arguments.get("salary_min")
    salary_max = arguments.get("salary_max")
    user_id = arguments.get("user_id")

    try:
        search_params = {
            'keywords': keywords,
            'location': location,
            'max_age_days': max_age_days,
            'salary_min': salary_min,
            'salary_max': salary_max
        }

        jobs = await search_jobs_async(search_params)

        # Save search results to MongoDB
        search_doc = {
            "user_id": user_id,
            "keywords": keywords,
            "location": location,
            "max_age_days": max_age_days,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "results_count": len(jobs),
            "timestamp": datetime.now(),
            "jobs": jobs[:50]  # Limit stored jobs to prevent large documents
        }
        db.job_searches.insert_one(search_doc)

        # Update job market data
        await update_job_market_data(keywords, location, jobs)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Found {len(jobs)} jobs for '{keywords}' across multiple APIs"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error searching jobs: {str(e)}"}],
            isError=True
        )

async def filter_jobs_by_criteria_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Filter jobs by criteria"""
    jobs = arguments["jobs"]
    location = arguments.get("location")
    max_age_days = arguments.get("max_age_days")
    salary_min = arguments.get("salary_min")
    salary_max = arguments.get("salary_max")

    try:
        filtered_jobs = apply_filters(jobs, location or "", max_age_days or 30)

        # Apply additional salary filters
        if salary_min or salary_max:
            salary_filtered = []
            for job in filtered_jobs:
                salary = job.get('salary', '')
                if salary:
                    try:
                        # Extract numeric salary (simplified)
                        salary_num = float(''.join(filter(str.isdigit, str(salary))))
                        if ((not salary_min or salary_num >= salary_min) and
                            (not salary_max or salary_num <= salary_max)):
                            salary_filtered.append(job)
                    except:
                        salary_filtered.append(job)  # Keep if can't parse
                else:
                    salary_filtered.append(job)  # Keep if no salary info
            filtered_jobs = salary_filtered

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Filtered {len(jobs)} jobs down to {len(filtered_jobs)} based on criteria"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error filtering jobs: {str(e)}"}],
            isError=True
        )

async def deduplicate_jobs_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Remove duplicate jobs"""
    jobs = arguments["jobs"]

    try:
        deduplicated_jobs = remove_duplicates(jobs)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Deduplicated {len(jobs)} jobs down to {len(deduplicated_jobs)} unique jobs"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error deduplicating jobs: {str(e)}"}],
            isError=True
        )

async def analyze_job_market_trends_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Analyze job market trends"""
    jobs = arguments["jobs"]
    keywords = arguments["keywords"]

    try:
        # Analyze trends
        trends = {
            "total_jobs": len(jobs),
            "unique_companies": len(set(job.get('company', '') for job in jobs if job.get('company'))),
            "locations": {},
            "salary_ranges": [],
            "common_requirements": {},
            "posting_frequency": "daily"  # Simplified
        }

        # Count locations
        for job in jobs:
            location = job.get('location', 'Unknown')
            trends["locations"][location] = trends["locations"].get(location, 0) + 1

        # Extract salary info
        for job in jobs:
            salary = job.get('salary', '')
            if salary:
                trends["salary_ranges"].append(str(salary))

        # Analyze requirements
        all_requirements = []
        for job in jobs:
            requirements = job.get('requirements', [])
            all_requirements.extend(requirements)

        for req in all_requirements:
            trends["common_requirements"][req] = trends["common_requirements"].get(req, 0) + 1

        # Save market analysis
        analysis_doc = {
            "keywords": keywords,
            "analysis": trends,
            "timestamp": datetime.now()
        }
        db.job_market_data.insert_one(analysis_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Job market analysis for '{keywords}': {len(jobs)} jobs, {trends['unique_companies']} companies, top locations: {list(trends['locations'].keys())[:3]}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error analyzing trends: {str(e)}"}],
            isError=True
        )

async def get_job_search_history_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Get job search history"""
    user_id = arguments["user_id"]

    try:
        # Get user's search history
        history = list(db.job_searches.find(
            {"user_id": user_id},
            {"_id": 0, "keywords": 1, "location": 1, "results_count": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(10))

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Found {len(history)} recent job searches for user {user_id}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error getting search history: {str(e)}"}],
            isError=True
        )

async def update_job_market_data(keywords: str, location: str, jobs: List[Dict]):
    """Update aggregated job market data"""
    try:
        # Aggregate data for market insights
        market_doc = {
            "keywords": keywords,
            "location": location,
            "total_jobs": len(jobs),
            "avg_salary": None,  # Could be calculated
            "top_companies": list(set(job.get('company', '') for job in jobs[:10] if job.get('company'))),
            "timestamp": datetime.now()
        }

        # Calculate average salary if available
        salaries = []
        for job in jobs:
            salary = job.get('salary', '')
            if salary:
                try:
                    # Extract numeric value (simplified)
                    salary_num = float(''.join(filter(str.isdigit, str(salary))))
                    salaries.append(salary_num)
                except:
                    pass

        if salaries:
            market_doc["avg_salary"] = sum(salaries) / len(salaries)

        db.job_market_data.insert_one(market_doc)

    except Exception as e:
        logger.error(f"Error updating job market data: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)