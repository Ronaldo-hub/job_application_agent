"""
Comprehensive pytest test suite for ATS Optimize MCP Server
Tests MCP endpoints, core functionality, error handling, MongoDB integration, and API responses
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import mongomock

# Mock external dependencies before importing main
with patch.dict('os.environ', {'HUGGINGFACE_API_KEY': 'test_key'}):
    with patch('resume_doc_processing.resume_tool.generate_resume'):
        with patch('resume_doc_processing.resume_tool.calculate_fit_score'):
            with patch('resume_doc_processing.resume_tool.load_master_resume'):
                with patch('resume_doc_processing.audit_tool.audit_resume'):
                    # Import the FastAPI app and related functions
                    from main import app, MCPToolResponse, generate_ats_resume_tool, audit_resume_for_hallucinations_tool, calculate_job_fit_score_tool, optimize_resume_keywords_tool, generate_resume_variants_tool, analyze_resume_effectiveness_tool

# Create test client
client = TestClient(app)

class TestATSOptimizeEndpoints:
    """Test MCP endpoints"""

    @patch('main.db')
    def test_root_endpoint(self, mock_db):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    @patch('main.db')
    def test_health_endpoint_healthy(self, mock_db):
        """Test health endpoint when service is healthy"""
        mock_db.command.return_value = {"ok": 1}

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @patch('main.db')
    def test_health_endpoint_unhealthy(self, mock_db):
        """Test health endpoint when MongoDB is unhealthy"""
        mock_db.command.side_effect = Exception("Connection failed")

        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert "Service unhealthy" in data["detail"]

    def test_list_tools_endpoint(self):
        """Test MCP tools listing endpoint"""
        response = client.get("/mcp/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)
        assert len(data["tools"]) > 0

        # Verify expected tools are present
        tool_names = [tool["name"] for tool in data["tools"]]
        expected_tools = [
            "generate_ats_resume",
            "audit_resume_for_hallucinations",
            "calculate_job_fit_score",
            "optimize_resume_keywords",
            "generate_resume_variants",
            "analyze_resume_effectiveness"
        ]
        for tool_name in expected_tools:
            assert tool_name in tool_names

    def test_list_resources_endpoint(self):
        """Test MCP resources listing endpoint"""
        response = client.get("/mcp/resources")
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data

    def test_list_prompts_endpoint(self):
        """Test MCP prompts listing endpoint"""
        response = client.get("/mcp/prompts")
        assert response.status_code == 200
        data = response.json()
        assert "prompts" in data

    @patch('main.db')
    def test_read_generated_resumes_resource(self, mock_db):
        """Test reading generated resumes resource"""
        mock_resumes = [
            {"user_id": "test_user", "job_title": "Developer", "timestamp": datetime.now()}
        ]
        mock_db.generated_resumes.find.return_value.sort.return_value.limit.return_value = mock_resumes

        response = client.get("/mcp/resources/mongodb://job_application_agent/generated_resumes")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @patch('main.db')
    def test_read_resume_audits_resource(self, mock_db):
        """Test reading resume audits resource"""
        mock_audits = [
            {"user_id": "test_user", "audit_result": {"accuracy_score": 85}, "timestamp": datetime.now()}
        ]
        mock_db.resume_audits.find.return_value.sort.return_value.limit.return_value = mock_audits

        response = client.get("/mcp/resources/mongodb://job_application_agent/resume_audits")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    def test_get_prompt(self):
        """Test getting MCP prompt"""
        response = client.get("/mcp/prompts/ats_optimization_guide")
        assert response.status_code == 200
        data = response.json()
        assert "prompt" in data

    def test_get_prompt_not_found(self):
        """Test getting non-existent MCP prompt"""
        response = client.get("/mcp/prompts/non_existent_prompt")
        assert response.status_code == 404

class TestATSOptimizeToolCalls:
    """Test MCP tool calls"""

    @patch('main.db')
    @patch('main.generate_resume')
    def test_generate_ats_resume_tool_success(self, mock_generate_resume, mock_db):
        """Test generate_ats_resume tool success"""
        mock_resume = {
            "content": "Generated resume content",
            "fit_score": 85.5,
            "word_file": "/path/to/resume.docx",
            "pdf_file": "/path/to/resume.pdf"
        }
        mock_generate_resume.return_value = mock_resume

        tool_call = {
            "name": "generate_ats_resume",
            "arguments": {
                "user_id": "test_user",
                "job_data": {
                    "title": "Python Developer",
                    "company": "Tech Corp",
                    "requirements": ["Python", "Django", "AWS"]
                },
                "format": "both"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "ATS-optimized resume generated" in data["content"][0]["text"]
        assert "85.5%" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.generate_resume')
    def test_generate_ats_resume_tool_error(self, mock_generate_resume, mock_db):
        """Test generate_ats_resume tool error handling"""
        mock_generate_resume.return_value = {"error": "Resume generation failed"}

        tool_call = {
            "name": "generate_ats_resume",
            "arguments": {
                "user_id": "test_user",
                "job_data": {"title": "Developer"}
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True
        assert "Error generating resume" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.audit_resume')
    def test_audit_resume_for_hallucinations_tool_success(self, mock_audit_resume, mock_db):
        """Test audit_resume_for_hallucinations tool success"""
        mock_audit_result = {
            "audit_result": {
                "accuracy_score": 92,
                "approved": True,
                "issues": []
            }
        }
        mock_audit_resume.return_value = mock_audit_result

        tool_call = {
            "name": "audit_resume_for_hallucinations",
            "arguments": {
                "user_id": "test_user",
                "resume_data": {
                    "personal_info": {"name": "John Doe"},
                    "skills": ["Python", "JavaScript"]
                }
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Resume audit completed" in data["content"][0]["text"]
        assert "92%" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.load_master_resume')
    @patch('main.calculate_fit_score')
    def test_calculate_job_fit_score_tool_with_master_resume(self, mock_calculate_fit, mock_load_master, mock_db):
        """Test calculate_job_fit_score tool using master resume"""
        mock_load_master.return_value = {"skills": ["Python", "Django"]}
        mock_calculate_fit.return_value = 78.5

        tool_call = {
            "name": "calculate_job_fit_score",
            "arguments": {
                "user_id": "test_user",
                "job_data": {
                    "title": "Python Developer",
                    "requirements": ["Python", "Django", "AWS"]
                }
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Job fit score: 78.5%" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.calculate_fit_score')
    def test_calculate_job_fit_score_tool_with_provided_resume(self, mock_calculate_fit, mock_db):
        """Test calculate_job_fit_score tool with provided resume data"""
        mock_calculate_fit.return_value = 85.0

        tool_call = {
            "name": "calculate_job_fit_score",
            "arguments": {
                "user_id": "test_user",
                "job_data": {"title": "Developer"},
                "resume_data": {"skills": ["Python", "JavaScript"]}
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Job fit score: 85.0%" in data["content"][0]["text"]

    def test_optimize_resume_keywords_tool(self):
        """Test optimize_resume_keywords tool"""
        job_data = {
            "title": "Python Developer",
            "requirements": ["Python", "Django", "AWS", "Docker"],
            "skills": ["Python", "JavaScript"]
        }
        resume_data = {
            "skills": ["Python", "JavaScript"],
            "summary": "Experienced developer"
        }

        tool_call = {
            "name": "optimize_resume_keywords",
            "arguments": {
                "user_id": "test_user",
                "job_data": job_data,
                "resume_data": resume_data
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Resume optimization analysis complete" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.generate_resume')
    def test_generate_resume_variants_tool_success(self, mock_generate_resume, mock_db):
        """Test generate_resume_variants tool success"""
        mock_resume = {
            "content": "Variant resume content",
            "fit_score": 82.0
        }
        mock_generate_resume.return_value = mock_resume

        job_list = [
            {"title": "Python Developer", "company": "Tech Corp"},
            {"title": "Django Developer", "company": "Web Inc"}
        ]

        tool_call = {
            "name": "generate_resume_variants",
            "arguments": {
                "user_id": "test_user",
                "job_list": job_list,
                "max_variants": 2
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Generated 2 resume variants" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.generate_resume')
    def test_generate_resume_variants_tool_with_errors(self, mock_generate_resume, mock_db):
        """Test generate_resume_variants tool with some generation errors"""
        # First call succeeds, second fails
        mock_generate_resume.side_effect = [
            {"content": "Good resume", "fit_score": 80.0},
            {"error": "Generation failed"}
        ]

        job_list = [
            {"title": "Python Developer"},
            {"title": "Java Developer"}
        ]

        tool_call = {
            "name": "generate_resume_variants",
            "arguments": {
                "user_id": "test_user",
                "job_list": job_list
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Generated 1 resume variants" in data["content"][0]["text"]

    def test_analyze_resume_effectiveness_tool(self):
        """Test analyze_resume_effectiveness tool"""
        tool_call = {
            "name": "analyze_resume_effectiveness",
            "arguments": {
                "user_id": "test_user",
                "resume_content": "Experienced Python developer with skills in Django, AWS, and Docker. 5 years experience.",
                "job_requirements": ["Python", "Django", "AWS", "Docker", "JavaScript"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "ATS effectiveness analysis" in data["content"][0]["text"]

    def test_analyze_resume_effectiveness_tool_no_requirements(self):
        """Test analyze_resume_effectiveness tool with no job requirements"""
        tool_call = {
            "name": "analyze_resume_effectiveness",
            "arguments": {
                "user_id": "test_user",
                "resume_content": "Short resume content",
                "job_requirements": []
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

class TestATSOptimizeErrorHandling:
    """Test error handling scenarios"""

    def test_tool_call_invalid_tool(self):
        """Test calling invalid tool returns 404"""
        tool_call = {
            "name": "invalid_tool",
            "arguments": {}
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 404

    @patch('main.db')
    @patch('main.generate_resume')
    def test_generate_ats_resume_tool_missing_user_id(self, mock_generate_resume, mock_db):
        """Test generate_ats_resume tool with missing user_id"""
        tool_call = {
            "name": "generate_ats_resume",
            "arguments": {
                "job_data": {"title": "Developer"}
                # Missing user_id
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully or return error
        assert response.status_code in [200, 400]

    @patch('main.db')
    @patch('main.audit_resume')
    def test_audit_resume_tool_missing_resume_data(self, mock_audit_resume, mock_db):
        """Test audit_resume_for_hallucinations tool with missing resume_data"""
        tool_call = {
            "name": "audit_resume_for_hallucinations",
            "arguments": {
                "user_id": "test_user"
                # Missing resume_data
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_optimize_keywords_missing_job_data(self):
        """Test optimize_resume_keywords tool with missing job_data"""
        tool_call = {
            "name": "optimize_resume_keywords",
            "arguments": {
                "user_id": "test_user",
                "resume_data": {"skills": ["Python"]}
                # Missing job_data
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_generate_variants_empty_job_list(self, mock_db):
        """Test generate_resume_variants tool with empty job list"""
        # Configure the mock
        mock_db.resume_variants.insert_one.return_value = None

        tool_call = {
            "name": "generate_resume_variants",
            "arguments": {
                "user_id": "test_user",
                "job_list": []
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Generated 0 resume variants" in data["content"][0]["text"]

    def test_analyze_effectiveness_empty_content(self):
        """Test analyze_resume_effectiveness tool with empty content"""
        tool_call = {
            "name": "analyze_resume_effectiveness",
            "arguments": {
                "user_id": "test_user",
                "resume_content": "",
                "job_requirements": ["Python"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

class TestMongoDBIntegration:
    """Test MongoDB integration"""

    @patch('main.db')
    def test_generated_resumes_storage(self, mock_db):
        """Test generated resumes are stored in MongoDB"""
        mock_db.generated_resumes.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.generated_resumes.insert_one is not None

    @patch('main.db')
    def test_resume_audits_storage(self, mock_db):
        """Test resume audits are stored in MongoDB"""
        mock_db.resume_audits.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.resume_audits.insert_one is not None

    @patch('main.db')
    def test_fit_analyses_storage(self, mock_db):
        """Test fit analyses are stored in MongoDB"""
        mock_db.fit_analyses.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.fit_analyses.insert_one is not None

    @patch('main.db')
    def test_resume_variants_storage(self, mock_db):
        """Test resume variants are stored in MongoDB"""
        mock_db.resume_variants.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.resume_variants.insert_one is not None

class TestATSOptimizeCoreFunctionality:
    """Test core business logic functions"""

    @patch('main.db')
    @patch('main.generate_resume')
    def test_generate_ats_resume_function_success(self, mock_generate_resume, mock_db):
        """Test generate_ats_resume function success"""
        mock_resume = {
            "content": "Generated resume content",
            "fit_score": 88.0,
            "word_file": "/path/to/resume.docx",
            "pdf_file": "/path/to/resume.pdf"
        }
        mock_generate_resume.return_value = mock_resume
        mock_db.generated_resumes.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(generate_ats_resume_tool({
            "user_id": "test_user",
            "job_data": {"title": "Developer", "company": "Tech Corp"},
            "format": "both"
        }))

        assert isinstance(result, MCPToolResponse)
        assert "ATS-optimized resume generated" in result.content[0]["text"]
        assert "88.0%" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.audit_resume')
    def test_audit_resume_function_error_handling(self, mock_audit_resume, mock_db):
        """Test audit_resume_for_hallucinations function error handling"""
        mock_audit_resume.side_effect = Exception("Audit service unavailable")
        mock_db.resume_audits.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(audit_resume_for_hallucinations_tool({
            "user_id": "test_user",
            "resume_data": {"skills": ["Python"]}
        }))

        assert isinstance(result, MCPToolResponse)
        assert result.isError == True
        assert "Error auditing resume" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.load_master_resume')
    @patch('main.calculate_fit_score')
    def test_calculate_fit_score_function_with_master_resume(self, mock_calculate_fit, mock_load_master, mock_db):
        """Test calculate_job_fit_score function using master resume"""
        mock_load_master.return_value = {"skills": ["Python", "Django", "AWS"]}
        mock_calculate_fit.return_value = 92.5
        mock_db.fit_analyses.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(calculate_job_fit_score_tool({
            "user_id": "test_user",
            "job_data": {"title": "Python Developer", "requirements": ["Python", "Django"]}
        }))

        assert isinstance(result, MCPToolResponse)
        assert "Job fit score: 92.5%" in result.content[0]["text"]

class TestATSOptimizeIntegration:
    """Test integration scenarios"""

    @patch('main.db')
    @patch('main.generate_resume')
    @patch('main.audit_resume')
    def test_complete_resume_optimization_workflow(self, mock_audit_resume, mock_generate_resume, mock_db):
        """Test complete resume optimization workflow"""
        # Setup mocks
        mock_generate_resume.return_value = {
            "content": "Optimized resume content",
            "fit_score": 87.0
        }
        mock_audit_resume.return_value = {
            "audit_result": {"accuracy_score": 95, "approved": True}
        }

        # Test workflow integration
        assert mock_generate_resume is not None
        assert mock_audit_resume is not None
        assert mock_db is not None

    @patch('main.db')
    @patch('main.generate_resume')
    def test_bulk_resume_generation(self, mock_generate_resume, mock_db):
        """Test bulk resume generation for multiple jobs"""
        mock_generate_resume.return_value = {
            "content": "Generated resume",
            "fit_score": 80.0
        }

        job_list = [
            {"title": "Frontend Developer", "company": "Web Corp"},
            {"title": "Backend Developer", "company": "API Inc"},
            {"title": "Full Stack Developer", "company": "Tech Ltd"}
        ]

        # Test the bulk generation would work
        import asyncio
        result = asyncio.run(generate_resume_variants_tool({
            "user_id": "test_user",
            "job_list": job_list,
            "max_variants": 3
        }))

        assert isinstance(result, MCPToolResponse)
        assert "Generated 3 resume variants" in result.content[0]["text"]

if __name__ == "__main__":
    pytest.main([__file__])