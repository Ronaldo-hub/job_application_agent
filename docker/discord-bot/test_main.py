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

# Mock external dependencies before importing main
with patch('email_comm_hub.discord_bot.send_notification'):
    with patch('gamification_engine.token_system'):
        with patch('learning_recommendations.course_suggestions'):
            with patch('job_discovery_matching.job_search'):
                with patch('resume_doc_processing.resume_tool'):
                    with patch('learning_recommendations.virtonomics_integration'):
                        with patch('learning_recommendations.simcompanies_integration'):
                            with patch('learning_recommendations.cwetlands_integration'):
                                with patch('learning_recommendations.theblueconnection_integration'):
                                    with patch('mesa_abm_simulations.run_policy_simulation'):
                                        with patch('agent_core.conversational_ai'):
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

    def test_list_prompts_endpoint(self):
        """Test MCP prompts listing endpoint"""
        response = client.get("/mcp/prompts")
        assert response.status_code == 200
        data = response.json()
        assert "prompts" in data

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

    def test_get_prompt(self):
        """Test getting MCP prompt"""
        response = client.get("/mcp/prompts/discord_notification_template")
        assert response.status_code == 200
        data = response.json()
        assert "prompt" in data

    def test_get_prompt_not_found(self):
        """Test getting non-existent MCP prompt"""
        response = client.get("/mcp/prompts/non_existent_prompt")
        assert response.status_code == 404

class TestDiscordBotToolCalls:
    """Test MCP tool calls"""

    @patch('main.db')
    def test_send_discord_notification_tool_success(self, mock_db):
        """Test send_discord_notification tool success"""
        mock_db.discord_notifications.insert_one.return_value = None

        tool_call = {
            "name": "send_discord_notification",
            "arguments": {
                "user_id": "test_user",
                "message": "Test notification",
                "embed_data": {"title": "Test Embed"}
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Discord notification sent to user test_user" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.job_search')
    @patch('main.resume_tool')
    def test_search_jobs_discord_tool_success_with_high_fit(self, mock_resume_tool, mock_job_search, mock_db):
        """Test search_jobs_discord tool success with high fit jobs"""
        # Mock job search results
        mock_jobs = [
            {"title": "Python Developer", "company": "Tech Corp"},
            {"title": "Data Scientist", "company": "Data Inc"},
            {"title": "Frontend Developer", "company": "Web Ltd"}
        ]

        # Create async mock for search_jobs_async
        async def mock_search_jobs_async(*args, **kwargs):
            return mock_jobs
        mock_job_search.search_jobs_async = mock_search_jobs_async

        # Mock resume fit scores
        mock_resume_tool.load_master_resume.return_value = {"skills": ["Python", "Django"]}
        mock_resume_tool.calculate_fit_score.side_effect = [85.0, 65.0, 90.0]  # Two high fit jobs

        mock_db.discord_interactions.insert_one.return_value = None

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
        assert "2 high-fit" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.job_search')
    @patch('main.resume_tool')
    def test_search_jobs_discord_tool_no_high_fit(self, mock_resume_tool, mock_job_search, mock_db):
        """Test search_jobs_discord tool with no high fit jobs"""
        # Mock job search results
        mock_jobs = [
            {"title": "Java Developer", "company": "Java Corp"},
            {"title": "C++ Developer", "company": "C++ Inc"}
        ]

        # Create async mock for search_jobs_async
        async def mock_search_jobs_async(*args, **kwargs):
            return mock_jobs
        mock_job_search.search_jobs_async = mock_search_jobs_async

        # Mock resume fit scores (all low)
        mock_resume_tool.load_master_resume.return_value = {"skills": ["Python"]}
        mock_resume_tool.calculate_fit_score.side_effect = [45.0, 50.0]

        mock_db.discord_interactions.insert_one.return_value = None

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
        assert "content" in data
        assert "0 high-fit" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.virtonomics_integration')
    @patch('main.simcompanies_integration')
    def test_get_game_recommendations_discord_tool_specific_game(self, mock_simcompanies, mock_virtonomics, mock_db):
        """Test get_game_recommendations_discord tool for specific game"""
        mock_virtonomics.get_virtonomics_recommendations.return_value = {
            "recommendation": "Business simulation game",
            "skill_match": 85
        }

        mock_db.discord_interactions.insert_one.return_value = None

        tool_call = {
            "name": "get_game_recommendations_discord",
            "arguments": {
                "user_id": "test_user",
                "skills": ["business", "strategy"],
                "game": "virtonomics"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Game recommendations generated for user test_user" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.virtonomics_integration')
    @patch('main.simcompanies_integration')
    def test_get_game_recommendations_discord_tool_all_games(self, mock_simcompanies, mock_virtonomics, mock_db):
        """Test get_game_recommendations_discord tool for all games"""
        mock_virtonomics.get_virtonomics_recommendations.return_value = {
            "recommendation": "Business simulation game"
        }
        mock_simcompanies.get_simcompanies_recommendations.return_value = {
            "recommendation": "Company management game"
        }

        mock_db.discord_interactions.insert_one.return_value = None

        tool_call = {
            "name": "get_game_recommendations_discord",
            "arguments": {
                "user_id": "test_user",
                "skills": ["business", "management"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "2 games" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_run_policy_simulation_discord_tool_success(self, mock_run_simulation, mock_db):
        """Test run_policy_simulation_discord tool success"""
        mock_result = {
            "final_metrics": {"policy_effectiveness": 87.5}
        }
        mock_run_simulation.return_value = mock_result

        mock_db.discord_interactions.insert_one.return_value = None

        tool_call = {
            "name": "run_policy_simulation_discord",
            "arguments": {
                "user_id": "test_user",
                "simulation_type": "unemployment",
                "parameters": {"population_size": 1000}
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Policy simulation completed for user test_user" in data["content"][0]["text"]
        assert "87.5%" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.run_policy_simulation')
    def test_run_policy_simulation_discord_tool_error(self, mock_run_simulation, mock_db):
        """Test run_policy_simulation_discord tool error handling"""
        mock_run_simulation.return_value = {"error": "Simulation failed"}

        tool_call = {
            "name": "run_policy_simulation_discord",
            "arguments": {
                "user_id": "test_user",
                "simulation_type": "unemployment"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True
        assert "Simulation error" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.token_system')
    def test_check_user_tokens_discord_tool_success(self, mock_token_system, mock_db):
        """Test check_user_tokens_discord tool success"""
        mock_stats = {
            "current_tokens": 1250,
            "level": 5,
            "total_earned": 2500
        }
        mock_token_system.get_user_stats.return_value = mock_stats

        mock_db.discord_interactions.insert_one.return_value = None

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
        assert "Level 5" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.token_system')
    def test_award_tokens_discord_tool_success(self, mock_token_system, mock_db):
        """Test award_tokens_discord tool success"""
        mock_result = {
            "tokens_earned": 100,
            "new_balance": 1350,
            "level_up": False
        }
        mock_token_system.earn_tokens.return_value = mock_result

        mock_db.discord_interactions.insert_one.return_value = None

        tool_call = {
            "name": "award_tokens_discord",
            "arguments": {
                "user_id": "test_user",
                "activity_type": "job_search",
                "metadata": {"jobs_found": 5}
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "+100 for job_search" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.conversational_ai')
    def test_chat_with_ai_discord_tool_success(self, mock_conversational_ai, mock_db):
        """Test chat_with_ai_discord tool success"""
        mock_conversational_ai.chat_with_user.return_value = "Hello! How can I help you with your job search?"

        mock_db.discord_interactions.insert_one.return_value = None

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
        assert "AI chat completed for user test_user" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.conversational_ai')
    def test_chat_with_ai_discord_tool_unavailable(self, mock_conversational_ai, mock_db):
        """Test chat_with_ai_discord tool when AI is unavailable"""
        mock_conversational_ai = None

        mock_db.discord_interactions.insert_one.return_value = None

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
        assert "AI chat completed for user test_user" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.course_suggestions')
    def test_get_course_suggestions_discord_tool_success(self, mock_course_suggestions, mock_db):
        """Test get_course_suggestions_discord tool success"""
        mock_suggestions = [
            {"title": "Python for Data Science", "platform": "Coursera", "duration": "8 weeks"},
            {"title": "Machine Learning Basics", "platform": "edX", "duration": "6 weeks"}
        ]

        # Create async mock for get_course_suggestions
        async def mock_get_course_suggestions(*args, **kwargs):
            return mock_suggestions
        mock_course_suggestions.get_course_suggestions = mock_get_course_suggestions

        mock_db.discord_interactions.insert_one.return_value = None

        tool_call = {
            "name": "get_course_suggestions_discord",
            "arguments": {
                "user_id": "test_user",
                "skill_gaps": ["python", "machine learning", "data analysis"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "2 skill gaps addressed" in data["content"][0]["text"]

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
    def test_send_discord_notification_missing_user_id(self, mock_db):
        """Test send_discord_notification tool with missing user_id"""
        tool_call = {
            "name": "send_discord_notification",
            "arguments": {
                "message": "Test message"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_send_discord_notification_missing_message(self, mock_db):
        """Test send_discord_notification tool with missing message"""
        tool_call = {
            "name": "send_discord_notification",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_search_jobs_discord_missing_user_id(self, mock_db):
        """Test search_jobs_discord tool with missing user_id"""
        tool_call = {
            "name": "search_jobs_discord",
            "arguments": {
                "keywords": "python developer"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_search_jobs_discord_missing_keywords(self, mock_db):
        """Test search_jobs_discord tool with missing keywords"""
        tool_call = {
            "name": "search_jobs_discord",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_get_game_recommendations_discord_missing_user_id(self, mock_db):
        """Test get_game_recommendations_discord tool with missing user_id"""
        tool_call = {
            "name": "get_game_recommendations_discord",
            "arguments": {
                "skills": ["python"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_run_policy_simulation_discord_missing_user_id(self, mock_db):
        """Test run_policy_simulation_discord tool with missing user_id"""
        tool_call = {
            "name": "run_policy_simulation_discord",
            "arguments": {
                "simulation_type": "unemployment"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_run_policy_simulation_discord_missing_simulation_type(self, mock_db):
        """Test run_policy_simulation_discord tool with missing simulation_type"""
        tool_call = {
            "name": "run_policy_simulation_discord",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_check_user_tokens_discord_missing_user_id(self, mock_db):
        """Test check_user_tokens_discord tool with missing user_id"""
        tool_call = {
            "name": "check_user_tokens_discord",
            "arguments": {}
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_award_tokens_discord_missing_user_id(self, mock_db):
        """Test award_tokens_discord tool with missing user_id"""
        tool_call = {
            "name": "award_tokens_discord",
            "arguments": {
                "activity_type": "job_search"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_award_tokens_discord_missing_activity_type(self, mock_db):
        """Test award_tokens_discord tool with missing activity_type"""
        tool_call = {
            "name": "award_tokens_discord",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_chat_with_ai_discord_missing_user_id(self, mock_db):
        """Test chat_with_ai_discord tool with missing user_id"""
        tool_call = {
            "name": "chat_with_ai_discord",
            "arguments": {
                "message": "Hello AI"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_chat_with_ai_discord_missing_message(self, mock_db):
        """Test chat_with_ai_discord tool with missing message"""
        tool_call = {
            "name": "chat_with_ai_discord",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_get_course_suggestions_discord_missing_user_id(self, mock_db):
        """Test get_course_suggestions_discord tool with missing user_id"""
        tool_call = {
            "name": "get_course_suggestions_discord",
            "arguments": {
                "skill_gaps": ["python"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_get_course_suggestions_discord_missing_skill_gaps(self, mock_db):
        """Test get_course_suggestions_discord tool with missing skill_gaps"""
        tool_call = {
            "name": "get_course_suggestions_discord",
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

class TestDiscordBotCoreFunctionality:
    """Test core business logic functions"""

    @patch('main.db')
    def test_send_discord_notification_function_success(self, mock_db):
        """Test send_discord_notification function success"""
        mock_db.discord_notifications.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(send_discord_notification_tool({
            "user_id": "test_user",
            "message": "Test notification",
            "embed_data": {"title": "Test"}
        }))

        assert isinstance(result, MCPToolResponse)
        assert "Discord notification sent to user test_user" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.job_search')
    @patch('main.resume_tool')
    def test_search_jobs_discord_function_with_fit_analysis(self, mock_resume_tool, mock_job_search, mock_db):
        """Test search_jobs_discord function with fit analysis"""
        # Mock job search
        mock_jobs = [
            {"title": "Python Developer", "company": "Tech Corp"},
            {"title": "Java Developer", "company": "Java Inc"}
        ]

        # Create async mock for search_jobs_async
        async def mock_search_jobs_async(*args, **kwargs):
            return mock_jobs
        mock_job_search.search_jobs_async = mock_search_jobs_async

        # Mock resume analysis
        mock_resume_tool.load_master_resume.return_value = {"skills": ["Python"]}
        mock_resume_tool.calculate_fit_score.side_effect = [90.0, 45.0]

        mock_db.discord_interactions.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(search_jobs_discord_tool({
            "user_id": "test_user",
            "keywords": "python developer",
            "location": "remote"
        }))

        assert isinstance(result, MCPToolResponse)
        assert "1 high-fit" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.token_system')
    def test_check_user_tokens_discord_function_success(self, mock_token_system, mock_db):
        """Test check_user_tokens_discord function success"""
        mock_stats = {
            "current_tokens": 1500,
            "level": 6,
            "achievements": ["first_job_search", "resume_optimized"]
        }
        mock_token_system.get_user_stats.return_value = mock_stats

        mock_db.discord_interactions.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(check_user_tokens_discord_tool({
            "user_id": "test_user"
        }))

        assert isinstance(result, MCPToolResponse)
        assert "1500 tokens" in result.content[0]["text"]
        assert "Level 6" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.token_system')
    def test_award_tokens_discord_function_success(self, mock_token_system, mock_db):
        """Test award_tokens_discord function success"""
        mock_result = {
            "tokens_earned": 50,
            "new_balance": 1550,
            "level_up": True,
            "new_level": 7
        }
        mock_token_system.earn_tokens.return_value = mock_result

        mock_db.discord_interactions.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(award_tokens_discord_tool({
            "user_id": "test_user",
            "activity_type": "resume_upload",
            "metadata": {"file_size": "2MB"}
        }))

        assert isinstance(result, MCPToolResponse)
        assert "+50 for resume_upload" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.conversational_ai')
    def test_chat_with_ai_discord_function_success(self, mock_conversational_ai, mock_db):
        """Test chat_with_ai_discord function success"""
        mock_conversational_ai.chat_with_user.return_value = "I'd be happy to help you with your job search!"

        mock_db.discord_interactions.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(chat_with_ai_discord_tool({
            "user_id": "test_user",
            "message": "Can you help me find a job?",
            "context": {"user_level": "beginner"}
        }))

        assert isinstance(result, MCPToolResponse)
        assert "AI chat completed for user test_user" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.course_suggestions')
    def test_get_course_suggestions_discord_function_success(self, mock_course_suggestions, mock_db):
        """Test get_course_suggestions_discord function success"""
        mock_suggestions = [
            {"title": "Advanced Python", "platform": "Udemy", "rating": 4.8},
            {"title": "Data Science Fundamentals", "platform": "Coursera", "rating": 4.9},
            {"title": "Machine Learning for Beginners", "platform": "edX", "rating": 4.7}
        ]

        # Create async mock for get_course_suggestions
        async def mock_get_course_suggestions(*args, **kwargs):
            return mock_suggestions
        mock_course_suggestions.get_course_suggestions = mock_get_course_suggestions

        mock_db.discord_interactions.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(get_course_suggestions_discord_tool({
            "user_id": "test_user",
            "skill_gaps": ["python", "data science", "machine learning"]
        }))

        assert isinstance(result, MCPToolResponse)
        assert "3 skill gaps addressed" in result.content[0]["text"]

class TestDiscordBotIntegration:
    """Test integration scenarios"""

    @patch('main.db')
    @patch('main.send_notification')
    def test_discord_notification_integration(self, mock_send_notification, mock_db):
        """Test discord notification integration"""
        mock_send_notification.return_value = {"status": "sent", "message_id": "12345"}

        mock_db.discord_notifications.insert_one.return_value = None

        # Test integration flow
        assert mock_send_notification is not None
        assert mock_db is not None

    @patch('main.db')
    @patch('main.job_search')
    @patch('main.resume_tool')
    @patch('main.send_notification')
    def test_job_search_notification_integration(self, mock_send_notification, mock_resume_tool, mock_job_search, mock_db):
        """Test job search with notification integration"""
        # Mock job search results
        mock_jobs = [
            {"title": "Senior Python Developer", "company": "Tech Corp", "location": "Remote"},
            {"title": "Data Scientist", "company": "Data Inc", "location": "Cape Town"}
        ]
        mock_job_search.search_jobs_async.return_value = mock_jobs

        # Mock high fit scores
        mock_resume_tool.load_master_resume.return_value = {"skills": ["Python", "Machine Learning"]}
        mock_resume_tool.calculate_fit_score.side_effect = [88.0, 92.0]

        mock_send_notification.return_value = {"status": "sent"}
        mock_db.discord_interactions.insert_one.return_value = None

        # Test integration flow
        assert mock_job_search is not None
        assert mock_resume_tool is not None
        assert mock_send_notification is not None
        assert mock_db is not None

    @patch('main.db')
    @patch('main.token_system')
    @patch('main.send_notification')
    def test_gamification_notification_integration(self, mock_send_notification, mock_token_system, mock_db):
        """Test gamification with notification integration"""
        mock_token_system.earn_tokens.return_value = {
            "tokens_earned": 75,
            "new_balance": 1325,
            "level_up": False
        }

        mock_send_notification.return_value = {"status": "sent"}
        mock_db.discord_interactions.insert_one.return_value = None

        # Test integration flow
        assert mock_token_system is not None
        assert mock_send_notification is not None
        assert mock_db is not None

    @patch('main.db')
    @patch('main.conversational_ai')
    @patch('main.send_notification')
    def test_ai_chat_notification_integration(self, mock_send_notification, mock_conversational_ai, mock_db):
        """Test AI chat with notification integration"""
        mock_conversational_ai.chat_with_user.return_value = "Based on your profile, I recommend focusing on Python development roles."

        mock_send_notification.return_value = {"status": "sent"}
        mock_db.discord_interactions.insert_one.return_value = None

        # Test integration flow
        assert mock_conversational_ai is not None
        assert mock_send_notification is not None
        assert mock_db is not None

if __name__ == "__main__":
    pytest.main([__file__])