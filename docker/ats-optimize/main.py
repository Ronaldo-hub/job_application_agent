"""
FastAPI MCP Server for ATS Optimize Service
Implements MCP protocol for ATS-optimized resume generation and auditing
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
from resume_doc_processing.resume_tool import generate_resume, calculate_fit_score, load_master_resume
from resume_doc_processing.audit_tool import audit_resume

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ATS Optimize MCP Server",
    description="MCP server for ATS-optimized resume generation and auditing",
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
        "name": "generate_ats_resume",
        "description": "Generate ATS-optimized resume for a specific job",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "job_data": {"type": "object", "description": "Job details for optimization"},
                "format": {"type": "string", "description": "Output format (word, pdf, both)", "default": "both"}
            },
            "required": ["user_id", "job_data"]
        }
    },
    {
        "name": "audit_resume_for_hallucinations",
        "description": "Audit generated resume for accuracy and detect hallucinations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "resume_data": {"type": "object", "description": "Resume data to audit"}
            },
            "required": ["user_id", "resume_data"]
        }
    },
    {
        "name": "calculate_job_fit_score",
        "description": "Calculate fit score between resume and job requirements",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "job_data": {"type": "object", "description": "Job details"},
                "resume_data": {"type": "object", "description": "Resume data (optional, uses master resume if not provided)"}
            },
            "required": ["user_id", "job_data"]
        }
    },
    {
        "name": "optimize_resume_keywords",
        "description": "Optimize resume with job-specific keywords",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "job_data": {"type": "object", "description": "Job details with keywords"},
                "resume_data": {"type": "object", "description": "Current resume data"}
            },
            "required": ["user_id", "job_data", "resume_data"]
        }
    },
    {
        "name": "generate_resume_variants",
        "description": "Generate multiple resume variants for different job applications",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "job_list": {"type": "array", "description": "List of job data"},
                "max_variants": {"type": "integer", "description": "Maximum number of variants to generate", "default": 3}
            },
            "required": ["user_id", "job_list"]
        }
    },
    {
        "name": "analyze_resume_effectiveness",
        "description": "Analyze resume effectiveness for ATS systems",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "resume_content": {"type": "string", "description": "Resume content to analyze"},
                "job_requirements": {"type": "array", "description": "Job requirements to check against"}
            },
            "required": ["user_id", "resume_content"]
        }
    }
]

# MCP Resources
MCP_RESOURCES = [
    {
        "uri": "mongodb://job_application_agent/generated_resumes",
        "name": "Generated Resumes",
        "description": "Access to ATS-optimized generated resumes",
        "mimeType": "application/json"
    },
    {
        "uri": "mongodb://job_application_agent/resume_audits",
        "name": "Resume Audits",
        "description": "Access to resume audit results",
        "mimeType": "application/json"
    }
]

# MCP Prompts
MCP_PROMPTS = [
    {
        "name": "ats_optimization_guide",
        "description": "Guide for ATS optimization best practices",
        "arguments": [
            {"name": "job_title", "description": "Target job title", "required": True}
        ]
    }
]

# MCP Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "ATS Optimize MCP Server", "version": "1.0.0"}

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

        if tool_name == "generate_ats_resume":
            return await generate_ats_resume_tool(arguments)
        elif tool_name == "audit_resume_for_hallucinations":
            return await audit_resume_for_hallucinations_tool(arguments)
        elif tool_name == "calculate_job_fit_score":
            return await calculate_job_fit_score_tool(arguments)
        elif tool_name == "optimize_resume_keywords":
            return await optimize_resume_keywords_tool(arguments)
        elif tool_name == "generate_resume_variants":
            return await generate_resume_variants_tool(arguments)
        elif tool_name == "analyze_resume_effectiveness":
            return await analyze_resume_effectiveness_tool(arguments)
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
        if uri == "mongodb://job_application_agent/generated_resumes":
            # Return recent generated resumes
            resumes = list(db.generated_resumes.find().sort("timestamp", -1).limit(20))
            return {"content": [{"type": "text", "text": json.dumps(resumes, default=str)}]}
        elif uri == "mongodb://job_application_agent/resume_audits":
            # Return recent resume audits
            audits = list(db.resume_audits.find().sort("timestamp", -1).limit(20))
            return {"content": [{"type": "text", "text": json.dumps(audits, default=str)}]}
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
async def generate_ats_resume_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Generate ATS-optimized resume"""
    user_id = arguments["user_id"]
    job_data = arguments["job_data"]
    format_type = arguments.get("format", "both")

    try:
        resume = generate_resume(job_data)

        if 'error' in resume:
            return MCPToolResponse(
                content=[{"type": "text", "text": f"Error generating resume: {resume['error']}"}],
                isError=True
            )

        # Save to database
        resume_doc = {
            "user_id": user_id,
            "job_title": job_data.get('title', ''),
            "company": job_data.get('company', ''),
            "fit_score": resume.get('fit_score', 0),
            "content": resume.get('content', ''),
            "word_file": resume.get('word_file', ''),
            "pdf_file": resume.get('pdf_file', ''),
            "format": format_type,
            "timestamp": datetime.now()
        }
        db.generated_resumes.insert_one(resume_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"ATS-optimized resume generated for {job_data.get('title', 'Unknown')} with fit score {resume.get('fit_score', 0):.1f}%"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error generating ATS resume: {str(e)}"}],
            isError=True
        )

async def audit_resume_for_hallucinations_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Audit resume for hallucinations"""
    user_id = arguments["user_id"]
    resume_data = arguments["resume_data"]

    try:
        audit_result = audit_resume(resume_data)

        # Save audit result
        audit_doc = {
            "user_id": user_id,
            "audit_result": audit_result,
            "timestamp": datetime.now()
        }
        db.resume_audits.insert_one(audit_doc)

        audit_info = audit_result.get('audit_result', {})
        accuracy = audit_info.get('accuracy_score', 0)
        approved = audit_info.get('approved', False)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Resume audit completed. Accuracy: {accuracy}%. Approved: {approved}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error auditing resume: {str(e)}"}],
            isError=True
        )

async def calculate_job_fit_score_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Calculate job fit score"""
    user_id = arguments["user_id"]
    job_data = arguments["job_data"]
    resume_data = arguments.get("resume_data")

    try:
        if not resume_data:
            resume_data = load_master_resume()

        fit_score = calculate_fit_score(resume_data, job_data)

        # Save fit analysis
        fit_doc = {
            "user_id": user_id,
            "job_title": job_data.get('title', ''),
            "company": job_data.get('company', ''),
            "fit_score": fit_score,
            "timestamp": datetime.now()
        }
        db.fit_analyses.insert_one(fit_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Job fit score: {fit_score:.1f}% for {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error calculating fit score: {str(e)}"}],
            isError=True
        )

async def optimize_resume_keywords_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Optimize resume with job-specific keywords"""
    user_id = arguments["user_id"]
    job_data = arguments["job_data"]
    resume_data = arguments["resume_data"]

    try:
        # Extract job keywords
        job_keywords = set()
        if 'requirements' in job_data:
            job_keywords.update(job_data['requirements'])
        if 'skills' in job_data:
            job_keywords.update(job_data['skills'])

        # Check current resume keywords
        resume_keywords = set()
        if 'skills' in resume_data:
            resume_keywords.update(resume_data['skills'])

        # Find missing keywords
        missing_keywords = job_keywords - resume_keywords

        optimization_suggestions = []
        if missing_keywords:
            optimization_suggestions.append(f"Add these keywords to skills section: {', '.join(list(missing_keywords)[:5])}")

        # Suggest keyword integration in summary
        if 'summary' in resume_data and resume_data['summary']:
            summary_keywords = [kw for kw in job_keywords if kw.lower() in resume_data['summary'].lower()]
            if len(summary_keywords) < 3:
                optimization_suggestions.append("Incorporate more job keywords into professional summary")

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Resume optimization analysis complete. Found {len(missing_keywords)} missing keywords. Suggestions: {'; '.join(optimization_suggestions)}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error optimizing keywords: {str(e)}"}],
            isError=True
        )

async def generate_resume_variants_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Generate multiple resume variants"""
    user_id = arguments["user_id"]
    job_list = arguments["job_list"]
    max_variants = arguments.get("max_variants", 3)

    try:
        variants = []
        for i, job_data in enumerate(job_list[:max_variants]):
            resume = generate_resume(job_data)
            if 'error' not in resume:
                variants.append({
                    "variant": i + 1,
                    "job_title": job_data.get('title', ''),
                    "fit_score": resume.get('fit_score', 0),
                    "content": resume.get('content', '')
                })

        # Save variants
        variants_doc = {
            "user_id": user_id,
            "variants_count": len(variants),
            "variants": variants,
            "timestamp": datetime.now()
        }
        db.resume_variants.insert_one(variants_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Generated {len(variants)} resume variants for {len(job_list)} jobs"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error generating resume variants: {str(e)}"}],
            isError=True
        )

async def analyze_resume_effectiveness_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Analyze resume effectiveness for ATS"""
    user_id = arguments["user_id"]
    resume_content = arguments["resume_content"]
    job_requirements = arguments.get("job_requirements", [])

    try:
        # Basic ATS effectiveness analysis
        analysis = {
            "keyword_density": 0,
            "format_score": 0,
            "readability_score": 0,
            "suggestions": []
        }

        # Check keyword presence
        content_lower = resume_content.lower()
        matched_keywords = 0
        for req in job_requirements:
            if req.lower() in content_lower:
                matched_keywords += 1

        if job_requirements:
            analysis["keyword_density"] = (matched_keywords / len(job_requirements)) * 100

        # Basic format checks
        if "skills" in content_lower and "experience" in content_lower:
            analysis["format_score"] = 80
            analysis["suggestions"].append("Good section structure")
        else:
            analysis["format_score"] = 60
            analysis["suggestions"].append("Consider adding clear section headers")

        # Readability check (simplified)
        word_count = len(resume_content.split())
        if word_count < 300:
            analysis["readability_score"] = 70
            analysis["suggestions"].append("Resume might be too concise")
        elif word_count > 800:
            analysis["readability_score"] = 60
            analysis["suggestions"].append("Consider condensing content")
        else:
            analysis["readability_score"] = 85
            analysis["suggestions"].append("Good content length")

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"ATS effectiveness analysis: Keywords {analysis['keyword_density']:.1f}%, Format {analysis['format_score']}%, Readability {analysis['readability_score']}%"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error analyzing effectiveness: {str(e)}"}],
            isError=True
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)