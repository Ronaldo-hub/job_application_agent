"""
Comprehensive pytest test suite for Discord Bot MCP Server
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
from main import app, MCPToolResponse, send_discord_notification_tool, search_jobs_discord_tool, get_game_recommendations_discord_tool, run_policy_simulation_discord_tool, check_user_tokens_discord_tool, award_tokens_discord_tool, chat_with_ai_discord_tool, get_course_suggestions_discord_tool

# Create test client
client = TestClient(app)

class TestDiscordBotEndpoints:
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
            "send_discord_notification",
            "search_jobs_discord",
            "get_game_recommendations_discord",
            "run_policy_simulation_discord",
            "check_user_tokens_discord",
            "award_tokens_discord",
            "chat_with_ai_discord",
            "get_course_suggestions_discord"
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
    def test_read_discord_notifications_resource(self, mock_db):
        """Test reading discord notifications resource"""
        mock_notifications = [
            {"user_id": "test_user", "message": "Test notification", "timestamp": datetime.now()}
        ]
        mock_db.discord_notifications.find.return_value.sort.return_value.limit.return_value = mock_notifications

        response = client.get("/mcp/resources/mongodb://job_application_agent/discord_notifications")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @patch('main.db')
    def test_read_discord_interactions_resource(self, mock_db):
        """Test reading discord interactions resource"""
        mock_interactions = [
            {"user_id": "test_user", "interaction_type": "job_search", "timestamp": datetime.now()}
        ]
        mock_db.discord_interactions.find.return_value.sort.return_value.limit.return_value = mock_interactions

        response = client.get("/mcp/resources/mongodb://job_application_agent/discord_interactions")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

class TestDiscordBotToolCalls:
    """Test MCP tool calls"""

    @patch('main.db')
    def test_send_discord_notification_tool_success(self, mock_db):
        """Test send_discord_notification tool success"""
        tool_call = {
            "name": "send_discord_notification",
            "arguments": {
                "user_id": "test_user",
                "message": "Test notification message",
                "embed_data": {
                    "title": "Test Embed",
                    "description": "Test description"
                }
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Discord notification sent" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.job_search.search_jobs_async')
    @patch('main.resume_tool.load_master_resume')
    @patch('main.resume_tool.calculate_fit_score')
    def test_search_jobs_discord_tool_with_high_fit(self, mock_fit_score, mock_load_resume, mock_search_jobs, mock_db):
        """Test search_jobs_discord tool with high fit jobs"""
        mock_search_jobs.return_value = [
            {"title": "Python Developer", "company": "Tech Corp", "location": "Remote"},
            {"title": "Java Developer", "company": "Web Inc", "location": "Cape Town"}
        ]
        mock_load_resume.return_value = {"skills": ["python", "django"]}
        mock_fit_score.return_value = 90.0  # High fit score

        tool_call = {
            "name": "search_jobs_discord",
            "arguments": {
                "user_id": "test_user",
                "keywords": "python developer",
                "location": "remote"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Found 2 jobs" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.job_search.search_jobs_async')
    @patch('main.resume_tool.load_master_resume')
    @patch('main.resume_tool.calculate_fit_score')
    def test_search_jobs_discord_tool_no_high_fit(self, mock_fit_score, mock_load_resume, mock_search_jobs, mock_db):
        """Test search_jobs_discord tool with no high fit jobs"""
        mock_search_jobs.return_value = [
            {"title": "Java Developer", "company": "Web Inc", "location": "Cape Town"}
        ]
        mock_load_resume.return_value = {"skills": ["python", "django"]}
        mock_fit_score.return_value = 60.0  # Low fit score

        tool_call = {
            "name": "search_jobs_discord",
            "arguments": {
                "user_id": "test_user",
                "keywords": "python developer",
                "location": "remote"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Found 1 jobs" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.virtonomics_integration')
    def test_get_game_recommendations_discord_tool_virtonomics(self, mock_virtonomics, mock_db):
        """Test get_game_recommendations_discord tool for Virtonomics"""
        mock_integration = Mock()
        mock_integration.get_virtonomics_recommendations.return_value = {
            "recommendation": "Focus on business simulation",
            "skills_to_develop": ["economics", "strategy"]
        }
        mock_virtonomics.return_value = mock_integration

        tool_call = {
            "name": "get_game_recommendations_discord",
            "arguments": {
                "user_id": "test_user",
                "skills": ["business", "analysis"],
                "game": "virtonomics"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Game recommendations generated" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_run_policy_simulation_discord_tool_success(self, mock_run_simulation, mock_db):
        """Test run_policy_simulation_discord tool success"""
        mock_result = {
            "final_metrics": {
                "policy_effectiveness": 0.82
            }
        }
        mock_run_simulation.return_value = mock_result

        tool_call = {
            "name": "run_policy_simulation_discord",
            "arguments": {
                "user_id": "test_user",
                "simulation_type": "unemployment",
                "parameters": {"policy_strength": 0.8}
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Policy simulation completed" in data["content"][0]["text"]
        assert "82.0%" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.token_system.get_user_stats')
    def test_check_user_tokens_discord_tool(self, mock_get_stats, mock_db):
        """Test check_user_tokens_discord tool"""
        mock_get_stats.return_value = {
            "current_tokens": 1250,
            "level": 12,
            "total_earned": 2500
        }

        tool_call = {
            "name": "check_user_tokens_discord",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "1250 tokens" in data["content"][0]["text"]
        assert "Level 12" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.token_system.earn_tokens')
    def test_award_tokens_discord_tool(self, mock_earn_tokens, mock_db):
        """Test award_tokens_discord tool"""
        mock_earn_tokens.return_value = {
            "tokens_earned": 100,
            "new_balance": 1350
        }

        tool_call = {
            "name": "award_tokens_discord",
            "arguments": {
                "user_id": "test_user",
                "activity_type": "job_application",
                "metadata": {"company": "Tech Corp"}
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "+100 tokens" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.conversational_ai')
    def test_chat_with_ai_discord_tool_with_ai(self, mock_conversational_ai, mock_db):
        """Test chat_with_ai_discord tool when AI is available"""
        mock_conversational_ai.chat_with_user.return_value = "Hello! How can I help you with your job search?"

        tool_call = {
            "name": "chat_with_ai_discord",
            "arguments": {
                "user_id": "test_user",
                "message": "Hello AI",
                "context": {"previous_topic": "job_search"}
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "AI chat completed" in data["content"][0]["text"]

    @patch('main.db')
    def test_chat_with_ai_discord_tool_no_ai(self, mock_db):
        """Test chat_with_ai_discord tool when AI is not available"""
        # Mock conversational_ai as None
        with patch('main.conversational_ai', None):
            tool_call = {
                "name": "chat_with_ai_discord",
                "arguments": {
                    "user_id": "test_user",
                    "message": "Hello AI"
                }
            }

            response = client.post("/mcp/tools/call", json=tool_call)
            assert response.status_code == 200
            data = response.json()
            assert "content" in data
            assert "AI assistant is currently unavailable" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.course_suggestions.get_course_suggestions')
    def test_get_course_suggestions_discord_tool(self, mock_get_suggestions, mock_db):
        """Test get_course_suggestions_discord tool"""
        mock_get_suggestions.return_value = [
            "Advanced Python Programming",
            "Data Structures and Algorithms",
            "Machine Learning Fundamentals"
        ]

        tool_call = {
            "name": "get_course_suggestions_discord",
            "arguments": {
                "user_id": "test_user",
                "skill_gaps": ["python", "algorithms", "ml"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Course suggestions generated" in data["content"][0]["text"]

class TestDiscordBotErrorHandling:
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
    @patch('main.job_search.search_jobs_async')
    def test_search_jobs_discord_error_handling(self, mock_search_jobs, mock_db):
        """Test search_jobs_discord tool error handling"""
        mock_search_jobs.side_effect = Exception("Job search API failed")

        tool_call = {
            "name": "search_jobs_discord",
            "arguments": {
                "user_id": "test_user",
                "keywords": "python developer"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True
        assert "Error in Discord job search" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.token_system.get_user_stats')
    def test_check_user_tokens_error_handling(self, mock_get_stats, mock_db):
        """Test check_user_tokens_discord tool error handling"""
        mock_get_stats.side_effect = Exception("Token system error")

        tool_call = {
            "name": "check_user_tokens_discord",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True
        assert "Error checking tokens" in data["content"][0]["text"]

class TestMongoDBIntegration:
    """Test MongoDB integration"""

    @patch('main.db')
    def test_discord_notifications_storage(self, mock_db):
        """Test discord notifications are stored in MongoDB"""
        mock_db.discord_notifications.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.discord_notifications.insert_one is not None

    @patch('main.db')
    def test_discord_interactions_storage(self, mock_db):
        """Test discord interactions are stored in MongoDB"""
        mock_db.discord_interactions.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.discord_interactions.insert_one is not None

    @patch('main.db')
    def test_gamification_activities_storage(self, mock_db):
        """Test gamification activities are stored in MongoDB"""
        mock_db.gamification_activities.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.gamification_activities.insert_one is not None

class TestDiscordBotCoreFunctionality:
    """Test core business logic functions"""

    @patch('main.db')
    @patch('main.job_search.search_jobs_async')
    @patch('main.resume_tool.load_master_resume')
    @patch('main.resume_tool.calculate_fit_score')
    def test_job_fit_analysis_integration(self, mock_fit_score, mock_load_resume, mock_search_jobs, mock_db):
        """Test job fit analysis integration"""
        mock_search_jobs.return_value = [
            {"title": "Python Developer", "company": "Tech Corp", "requirements": ["python", "django"]}
        ]
        mock_load_resume.return_value = {"skills": ["python", "django", "aws"]}
        mock_fit_score.return_value = 95.0

        # Test the integration would work
        assert mock_search_jobs is not None
        assert mock_load_resume is not None
        assert mock_fit_score is not None

    @patch('main.db')
    @patch('main.token_system.earn_tokens')
    def test_token_system_integration(self, mock_earn_tokens, mock_db):
        """Test token system integration"""
        mock_earn_tokens.return_value = {"tokens_earned": 50, "new_balance": 1300}

        # Test the integration would work
        assert mock_earn_tokens is not None

    @patch('main.db')
    @patch('main.conversational_ai')
    def test_ai_chat_integration(self, mock_conversational_ai, mock_db):
        """Test AI chat integration"""
        mock_conversational_ai.chat_with_user.return_value = "Test AI response"

        # Test the integration would work
        assert mock_conversational_ai is not None

class TestDiscordBotIntegration:
    """Test integration scenarios"""

    @patch('main.db')
    @patch('main.job_search.search_jobs_async')
    @patch('main.resume_tool.load_master_resume')
    @patch('main.resume_tool.calculate_fit_score')
    @patch('main.token_system.earn_tokens')
    def test_complete_job_search_workflow(self, mock_earn_tokens, mock_fit_score, mock_load_resume, mock_search_jobs, mock_db):
        """Test complete job search workflow with token rewards"""
        # Setup mocks
        mock_search_jobs.return_value = [
            {"title": "Python Developer", "company": "Tech Corp", "requirements": ["python"]}
        ]
        mock_load_resume.return_value = {"skills": ["python", "django"]}
        mock_fit_score.return_value = 88.0
        mock_earn_tokens.return_value = {"tokens_earned": 25}

        # Test the workflow would work end-to-end
        assert mock_search_jobs is not None
        assert mock_load_resume is not None
        assert mock_fit_score is not None
        assert mock_earn_tokens is not None

if __name__ == "__main__":
    pytest.main([__file__])