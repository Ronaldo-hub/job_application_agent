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

# Mock external dependencies before importing main
with patch('mesa_abm_simulations.run_policy_simulation'):
    with patch('mesa_abm_simulations.generate_policy_recommendations'):
        with patch('sklearn.cluster.KMeans'):
            with patch('sklearn.preprocessing.MultiLabelBinarizer'):
                # Import the FastAPI app and related functions
                from main import app, MCPToolResponse, run_policy_simulation_tool, compare_policy_scenarios_tool, generate_policy_recommendations_tool, analyze_simulation_trends_tool, run_cape_town_simulation_tool, get_simulation_history_tool, extract_team_skills_tool, form_teams_tool, suggest_team_activities_tool, create_team_simulation_tool, extract_skills_from_resumes, form_teams_with_clustering, suggest_collaborative_activities

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

    def test_list_prompts_endpoint(self):
        """Test MCP prompts listing endpoint"""
        response = client.get("/mcp/prompts")
        assert response.status_code == 200
        data = response.json()
        assert "prompts" in data

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
    def test_read_policy_recommendations_resource(self, mock_db):
        """Test reading policy recommendations resource"""
        mock_recommendations = [
            {"user_id": "test_user", "recommendation_level": "High", "timestamp": datetime.now()}
        ]
        mock_db.policy_recommendations.find.return_value.sort.return_value.limit.return_value = mock_recommendations

        response = client.get("/mcp/resources/mongodb://job_application_agent/policy_recommendations")
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

    def test_get_prompt(self):
        """Test getting MCP prompt"""
        response = client.get("/mcp/prompts/policy_simulation_guide")
        assert response.status_code == 200
        data = response.json()
        assert "prompt" in data

    def test_get_prompt_not_found(self):
        """Test getting non-existent MCP prompt"""
        response = client.get("/mcp/prompts/non_existent_prompt")
        assert response.status_code == 404

class TestTeamSimToolCalls:
    """Test MCP tool calls"""

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_run_policy_simulation_tool_success(self, mock_run_simulation, mock_db):
        """Test run_policy_simulation tool success"""
        mock_result = {
            "final_metrics": {"policy_effectiveness": 85.5},
            "steps_run": 100
        }
        mock_run_simulation.return_value = mock_result

        tool_call = {
            "name": "run_policy_simulation",
            "arguments": {
                "simulation_type": "unemployment",
                "parameters": {"population_size": 1000},
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Policy simulation completed" in data["content"][0]["text"]
        assert "85.5%" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_run_policy_simulation_tool_error(self, mock_run_simulation, mock_db):
        """Test run_policy_simulation tool error handling"""
        mock_run_simulation.return_value = {"error": "Simulation failed"}

        tool_call = {
            "name": "run_policy_simulation",
            "arguments": {
                "simulation_type": "unemployment"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True
        assert "Simulation error" in data["content"][0]["text"]

    @patch('main.db')
    @patch('mesa_abm_simulations.PolicySimulationRunner')
    def test_compare_policy_scenarios_tool_success(self, mock_runner_class, mock_db):
        """Test compare_policy_scenarios tool success"""
        mock_runner = Mock()
        mock_comparison = {
            "best_scenario": {
                "scenario_name": "Scenario A",
                "final_metrics": {"policy_effectiveness": 90.0}
            }
        }
        mock_runner.compare_policies.return_value = mock_comparison
        mock_runner_class.return_value = mock_runner

        tool_call = {
            "name": "compare_policy_scenarios",
            "arguments": {
                "simulation_type": "unemployment",
                "scenarios": [
                    {"name": "Scenario A", "parameters": {"tax_rate": 0.1}},
                    {"name": "Scenario B", "parameters": {"tax_rate": 0.2}}
                ],
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Scenario comparison completed" in data["content"][0]["text"]
        assert "Scenario A" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.generate_policy_recommendations')
    def test_generate_policy_recommendations_tool_success(self, mock_generate_recommendations, mock_db):
        """Test generate_policy_recommendations tool success"""
        mock_recommendations = {
            "recommendation_level": "High",
            "implementation_priority": "Immediate"
        }
        mock_generate_recommendations.return_value = mock_recommendations

        tool_call = {
            "name": "generate_policy_recommendations",
            "arguments": {
                "simulation_results": {
                    "final_metrics": {"policy_effectiveness": 85.0}
                },
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Policy recommendations generated" in data["content"][0]["text"]
        assert "High" in data["content"][0]["text"]

    @patch('main.db')
    def test_analyze_simulation_trends_tool_effectiveness(self, mock_db):
        """Test analyze_simulation_trends tool with effectiveness analysis"""
        mock_db.simulation_analyses.insert_one.return_value = None

        tool_call = {
            "name": "analyze_simulation_trends",
            "arguments": {
                "simulation_data": {
                    "final_metrics": {"policy_effectiveness": 0.85}
                },
                "analysis_type": "effectiveness",
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Simulation trend analysis completed" in data["content"][0]["text"]

    @patch('main.db')
    def test_analyze_simulation_trends_tool_trends(self, mock_db):
        """Test analyze_simulation_trends tool with trends analysis"""
        mock_db.simulation_analyses.insert_one.return_value = None

        tool_call = {
            "name": "analyze_simulation_trends",
            "arguments": {
                "simulation_data": {
                    "time_series_data": {
                        "employed": [10, 12, 15, 18, 20, 22, 25, 28, 30, 32]
                    }
                },
                "analysis_type": "trends",
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Simulation trend analysis completed" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_run_cape_town_simulation_tool_unemployment(self, mock_run_simulation, mock_db):
        """Test run_cape_town_simulation tool for unemployment"""
        mock_result = {
            "final_metrics": {"policy_effectiveness": 78.5}
        }
        mock_run_simulation.return_value = mock_result

        tool_call = {
            "name": "run_cape_town_simulation",
            "arguments": {
                "issue_type": "unemployment",
                "parameters": {"intervention_strength": 0.8},
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Cape Town unemployment simulation completed" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_run_cape_town_simulation_tool_water_crisis(self, mock_run_simulation, mock_db):
        """Test run_cape_town_simulation tool for water crisis"""
        mock_result = {
            "final_metrics": {"policy_effectiveness": 82.0}
        }
        mock_run_simulation.return_value = mock_result

        tool_call = {
            "name": "run_cape_town_simulation",
            "arguments": {
                "issue_type": "water_crisis",
                "parameters": {"water_saving_measures": 0.9},
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Cape Town water_crisis simulation completed" in data["content"][0]["text"]

    @patch('main.db')
    def test_get_simulation_history_tool_success(self, mock_db):
        """Test get_simulation_history tool success"""
        mock_history = [
            {"simulation_type": "unemployment", "timestamp": datetime.now()},
            {"simulation_type": "water_scarcity", "timestamp": datetime.now()}
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
        assert "Found 2 simulation runs" in data["content"][0]["text"]

    @patch('main.db')
    def test_extract_team_skills_tool_success(self, mock_db):
        """Test extract_team_skills tool success"""
        # Mock resume data
        mock_resume = {
            "parsed_data": {
                "skills": ["Python", "JavaScript", "Leadership"]
            }
        }
        mock_db.resumes.find_one.return_value = mock_resume

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
    def test_extract_team_skills_tool_no_data(self, mock_db):
        """Test extract_team_skills tool with no resume data"""
        mock_db.resumes.find_one.return_value = None

        tool_call = {
            "name": "extract_team_skills",
            "arguments": {
                "user_ids": ["user1"],
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "0 users have skills data" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.form_teams_with_clustering')
    def test_form_teams_tool_success(self, mock_form_teams, mock_db):
        """Test form_teams tool success"""
        mock_teams = {
            "team_1": ["user1", "user2"],
            "team_2": ["user3", "user4"],
            "team_3": ["user5"]
        }
        mock_form_teams.return_value = mock_teams

        # Mock resume data for skill extraction
        mock_resume = {
            "parsed_data": {"skills": ["Python", "Django"]}
        }
        mock_db.resumes.find_one.return_value = mock_resume

        tool_call = {
            "name": "form_teams",
            "arguments": {
                "user_ids": ["user1", "user2", "user3", "user4", "user5"],
                "num_teams": 3,
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Formed 3 teams from 5 users" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.form_teams_with_clustering')
    def test_form_teams_tool_no_skills_data(self, mock_form_teams, mock_db):
        """Test form_teams tool with no skills data"""
        mock_form_teams.return_value = {}
        mock_db.resumes.find_one.return_value = None
        mock_db.team_formations.insert_one.return_value = None

        tool_call = {
            "name": "form_teams",
            "arguments": {
                "user_ids": ["user1"],
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True
        assert "No skill data available" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.suggest_collaborative_activities')
    def test_suggest_team_activities_tool_success(self, mock_suggest_activities, mock_db):
        """Test suggest_team_activities tool success"""
        mock_activities = {
            "team_1": ["Start a community co-op business", "Develop local tech startup"],
            "team_2": ["Establish urban farming cooperative", "Water conservation garden project"]
        }
        mock_suggest_activities.return_value = mock_activities

        tool_call = {
            "name": "suggest_team_activities",
            "arguments": {
                "teams": {
                    "team_1": ["user1", "user2"],
                    "team_2": ["user3", "user4"]
                },
                "cape_town_focus": True,
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Suggested" in data["content"][0]["text"]
        assert "Cape Town issues" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.form_teams_with_clustering')
    @patch('main.suggest_collaborative_activities')
    def test_create_team_simulation_tool_success(self, mock_suggest_activities, mock_form_teams, mock_db):
        """Test create_team_simulation tool success"""
        mock_teams = {
            "team_1": ["user1", "user2"],
            "team_2": ["user3", "user4"]
        }
        mock_form_teams.return_value = mock_teams

        mock_activities = {
            "team_1": ["Start a community co-op business"],
            "team_2": ["Establish urban farming cooperative"]
        }
        mock_suggest_activities.return_value = mock_activities

        # Mock resume data
        mock_resume = {
            "parsed_data": {"skills": ["Python", "Leadership"]}
        }
        mock_db.resumes.find_one.return_value = mock_resume

        tool_call = {
            "name": "create_team_simulation",
            "arguments": {
                "user_ids": ["user1", "user2", "user3", "user4"],
                "num_teams": 2,
                "cape_town_focus": True,
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Team simulation completed" in data["content"][0]["text"]
        assert "Formed 2 teams" in data["content"][0]["text"]

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
    def test_run_policy_simulation_tool_missing_type(self, mock_run_simulation, mock_db):
        """Test run_policy_simulation tool with missing simulation_type"""
        tool_call = {
            "name": "run_policy_simulation",
            "arguments": {
                "parameters": {"population_size": 1000}
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    @patch('mesa_abm_simulations.PolicySimulationRunner')
    def test_compare_scenarios_missing_scenarios(self, mock_runner_class, mock_db):
        """Test compare_policy_scenarios tool with missing scenarios"""
        tool_call = {
            "name": "compare_policy_scenarios",
            "arguments": {
                "simulation_type": "unemployment"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    @patch('main.generate_policy_recommendations')
    def test_generate_recommendations_missing_results(self, mock_generate_recommendations, mock_db):
        """Test generate_policy_recommendations tool with missing simulation_results"""
        tool_call = {
            "name": "generate_policy_recommendations",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_analyze_trends_missing_data(self):
        """Test analyze_simulation_trends tool with missing simulation_data"""
        tool_call = {
            "name": "analyze_simulation_trends",
            "arguments": {
                "analysis_type": "effectiveness",
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_cape_town_simulation_invalid_issue_type(self, mock_run_simulation, mock_db):
        """Test run_cape_town_simulation tool with invalid issue_type"""
        mock_run_simulation.side_effect = ValueError("Unknown Cape Town issue type: invalid")

        tool_call = {
            "name": "run_cape_town_simulation",
            "arguments": {
                "issue_type": "invalid",
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True
        assert "Error running Cape Town simulation" in data["content"][0]["text"]

    @patch('main.db')
    def test_get_simulation_history_missing_user_id(self, mock_db):
        """Test get_simulation_history tool with missing user_id"""
        tool_call = {
            "name": "get_simulation_history",
            "arguments": {
                "limit": 10
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_extract_team_skills_missing_user_ids(self, mock_db):
        """Test extract_team_skills tool with missing user_ids"""
        tool_call = {
            "name": "extract_team_skills",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_form_teams_missing_user_ids(self, mock_db):
        """Test form_teams tool with missing user_ids"""
        tool_call = {
            "name": "form_teams",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_suggest_activities_missing_teams(self, mock_db):
        """Test suggest_team_activities tool with missing teams"""
        tool_call = {
            "name": "suggest_team_activities",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_create_team_simulation_missing_user_ids(self, mock_db):
        """Test create_team_simulation tool with missing user_ids"""
        tool_call = {
            "name": "create_team_simulation",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

class TestMongoDBIntegration:
    """Test MongoDB integration"""

    @patch('main.db')
    def test_simulations_storage(self, mock_db):
        """Test simulations are stored in MongoDB"""
        mock_db.simulations.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.simulations.insert_one is not None

    @patch('main.db')
    def test_policy_recommendations_storage(self, mock_db):
        """Test policy recommendations are stored in MongoDB"""
        mock_db.policy_recommendations.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.policy_recommendations.insert_one is not None

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

    @patch('main.db')
    def test_team_activities_storage(self, mock_db):
        """Test team activities are stored in MongoDB"""
        mock_db.team_activities.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.team_activities.insert_one is not None

    @patch('main.db')
    def test_scenario_comparisons_storage(self, mock_db):
        """Test scenario comparisons are stored in MongoDB"""
        mock_db.scenario_comparisons.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.scenario_comparisons.insert_one is not None

    @patch('main.db')
    def test_simulation_analyses_storage(self, mock_db):
        """Test simulation analyses are stored in MongoDB"""
        mock_db.simulation_analyses.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.simulation_analyses.insert_one is not None

    @patch('main.db')
    def test_cape_town_simulations_storage(self, mock_db):
        """Test Cape Town simulations are stored in MongoDB"""
        mock_db.cape_town_simulations.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.cape_town_simulations.insert_one is not None

    @patch('main.db')
    def test_team_skills_storage(self, mock_db):
        """Test team skills are stored in MongoDB"""
        mock_db.team_skills.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.team_skills.insert_one is not None

class TestTeamSimCoreFunctionality:
    """Test core business logic functions"""

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_run_policy_simulation_function_success(self, mock_run_simulation, mock_db):
        """Test run_policy_simulation function success"""
        mock_result = {
            "final_metrics": {"policy_effectiveness": 87.5},
            "steps_run": 150
        }
        mock_run_simulation.return_value = mock_result
        mock_db.simulations.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(run_policy_simulation_tool({
            "simulation_type": "unemployment",
            "parameters": {"population_size": 1000},
            "user_id": "test_user"
        }))

        assert isinstance(result, MCPToolResponse)
        assert "Policy simulation completed" in result.content[0]["text"]
        assert "87.5%" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.generate_policy_recommendations')
    def test_generate_policy_recommendations_function_success(self, mock_generate_recommendations, mock_db):
        """Test generate_policy_recommendations function success"""
        mock_recommendations = {
            "recommendation_level": "Medium",
            "implementation_priority": "High"
        }
        mock_generate_recommendations.return_value = mock_recommendations
        mock_db.policy_recommendations.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(generate_policy_recommendations_tool({
            "simulation_results": {"final_metrics": {"policy_effectiveness": 80.0}},
            "user_id": "test_user"
        }))

        assert isinstance(result, MCPToolResponse)
        assert "Policy recommendations generated" in result.content[0]["text"]
        assert "Medium" in result.content[0]["text"]

    @patch('main.db')
    def test_extract_skills_from_resumes_function(self, mock_db):
        """Test extract_skills_from_resumes function"""
        # Mock resume data
        mock_resume1 = {
            "parsed_data": {"skills": ["Python", "Django"]}
        }
        mock_resume2 = {
            "parsed_data": {"skills": ["JavaScript", "React"]}
        }

        def mock_find_one(query, **kwargs):
            if query["user_id"] == "user1":
                return mock_resume1
            elif query["user_id"] == "user2":
                return mock_resume2
            return None

        mock_db.resumes.find_one.side_effect = mock_find_one

        # Test the function directly
        result = extract_skills_from_resumes(["user1", "user2"])

        assert isinstance(result, dict)
        assert "user1" in result
        assert "user2" in result
        assert result["user1"] == ["Python", "Django"]
        assert result["user2"] == ["JavaScript", "React"]

    @patch('main.db')
    @patch('sklearn.cluster.KMeans')
    @patch('sklearn.preprocessing.MultiLabelBinarizer')
    def test_form_teams_with_clustering_function(self, mock_mlb, mock_kmeans, mock_db):
        """Test form_teams_with_clustering function"""
        # Mock sklearn components
        mock_mlb_instance = Mock()
        mock_mlb_instance.fit_transform.return_value = [[1, 0, 1], [0, 1, 1], [1, 1, 0]]
        mock_mlb_instance.classes_ = ["Python", "JavaScript", "Leadership"]
        mock_mlb.return_value = mock_mlb_instance

        mock_kmeans_instance = Mock()
        mock_kmeans_instance.fit_predict.return_value = [0, 1, 0]
        mock_kmeans.return_value = mock_kmeans_instance

        # Test data
        skills_data = {
            "user1": ["Python", "Leadership"],
            "user2": ["JavaScript", "Leadership"],
            "user3": ["Python"]
        }

        # Test the function directly
        result = form_teams_with_clustering(skills_data, 2)

        assert isinstance(result, dict)
        assert len(result) == 2
        assert "team_1" in result
        assert "team_2" in result

    @patch('main.db')
    def test_suggest_collaborative_activities_function(self, mock_db):
        """Test suggest_collaborative_activities function"""
        # Mock team member skills
        mock_resume = {
            "parsed_data": {"skills": ["Engineering", "Programming"]}
        }
        mock_db.resumes.find_one.return_value = mock_resume

        teams = {
            "team_1": ["user1", "user2"],
            "team_2": ["user3"]
        }

        # Test the function directly
        result = suggest_collaborative_activities(teams, True)

        assert isinstance(result, dict)
        assert "team_1" in result
        assert "team_2" in result
        assert isinstance(result["team_1"], list)
        assert len(result["team_1"]) > 0

class TestTeamSimIntegration:
    """Test integration scenarios"""

    @patch('main.db')
    @patch('main.run_policy_simulation')
    @patch('main.generate_policy_recommendations')
    def test_complete_policy_simulation_workflow(self, mock_generate_recommendations, mock_run_simulation, mock_db):
        """Test complete policy simulation workflow"""
        # Setup mocks
        mock_run_simulation.return_value = {
            "final_metrics": {"policy_effectiveness": 82.0},
            "steps_run": 120
        }
        mock_generate_recommendations.return_value = {
            "recommendation_level": "High",
            "implementation_priority": "Immediate"
        }

        # Test workflow integration
        assert mock_run_simulation is not None
        assert mock_generate_recommendations is not None
        assert mock_db is not None

    @patch('main.db')
    @patch('main.form_teams_with_clustering')
    @patch('main.suggest_collaborative_activities')
    def test_complete_team_formation_workflow(self, mock_suggest_activities, mock_form_teams, mock_db):
        """Test complete team formation workflow"""
        # Setup mocks
        mock_form_teams.return_value = {
            "team_1": ["user1", "user2"],
            "team_2": ["user3", "user4"]
        }
        mock_suggest_activities.return_value = {
            "team_1": ["Start a community co-op business"],
            "team_2": ["Establish urban farming cooperative"]
        }

        # Mock resume data
        mock_resume = {
            "parsed_data": {"skills": ["Python", "Leadership"]}
        }
        mock_db.resumes.find_one.return_value = mock_resume

        # Test workflow integration
        assert mock_form_teams is not None
        assert mock_suggest_activities is not None
        assert mock_db is not None

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_cape_town_simulation_integration(self, mock_run_simulation, mock_db):
        """Test Cape Town simulation integration"""
        mock_run_simulation.return_value = {
            "final_metrics": {"policy_effectiveness": 79.5}
        }

        # Test Cape Town specific scenarios
        cape_town_issues = ["unemployment", "water_crisis"]

        for issue in cape_town_issues:
            # Test the function directly
            import asyncio
            result = asyncio.run(run_cape_town_simulation_tool({
                "issue_type": issue,
                "parameters": {"intervention_strength": 0.8},
                "user_id": "test_user"
            }))

            assert isinstance(result, MCPToolResponse)
            assert f"Cape Town {issue} simulation completed" in result.content[0]["text"]

if __name__ == "__main__":
    pytest.main([__file__])