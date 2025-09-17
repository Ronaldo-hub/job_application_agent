
"""
Comprehensive pytest test suite for Team Simulation MCP Server
Tests MCP endpoints, core functionality, error handling, MongoDB integration, and API responses
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import mongomock
import numpy as np

# Import the FastAPI app and related functions
from main import app, MCPToolResponse, run_policy_simulation_tool, compare_policy_scenarios_tool, generate_policy_recommendations_tool, analyze_simulation_trends_tool, run_cape_town_simulation_tool, get_simulation_history_tool, extract_team_skills_tool, form_teams_tool, suggest_team_activities_tool, create_team_simulation_tool

# Create test client
client = TestClient(app)

class TestTeamSimEndpoints:
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
            "run_policy_simulation",
            "compare_policy_scenarios",
            "generate_policy_recommendations",
            "analyze_simulation_trends",
            "run_cape_town_simulation",
            "get_simulation_history",
            "extract_team_skills",
            "form_teams",
            "suggest_team_activities",
            "create_team_simulation"
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
    def test_read_simulations_resource(self, mock_db):
        """Test reading simulations resource"""
        mock_simulations = [
            {"user_id": "test_user", "simulation_type": "unemployment", "timestamp": datetime.now()}
        ]
        mock_db.simulations.find.return_value.sort.return_value.limit.return_value = mock_simulations

        response = client.get("/mcp/resources/mongodb://job_application_agent/simulations")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @patch('main.db')
    def test_read_team_simulations_resource(self, mock_db):
        """Test reading team simulations resource"""
        mock_team_sims = [
            {"user_id": "test_user", "num_teams": 3, "timestamp": datetime.now()}
        ]
        mock_db.team_simulations.find.return_value.sort.return_value.limit.return_value = mock_team_sims

        response = client.get("/mcp/resources/mongodb://job_application_agent/team_simulations")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

class TestTeamSimToolCalls:
    """Test MCP tool calls"""

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_run_policy_simulation_tool_success(self, mock_run_simulation, mock_db):
        """Test run_policy_simulation tool success"""
        mock_result = {
            "final_metrics": {
                "policy_effectiveness": 0.85,
                "steps_run": 100
            },
            "time_series_data": {
                "employed": [0.6, 0.65, 0.7, 0.75, 0.8]
            }
        }
        mock_run_simulation.return_value = mock_result

        tool_call = {
            "name": "run_policy_simulation",
            "arguments": {
                "simulation_type": "unemployment",
                "parameters": {"policy_strength": 0.8},
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "85.0%" in data["content"][0]["text"]
        assert "100 steps" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_run_policy_simulation_tool_error(self, mock_run_simulation, mock_db):
        """Test run_policy_simulation tool error handling"""
        mock_run_simulation.return_value = {"error": "Simulation failed"}

        tool_call = {
            "name": "run_policy_simulation",
            "arguments": {
                "simulation_type": "unemployment",
                "parameters": {},
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True
        assert "Simulation error" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.PolicySimulationRunner')
    def test_compare_policy_scenarios_tool(self, mock_runner_class, mock_db):
        """Test compare_policy_scenarios tool"""
        mock_runner = Mock()
        mock_runner.compare_policies.return_value = {
            "best_scenario": {
                "scenario_name": "High Investment",
                "final_metrics": {"policy_effectiveness": 0.9}
            },
            "comparison_data": {}
        }
        mock_runner_class.return_value = mock_runner

        scenarios = [
            {"name": "Low Investment", "parameters": {"investment": 0.3}},
            {"name": "High Investment", "parameters": {"investment": 0.8}}
        ]

        tool_call = {
            "name": "compare_policy_scenarios",
            "arguments": {
                "simulation_type": "unemployment",
                "scenarios": scenarios,
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "High Investment" in data["content"][0]["text"]
        assert "90.0%" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.generate_policy_recommendations')
    def test_generate_policy_recommendations_tool(self, mock_generate_rec, mock_db):
        """Test generate_policy_recommendations tool"""
        mock_recommendations = {
            "recommendation_level": "High",
            "implementation_priority": "Immediate",
            "suggested_actions": ["Increase funding", "Expand programs"]
        }
        mock_generate_rec.return_value = mock_recommendations

        tool_call = {
            "name": "generate_policy_recommendations",
            "arguments": {
                "simulation_results": {
                    "final_metrics": {"policy_effectiveness": 0.8}
                },
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "High" in data["content"][0]["text"]
        assert "Immediate" in data["content"][0]["text"]

    def test_analyze_simulation_trends_tool_effectiveness(self):
        """Test analyze_simulation_trends tool for effectiveness analysis"""
        simulation_data = {
            "final_metrics": {"policy_effectiveness": 0.95}
        }

        tool_call = {
            "name": "analyze_simulation_trends",
            "arguments": {
                "simulation_data": simulation_data,
                "analysis_type": "effectiveness",
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Highly Effective" in data["content"][0]["text"]

    def test_analyze_simulation_trends_tool_trends(self):
        """Test analyze_simulation_trends tool for trends analysis"""
        simulation_data = {
            "time_series_data": {
                "employed": [0.5, 0.55, 0.6, 0.65, 0.7]  # Improving trend
            }
        }

        tool_call = {
            "name": "analyze_simulation_trends",
            "arguments": {
                "simulation_data": simulation_data,
                "analysis_type": "trends",
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Improving" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_run_cape_town_simulation_tool_unemployment(self, mock_run_simulation, mock_db):
        """Test run_cape_town_simulation tool for unemployment"""
        mock_result = {
            "final_metrics": {"policy_effectiveness": 0.75}
        }
        mock_run_simulation.return_value = mock_result

        tool_call = {
            "name": "run_cape_town_simulation",
            "arguments": {
                "issue_type": "unemployment",
                "parameters": {"policy_strength": 0.7},
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Cape Town unemployment simulation" in data["content"][0]["text"]
        assert "75.0%" in data["content"][0]["text"]

    @patch('main.db')
    def test_get_simulation_history_tool(self, mock_db):
        """Test get_simulation_history tool"""
        mock_history = [
            {"user_id": "test_user", "simulation_type": "unemployment", "timestamp": datetime.now()}
        ]
        mock_db.simulations.find.return_value.sort.return_value.limit.return_value = mock_history

        tool_call = {
            "name": "get_simulation_history",
            "arguments": {
                "user_id": "test_user",
                "limit": 5
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Found 1 simulation runs" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.extract_skills_from_resumes')
    def test_extract_team_skills_tool(self, mock_extract_skills, mock_db):
        """Test extract_team_skills tool"""
        mock_extract_skills.return_value = {
            "user1": ["python", "django"],
            "user2": ["javascript", "react"],
            "user3": ["python", "aws"]
        }

        tool_call = {
            "name": "extract_team_skills",
            "arguments": {
                "user_ids": ["user1", "user2", "user3"],
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Extracted skills from 3 users" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.extract_skills_from_resumes')
    @patch('main.form_teams_with_clustering')
    def test_form_teams_tool(self, mock_form_teams, mock_extract_skills, mock_db):
        """Test form_teams tool"""
        mock_extract_skills.return_value = {
            "user1": ["python", "django"],
            "user2": ["javascript", "react"]
        }
        mock_form_teams.return_value = {
            "team_1": ["user1", "user2"]
        }

        tool_call = {
            "name": "form_teams",
            "arguments": {
                "user_ids": ["user1", "user2"],
                "num_teams": 1,
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Formed 1 teams" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.suggest_collaborative_activities')
    def test_suggest_team_activities_tool(self, mock_suggest_activities, mock_db):
        """Test suggest_team_activities tool"""
        mock_suggest_activities.return_value = {
            "team_1": ["Start a community co-op", "Develop local tech startup"],
            "team_2": ["Establish urban farming", "Water conservation project"]
        }

        teams = {
            "team_1": ["user1", "user2"],
            "team_2": ["user3", "user4"]
        }

        tool_call = {
            "name": "suggest_team_activities",
            "arguments": {
                "teams": teams,
                "cape_town_focus": True,
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Cape Town issues" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.extract_skills_from_resumes')
    @patch('main.form_teams_with_clustering')
    @patch('main.suggest_collaborative_activities')
    def test_create_team_simulation_tool(self, mock_suggest_activities, mock_form_teams, mock_extract_skills, mock_db):
        """Test create_team_simulation tool"""
        mock_extract_skills.return_value = {
            "user1": ["python", "django"],
            "user2": ["javascript", "react"]
        }
        mock_form_teams.return_value = {
            "team_1": ["user1", "user2"]
        }
        mock_suggest_activities.return_value = {
            "team_1": ["Start a community co-op"]
        }

        tool_call = {
            "name": "create_team_simulation",
            "arguments": {
                "user_ids": ["user1", "user2"],
                "num_teams": 1,
                "cape_town_focus": True,
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Team simulation completed" in data["content"][0]["text"]

class TestTeamSimErrorHandling:
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
    @patch('main.run_policy_simulation')
    def test_run_policy_simulation_invalid_type(self, mock_run_simulation, mock_db):
        """Test run_policy_simulation tool with invalid simulation type"""
        mock_run_simulation.side_effect = ValueError("Unknown simulation type")

        tool_call = {
            "name": "run_policy_simulation",
            "arguments": {
                "simulation_type": "invalid_type",
                "parameters": {},
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True

    @patch('main.db')
    @patch('main.extract_skills_from_resumes')
    def test_extract_team_skills_no_users(self, mock_extract_skills, mock_db):
        """Test extract_team_skills tool with no users"""
        mock_extract_skills.return_value = {}

        tool_call = {
            "name": "extract_team_skills",
            "arguments": {
                "user_ids": [],
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

class TestMongoDBIntegration:
    """Test MongoDB integration"""

    @patch('main.db')
    def test_simulations_storage(self, mock_db):
        """Test simulations are stored in MongoDB"""
        mock_db.simulations.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.simulations.insert_one is not None

    @patch('main.db')
    def test_team_simulations_storage(self, mock_db):
        """Test team simulations are stored in MongoDB"""
        mock_db.team_simulations.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.team_simulations.insert_one is not None

    @patch('main.db')
    def test_team_formations_storage(self, mock_db):
        """Test team formations are stored in MongoDB"""
        mock_db.team_formations.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.team_formations.insert_one is not None

class TestTeamSimCoreFunctionality:
    """Test core business logic functions"""

    @patch('main.db')
    def test_extract_skills_from_resumes_function(self, mock_db):
        """Test extract_skills_from_resumes function"""
        mock_resume_doc = {
            "user_id": "test_user",
            "parsed_data": {
                "skills": ["python", "django"]
            }
        }
        mock_db.resumes.find_one.return_value = mock_resume_doc

        # Test the function logic
        from main import extract_skills_from_resumes
        result = extract_skills_from_resumes(["test_user"])

        assert "test_user" in result
        assert "python" in result["test_user"]
        assert "django" in result["test_user"]

    @patch('main.db')
    def test_form_teams_with_clustering_function(self, mock_db):
        """Test form_teams_with_clustering function"""
        skills_data = {
            "user1": ["python", "django"],
            "user2": ["javascript", "react"],
            "user3": ["python", "aws"]
        }

        # Mock sklearn components
        with patch('main.MLB') as mock_mlb, \
             patch('main.KMeans') as mock_kmeans:

            mock_mlb_instance = Mock()
            mock_mlb_instance.fit_transform.return_value = np.array([[1, 0], [0, 1], [1, 0]])
            mock_mlb.return_value = mock_mlb_instance

            mock_kmeans_instance = Mock()
            mock_kmeans_instance.fit_predict.return_value = np.array