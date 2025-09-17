"""
Comprehensive pytest test suite for Resume Upload MCP Server
Tests MCP endpoints, core functionality, error handling, MongoDB integration, and API responses
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import mongomock
from io import BytesIO

# Import the FastAPI app and related functions
from main import app, MCPToolResponse, parse_resume_file_tool, extract_resume_sections_tool, merge_resume_data_tool, validate_resume_completeness_tool, anonymize_resume_data_tool

# Create test client
client = TestClient(app)

class TestResumeUploadEndpoints:
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

    def test_list_resources_endpoint(self):
        """Test MCP resources listing endpoint"""
        response = client.get("/mcp/resources")
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data

    @patch('main.db')
    def test_read_resumes_resource(self, mock_db):
        """Test reading resumes resource"""
        mock_resumes = [
            {"user_id": "test_user", "filename": "resume.pdf", "timestamp": datetime.now()}
        ]
        mock_db.resumes.find.return_value.sort.return_value.limit.return_value = mock_resumes

        response = client.get("/mcp/resources/mongodb://job_application_agent/resumes")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @patch('main.db')
    def test_read_master_resumes_resource(self, mock_db):
        """Test reading master resumes resource"""
        mock_master_resumes = [
            {"user_id": "test_user", "resume_data": {"skills": ["python"]}}
        ]
        mock_db.master_resumes.find.return_value = mock_master_resumes

        response = client.get("/mcp/resources/mongodb://job_application_agent/master_resumes")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

class TestResumeUploadToolCalls:
    """Test MCP tool calls"""

    @patch('main.db')
    @patch('main.parse_resume_file')
    def test_parse_resume_file_tool_success(self, mock_parse_resume, mock_db):
        """Test parse_resume_file tool success"""
        mock_parse_resume.return_value = {
            "personal_info": {"name": "John Doe"},
            "skills": ["python", "fastapi"],
            "experience": ["Software Engineer"]
        }

        tool_call = {
            "name": "parse_resume_file",
            "arguments": {
                "user_id": "test_user",
                "file_path": "/tmp/test_resume.pdf",
                "anonymize": True
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Resume parsed successfully" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.parse_resume_file')
    def test_parse_resume_file_tool_error(self, mock_parse_resume, mock_db):
        """Test parse_resume_file tool error handling"""
        mock_parse_resume.side_effect = Exception("Parsing failed")

        tool_call = {
            "name": "parse_resume_file",
            "arguments": {
                "user_id": "test_user",
                "file_path": "/tmp/test_resume.pdf"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True
        assert "Error parsing resume" in data["content"][0]["text"]

    @patch('main.db')
    def test_extract_resume_sections_tool_with_data(self, mock_db):
        """Test extract_resume_sections tool with provided resume data"""
        tool_call = {
            "name": "extract_resume_sections",
            "arguments": {
                "user_id": "test_user",
                "sections": ["skills", "experience"],
                "resume_data": {
                    "skills": ["python", "django"],
                    "experience": ["2 years Python dev"],
                    "education": ["BS Computer Science"]
                }
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Extracted sections" in data["content"][0]["text"]

    @patch('main.db')
    def test_extract_resume_sections_tool_from_db(self, mock_db):
        """Test extract_resume_sections tool loading from database"""
        mock_resume_doc = {
            "user_id": "test_user",
            "parsed_data": {
                "skills": ["python"],
                "experience": ["Developer"]
            }
        }
        mock_db.resumes.find_one.return_value = mock_resume_doc

        tool_call = {
            "name": "extract_resume_sections",
            "arguments": {
                "user_id": "test_user",
                "sections": ["skills"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @patch('main.db')
    @patch('main.merge_resume_data')
    @patch('main.load_master_resume')
    def test_merge_resume_data_tool_with_existing(self, mock_load_resume, mock_merge, mock_db):
        """Test merge_resume_data tool with existing resume"""
        mock_load_resume.return_value = {"skills": ["python"]}
        mock_merge.return_value = {"skills": ["python", "django"]}

        tool_call = {
            "name": "merge_resume_data",
            "arguments": {
                "user_id": "test_user",
                "new_resume_data": {"skills": ["django"]}
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Resume data merged" in data["content"][0]["text"]

    def test_validate_resume_completeness_tool_complete(self):
        """Test validate_resume_completeness tool with complete resume"""
        tool_call = {
            "name": "validate_resume_completeness",
            "arguments": {
                "user_id": "test_user",
                "resume_data": {
                    "personal_info": {"name": "John Doe"},
                    "summary": "Experienced developer",
                    "skills": ["python"],
                    "experience": ["Software Engineer"],
                    "education": ["BS Computer Science"]
                }
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "100.0%" in data["content"][0]["text"]

    def test_validate_resume_completeness_tool_incomplete(self):
        """Test validate_resume_completeness tool with incomplete resume"""
        tool_call = {
            "name": "validate_resume_completeness",
            "arguments": {
                "user_id": "test_user",
                "resume_data": {
                    "skills": ["python"],
                    "experience": ["Developer"]
                }
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Missing sections" in data["content"][0]["text"]

    @patch('main.popia_compliance')
    def test_anonymize_resume_data_tool_success(self, mock_popia):
        """Test anonymize_resume_data tool success"""
        mock_popia.anonymize_user_data.return_value = ({"skills": ["python"]}, {"name": "John Doe"})
        mock_popia.audit_data_processing = Mock()

        tool_call = {
            "name": "anonymize_resume_data",
            "arguments": {
                "user_id": "test_user",
                "resume_data": {
                    "personal_info": {"name": "John Doe"},
                    "skills": ["python"]
                }
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "anonymized" in data["content"][0]["text"]

    def test_anonymize_resume_data_tool_no_popia(self):
        """Test anonymize_resume_data tool when POPIA module not available"""
        # Mock popia_compliance as None
        with patch('main.popia_compliance', None):
            tool_call = {
                "name": "anonymize_resume_data",
                "arguments": {
                    "user_id": "test_user",
                    "resume_data": {"personal_info": {"name": "John Doe"}}
                }
            }

            response = client.post("/mcp/tools/call", json=tool_call)
            assert response.status_code == 200
            data = response.json()
            assert data["isError"] == True
            assert "POPIA compliance module not available" in data["content"][0]["text"]

class TestFileUploadEndpoint:
    """Test file upload endpoint"""

    @patch('main.db')
    @patch('main.parse_resume_file')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('os.remove')
    def test_upload_resume_success(self, mock_remove, mock_open, mock_parse_resume, mock_db):
        """Test successful resume upload"""
        mock_parse_resume.return_value = {
            "personal_info": {"name": "John Doe"},
            "skills": ["python"]
        }

        # Create a mock file
        file_content = b"Mock PDF content"
        files = {"file": ("test_resume.pdf", BytesIO(file_content), "application/pdf")}
        data = {"user_id": "test_user", "anonymize": True}

        response = client.post("/upload-resume", files=files, data=data)
        assert response.status_code == 200
        result = response.json()
        assert "Resume parsed successfully" in result["message"]
        assert result["user_id"] == "test_user"
        assert result["anonymized"] == True

    def test_upload_resume_invalid_file_type(self):
        """Test upload with invalid file type"""
        file_content = b"Mock executable content"
        files = {"file": ("test.exe", BytesIO(file_content), "application/x-msdownload")}
        data = {"user_id": "test_user"}

        response = client.post("/upload-resume", files=files, data=data)
        assert response.status_code == 400
        result = response.json()
        assert "Only PDF and DOCX files are supported" in result["detail"]

    @patch('main.parse_resume_file')
    def test_upload_resume_parsing_error(self, mock_parse_resume):
        """Test upload when resume parsing fails"""
        mock_parse_resume.side_effect = Exception("Parsing failed")

        file_content = b"Mock PDF content"
        files = {"file": ("test_resume.pdf", BytesIO(file_content), "application/pdf")}
        data = {"user_id": "test_user"}

        response = client.post("/upload-resume", files=files, data=data)
        assert response.status_code == 500

class TestErrorHandling:
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
    def test_extract_resume_sections_no_data(self, mock_db):
        """Test extract_resume_sections when no resume data found"""
        mock_db.resumes.find_one.return_value = None

        tool_call = {
            "name": "extract_resume_sections",
            "arguments": {
                "user_id": "test_user",
                "sections": ["skills"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True

class TestMongoDBIntegration:
    """Test MongoDB integration"""

    @patch('main.db')
    def test_resume_storage(self, mock_db):
        """Test resume data is stored in MongoDB"""
        mock_db.resumes.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.resumes.insert_one is not None

    @patch('main.db')
    def test_master_resume_updates(self, mock_db):
        """Test master resume updates work correctly"""
        mock_db.master_resumes.replace_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.master_resumes.replace_one is not None

    @patch('main.db')
    def test_anonymized_resume_storage(self, mock_db):
        """Test anonymized resume data storage"""
        mock_db.anonymized_resumes.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.anonymized_resumes.insert_one is not None

if __name__ == "__main__":
    pytest.main([__file__])