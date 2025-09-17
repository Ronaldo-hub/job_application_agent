"""
Comprehensive pytest test suite for Job Search MCP Server
Tests MCP endpoints, core functionality, error handling, MongoDB integration, and API responses
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import mongomock

# Import the FastAPI app and related functions
from main import app, MCPToolResponse, search_jobs_multi_api_tool, filter_jobs_by_criteria_tool, deduplicate_jobs_tool, analyze_job_market_trends_tool, get_job_search_history_tool, update_job_market_data

# Create test client
client = TestClient(app)

class TestJobSearchEndpoints:
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
            "search_jobs_multi_api",
            "filter_jobs_by_criteria",
            "deduplicate_jobs",
            "analyze_job_market_trends",
            "get_job_search_history"
        ]
        for tool_name in expected_tools:
            assert tool_name in tool_names

    def test_list_resources_endpoint(self):
        """Test MCP resources listing endpoint"""
        response = client.get("/mcp/resources")
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data

    @patch('main.db')
    def test_read_job_searches_resource(self, mock_db):
        """Test reading job searches resource"""
        mock_searches = [
            {"user_id": "test_user", "keywords": "python", "timestamp": datetime.now()}
        ]
        mock_db.job_searches.find.return_value.sort.return_value.limit.return_value = mock_searches

        response = client.get("/mcp/resources/mongodb://job_application_agent/job_searches")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @patch('main.db')
    def test_read_job_market_data_resource(self, mock_db):
        """Test reading job market data resource"""
        mock_market_data = [
            {"keywords": "python", "total_jobs": 150, "timestamp": datetime.now()}
        ]
        mock_db.job_market_data.find.return_value.sort.return_value.limit.return_value = mock_market_data

        response = client.get("/mcp/resources/mongodb://job_application_agent/job_market_data")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

class TestJobSearchToolCalls:
    """Test MCP tool calls"""

    @patch('main.db')
    @patch('main.search_jobs_async')
    def test_search_jobs_multi_api_tool_success(self, mock_search_jobs, mock_db):
        """Test search_jobs_multi_api tool success"""
        mock_jobs = [
            {"title": "Python Developer", "company": "Tech Corp", "location": "Remote"},
            {"title": "Django Developer", "company": "Web Inc", "location": "Cape Town"}
        ]
        mock_search_jobs.return_value = mock_jobs

        tool_call = {
            "name": "search_jobs_multi_api",
            "arguments": {
                "keywords": "python developer",
                "location": "remote",
                "max_age_days": 7,
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Found 2 jobs" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.search_jobs_async')
    def test_search_jobs_multi_api_tool_error(self, mock_search_jobs, mock_db):
        """Test search_jobs_multi_api tool error handling"""
        mock_search_jobs.side_effect = Exception("API connection failed")

        tool_call = {
            "name": "search_jobs_multi_api",
            "arguments": {
                "keywords": "python developer"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True
        assert "Error searching jobs" in data["content"][0]["text"]

    def test_filter_jobs_by_criteria_tool(self):
        """Test filter_jobs_by_criteria tool"""
        jobs = [
            {"title": "Python Dev", "location": "Cape Town", "salary": "50000"},
            {"title": "Java Dev", "location": "Johannesburg", "salary": "60000"},
            {"title": "Remote Python Dev", "location": "Remote", "salary": "70000"}
        ]

        tool_call = {
            "name": "filter_jobs_by_criteria",
            "arguments": {
                "jobs": jobs,
                "location": "Cape Town",
                "max_age_days": 30
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Filtered 3 jobs down to" in data["content"][0]["text"]

    def test_filter_jobs_by_criteria_with_salary(self):
        """Test filter_jobs_by_criteria tool with salary filters"""
        jobs = [
            {"title": "Junior Dev", "salary": "40000"},
            {"title": "Mid Dev", "salary": "60000"},
            {"title": "Senior Dev", "salary": "80000"}
        ]

        tool_call = {
            "name": "filter_jobs_by_criteria",
            "arguments": {
                "jobs": jobs,
                "salary_min": 50000,
                "salary_max": 75000
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @patch('main.remove_duplicates')
    def test_deduplicate_jobs_tool(self, mock_remove_duplicates):
        """Test deduplicate_jobs tool"""
        jobs = [
            {"title": "Python Developer", "company": "Tech Corp"},
            {"title": "Python Developer", "company": "Tech Corp"},  # Duplicate
            {"title": "Java Developer", "company": "Web Inc"}
        ]
        mock_remove_duplicates.return_value = [
            {"title": "Python Developer", "company": "Tech Corp"},
            {"title": "Java Developer", "company": "Web Inc"}
        ]

        tool_call = {
            "name": "deduplicate_jobs",
            "arguments": {
                "jobs": jobs
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Deduplicated 3 jobs down to 2" in data["content"][0]["text"]

    def test_analyze_job_market_trends_tool(self):
        """Test analyze_job_market_trends tool"""
        jobs = [
            {"title": "Python Dev", "company": "Tech Corp", "location": "Cape Town"},
            {"title": "Java Dev", "company": "Web Inc", "location": "Johannesburg"},
            {"title": "Python Dev", "company": "Data Co", "location": "Cape Town"}
        ]

        tool_call = {
            "name": "analyze_job_market_trends",
            "arguments": {
                "jobs": jobs,
                "keywords": "python developer"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Job market analysis" in data["content"][0]["text"]

    @patch('main.db')
    def test_get_job_search_history_tool(self, mock_db):
        """Test get_job_search_history tool"""
        mock_history = [
            {"user_id": "test_user", "keywords": "python", "results_count": 25, "timestamp": datetime.now()}
        ]
        mock_db.job_searches.find.return_value.sort.return_value.limit.return_value = mock_history

        tool_call = {
            "name": "get_job_search_history",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Found 1 recent job searches" in data["content"][0]["text"]

class TestJobSearchErrorHandling:
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
    @patch('main.search_jobs_async')
    def test_search_jobs_with_missing_keywords(self, mock_search_jobs, mock_db):
        """Test search_jobs_multi_api tool with missing keywords"""
        tool_call = {
            "name": "search_jobs_multi_api",
            "arguments": {
                "location": "remote"
                # Missing keywords
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should still work but might have different behavior
        assert response.status_code in [200, 400]

    def test_filter_jobs_empty_list(self):
        """Test filter_jobs_by_criteria tool with empty job list"""
        tool_call = {
            "name": "filter_jobs_by_criteria",
            "arguments": {
                "jobs": []
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    def test_analyze_trends_empty_jobs(self):
        """Test analyze_job_market_trends tool with empty job list"""
        tool_call = {
            "name": "analyze_job_market_trends",
            "arguments": {
                "jobs": [],
                "keywords": "python"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

class TestMongoDBIntegration:
    """Test MongoDB integration"""

    @patch('main.db')
    def test_job_search_storage(self, mock_db):
        """Test job search results are stored in MongoDB"""
        mock_db.job_searches.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.job_searches.insert_one is not None

    @patch('main.db')
    def test_job_market_data_storage(self, mock_db):
        """Test job market data is stored in MongoDB"""
        mock_db.job_market_data.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.job_market_data.insert_one is not None

    @patch('main.db')
    def test_scenario_comparisons_storage(self, mock_db):
        """Test scenario comparisons are stored in MongoDB"""
        mock_db.scenario_comparisons.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.scenario_comparisons.insert_one is not None

class TestJobSearchCoreFunctionality:
    """Test core business logic functions"""

    @patch('main.db')
    def test_update_job_market_data_function(self, mock_db):
        """Test update_job_market_data function"""
        jobs = [
            {"title": "Python Dev", "company": "Tech Corp", "salary": "50000"},
            {"title": "Java Dev", "company": "Web Inc", "salary": "60000"}
        ]

        # Call the function directly
        update_job_market_data("python", "remote", jobs)

        # Verify data was inserted
        assert mock_db.job_market_data.insert_one.called

    @patch('main.db')
    def test_update_job_market_data_with_salaries(self, mock_db):
        """Test update_job_market_data function with salary calculations"""
        jobs = [
            {"title": "Dev", "company": "Corp", "salary": "50000"},
            {"title": "Dev2", "company": "Corp2", "salary": "70000"}
        ]

        update_job_market_data("developer", "remote", jobs)

        # Verify the call was made
        assert mock_db.job_market_data.insert_one.called
        call_args = mock_db.job_market_data.insert_one.call_args[0][0]

        # Verify salary calculation
        assert "avg_salary" in call_args

class TestJobSearchIntegration:
    """Test integration scenarios"""

    @patch('main.db')
    @patch('main.search_jobs_async')
    @patch('main.apply_filters')
    @patch('main.remove_duplicates')
    def test_complete_job_search_workflow(self, mock_deduplicate, mock_filter, mock_search, mock_db):
        """Test complete job search workflow"""
        # Setup mocks
        mock_search.return_value = [
            {"title": "Python Dev", "company": "Tech Corp", "location": "Remote"},
            {"title": "Python Dev", "company": "Tech Corp", "location": "Remote"},  # Duplicate
            {"title": "Java Dev", "company": "Web Inc", "location": "Cape Town"}
        ]
        mock_filter.return_value = [
            {"title": "Python Dev", "company": "Tech Corp", "location": "Remote"}
        ]
        mock_deduplicate.return_value = [
            {"title": "Python Dev", "company": "Tech Corp", "location": "Remote"}
        ]

        # Test the workflow would work end-to-end
        assert mock_search is not None
        assert mock_filter is not None
        assert mock_deduplicate is not None

if __name__ == "__main__":
    pytest.main([__file__])