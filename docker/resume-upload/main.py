"""
FastAPI MCP Server for Resume Upload Service
Implements MCP protocol for resume parsing and processing
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymongo
from pymongo import MongoClient

# Import existing logic
from resume_doc_processing.resume_parser import parse_resume_file, parse_pdf_resume, parse_docx_resume, merge_resume_data
from resume_doc_processing.resume_tool import load_master_resume
from compliance_monitoring_testing import popia_compliance

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Resume Upload MCP Server",
    description="MCP server for resume parsing and processing",
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
        "name": "parse_resume_file",
        "description": "Parse a resume file (PDF or DOCX) and extract structured data",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "file_path": {"type": "string", "description": "Path to resume file"},
                "anonymize": {"type": "boolean", "description": "Whether to anonymize personal data", "default": True}
            },
            "required": ["user_id", "file_path"]
        }
    },
    {
        "name": "extract_resume_sections",
        "description": "Extract specific sections from parsed resume",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "sections": {"type": "array", "description": "Sections to extract", "items": {"type": "string"}},
                "resume_data": {"type": "object", "description": "Parsed resume data"}
            },
            "required": ["user_id", "sections"]
        }
    },
    {
        "name": "merge_resume_data",
        "description": "Merge new resume data with existing master resume",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "new_resume_data": {"type": "object", "description": "New resume data to merge"},
                "existing_resume_data": {"type": "object", "description": "Existing resume data"}
            },
            "required": ["user_id", "new_resume_data"]
        }
    },
    {
        "name": "validate_resume_completeness",
        "description": "Validate if resume has all required sections",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "resume_data": {"type": "object", "description": "Resume data to validate"}
            },
            "required": ["user_id", "resume_data"]
        }
    },
    {
        "name": "anonymize_resume_data",
        "description": "Anonymize personal information in resume data (POPIA compliance)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "resume_data": {"type": "object", "description": "Resume data to anonymize"}
            },
            "required": ["user_id", "resume_data"]
        }
    }
]

# MCP Resources
MCP_RESOURCES = [
    {
        "uri": "mongodb://job_application_agent/resumes",
        "name": "Parsed Resumes",
        "description": "Access to parsed resume data",
        "mimeType": "application/json"
    },
    {
        "uri": "mongodb://job_application_agent/master_resumes",
        "name": "Master Resumes",
        "description": "Access to master resume data",
        "mimeType": "application/json"
    }
]

# MCP Prompts
MCP_PROMPTS = [
    {
        "name": "resume_parsing_guidance",
        "description": "Guidance for resume parsing and data extraction",
        "arguments": [
            {"name": "file_type", "description": "Type of resume file", "required": True}
        ]
    }
]

# MCP Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Resume Upload MCP Server", "version": "1.0.0"}

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

        if tool_name == "parse_resume_file":
            return await parse_resume_file_tool(arguments)
        elif tool_name == "extract_resume_sections":
            return await extract_resume_sections_tool(arguments)
        elif tool_name == "merge_resume_data":
            return await merge_resume_data_tool(arguments)
        elif tool_name == "validate_resume_completeness":
            return await validate_resume_completeness_tool(arguments)
        elif tool_name == "anonymize_resume_data":
            return await anonymize_resume_data_tool(arguments)
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
        if uri == "mongodb://job_application_agent/resumes":
            # Return recent parsed resumes (anonymized)
            resumes = list(db.resumes.find({}, {"_id": 0, "personal_info": 0}).sort("timestamp", -1).limit(10))
            return {"content": [{"type": "text", "text": json.dumps(resumes, default=str)}]}
        elif uri == "mongodb://job_application_agent/master_resumes":
            # Return master resumes (anonymized)
            master_resumes = list(db.master_resumes.find({}, {"_id": 0, "personal_info": 0}))
            return {"content": [{"type": "text", "text": json.dumps(master_resumes, default=str)}]}
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

# File upload endpoint
@app.post("/upload-resume")
async def upload_resume(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    anonymize: bool = Form(True)
):
    """Upload and parse resume file"""
    try:
        # Validate file type
        if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

        # Save file temporarily
        file_path = f"/tmp/{user_id}_{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Parse resume
        parsed_resume = parse_resume_file(file_path, user_id, anonymize)

        # Save to MongoDB
        resume_doc = {
            "user_id": user_id,
            "filename": file.filename,
            "parsed_data": parsed_resume,
            "timestamp": datetime.now(),
            "anonymized": anonymize
        }
        db.resumes.insert_one(resume_doc)

        # Clean up temp file
        os.remove(file_path)

        return {
            "message": "Resume parsed successfully",
            "user_id": user_id,
            "sections_extracted": list(parsed_resume.keys()),
            "anonymized": anonymize
        }

    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Tool implementations
async def parse_resume_file_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Parse resume file tool"""
    user_id = arguments["user_id"]
    file_path = arguments["file_path"]
    anonymize = arguments.get("anonymize", True)

    try:
        parsed_resume = parse_resume_file(file_path, user_id, anonymize)

        # Save to database
        resume_doc = {
            "user_id": user_id,
            "file_path": file_path,
            "parsed_data": parsed_resume,
            "timestamp": datetime.now(),
            "anonymized": anonymize
        }
        db.resumes.insert_one(resume_doc)

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Resume parsed successfully for user {user_id}. Extracted sections: {', '.join(parsed_resume.keys())}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error parsing resume: {str(e)}"}],
            isError=True
        )

async def extract_resume_sections_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Extract specific sections from resume"""
    user_id = arguments["user_id"]
    sections = arguments["sections"]
    resume_data = arguments.get("resume_data")

    try:
        if not resume_data:
            # Try to get from database
            resume_doc = db.resumes.find_one({"user_id": user_id}, sort=[("timestamp", -1)])
            if resume_doc:
                resume_data = resume_doc["parsed_data"]
            else:
                raise HTTPException(status_code=404, detail=f"No resume data found for user {user_id}")

        extracted_data = {}
        for section in sections:
            if section in resume_data:
                extracted_data[section] = resume_data[section]

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Extracted sections {', '.join(sections)} for user {user_id}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error extracting sections: {str(e)}"}],
            isError=True
        )

async def merge_resume_data_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Merge resume data tool"""
    user_id = arguments["user_id"]
    new_resume_data = arguments["new_resume_data"]
    existing_resume_data = arguments.get("existing_resume_data")

    try:
        if not existing_resume_data:
            # Try to load master resume
            existing_resume_data = load_master_resume()

        merged_resume = merge_resume_data(existing_resume_data, new_resume_data)

        # Save merged resume
        master_doc = {
            "user_id": user_id,
            "resume_data": merged_resume,
            "last_updated": datetime.now()
        }
        db.master_resumes.replace_one(
            {"user_id": user_id},
            master_doc,
            upsert=True
        )

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": f"Resume data merged successfully for user {user_id}"
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error merging resume data: {str(e)}"}],
            isError=True
        )

async def validate_resume_completeness_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Validate resume completeness"""
    user_id = arguments["user_id"]
    resume_data = arguments["resume_data"]

    try:
        required_sections = ["personal_info", "summary", "skills", "experience", "education"]
        missing_sections = []

        for section in required_sections:
            if section not in resume_data or not resume_data[section]:
                missing_sections.append(section)

        completeness_score = ((len(required_sections) - len(missing_sections)) / len(required_sections)) * 100

        result_text = f"Resume completeness: {completeness_score:.1f}%"
        if missing_sections:
            result_text += f". Missing sections: {', '.join(missing_sections)}"

        return MCPToolResponse(
            content=[{
                "type": "text",
                "text": result_text
            }]
        )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error validating resume: {str(e)}"}],
            isError=True
        )

async def anonymize_resume_data_tool(arguments: Dict[str, Any]) -> MCPToolResponse:
    """Anonymize resume data"""
    user_id = arguments["user_id"]
    resume_data = arguments["resume_data"]

    try:
        if popia_compliance:
            anonymized_resume, mapping_dict = popia_compliance.anonymize_user_data(resume_data)

            # Audit the anonymization
            popia_compliance.audit_data_processing(
                user_id,
                'resume_anonymization',
                ['personal_info']
            )

            # Save anonymized version
            anon_doc = {
                "user_id": user_id,
                "original_resume": resume_data,
                "anonymized_resume": anonymized_resume,
                "anonymization_mapping": mapping_dict,
                "timestamp": datetime.now()
            }
            db.anonymized_resumes.insert_one(anon_doc)

            return MCPToolResponse(
                content=[{
                    "type": "text",
                    "text": f"Resume data anonymized for user {user_id} (POPIA compliant)"
                }]
            )
        else:
            return MCPToolResponse(
                content=[{"type": "text", "text": "POPIA compliance module not available"}],
                isError=True
            )

    except Exception as e:
        return MCPToolResponse(
            content=[{"type": "text", "text": f"Error anonymizing resume: {str(e)}"}],
            isError=True
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)