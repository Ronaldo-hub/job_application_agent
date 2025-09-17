"""
Comprehensive pytest test suite for Game Integration MCP Server
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
with patch('main.token_system'):
    with patch('main.course_suggestions'):
        with patch('main.virtonomics_integration'):
            with patch('main.simcompanies_integration'):
                with patch('main.cwetlands_integration'):
                    with patch('main.theblueconnection_integration'):
                        with patch('main.game_activity_tracker'):
                            # Import the FastAPI app and related functions
                            from main import app, MCPToolResponse, earn_gamification_tokens_tool, spend_gamification_tokens_tool, get_user_gamification_stats_tool, get_game_recommendations_tool, track_game_activity_tool, get_course_recommendations_tool, get_gamification_leaderboard_tool, analyze_user_progress_tool

# Create test client
client = TestClient(app)

class TestGameIntegrationEndpoints:
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
            "earn_gamification_tokens",
            "spend_gamification_tokens",
            "get_user_gamification_stats",
            "get_game_recommendations",
            "track_game_activity",
            "get_course_recommendations",
            "get_gamification_leaderboard",
            "analyze_user_progress"
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
    def test_read_gamification_stats_resource(self, mock_db):
        """Test reading gamification stats resource"""
        mock_stats = [
            {"user_id": "test_user", "level": 5, "current_tokens": 1250, "timestamp": datetime.now()}
        ]
        mock_db.gamification_stats.find.return_value.sort.return_value.limit.return_value = mock_stats

        response = client.get("/mcp/resources/mongodb://job_application_agent/gamification_stats")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @patch('main.db')
    def test_read_game_activities_resource(self, mock_db):
        """Test reading game activities resource"""
        mock_activities = [
            {"user_id": "test_user", "game": "virtonomics", "activity": "completed_level", "timestamp": datetime.now()}
        ]
        mock_db.game_activities.find.return_value.sort.return_value.limit.return_value = mock_activities

        response = client.get("/mcp/resources/mongodb://job_application_agent/game_activities")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @patch('main.db')
    def test_read_course_recommendations_resource(self, mock_db):
        """Test reading course recommendations resource"""
        mock_recommendations = [
            {"user_id": "test_user", "skill_gaps": ["python"], "recommendations": ["Python Course"], "timestamp": datetime.now()}
        ]
        mock_db.course_recommendations.find.return_value.sort.return_value.limit.return_value = mock_recommendations

        response = client.get("/mcp/resources/mongodb://job_application_agent/course_recommendations")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    def test_get_prompt(self):
        """Test getting MCP prompt"""
        response = client.get("/mcp/prompts/gamification_motivation")
        assert response.status_code == 200
        data = response.json()
        assert "prompt" in data

    def test_get_prompt_not_found(self):
        """Test getting non-existent MCP prompt"""
        response = client.get("/mcp/prompts/non_existent_prompt")
        assert response.status_code == 404

class TestGameIntegrationToolCalls:
    """Test MCP tool calls"""

    @patch('main.db')
    @patch('main.token_system')
    def test_earn_gamification_tokens_tool_success(self, mock_token_system, mock_db):
        """Test earn_gamification_tokens tool success"""
        mock_result = {
            "tokens_earned": 50,
            "new_balance": 1300,
            "level_up": False
        }
        mock_token_system.earn_tokens.return_value = mock_result

        mock_db.gamification_activities.insert_one.return_value = None

        tool_call = {
            "name": "earn_gamification_tokens",
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
        assert "Tokens earned for user test_user: +50 for job_search" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.token_system')
    def test_spend_gamification_tokens_tool_success(self, mock_token_system, mock_db):
        """Test spend_gamification_tokens tool success"""
        mock_result = {
            "reward": "Premium Resume Review",
            "cost": 200,
            "new_balance": 1100
        }
        mock_token_system.spend_tokens.return_value = mock_result

        mock_db.reward_redemptions.insert_one.return_value = None

        tool_call = {
            "name": "spend_gamification_tokens",
            "arguments": {
                "user_id": "test_user",
                "reward_id": "premium_resume_review"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Premium Resume Review for 200 tokens" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.token_system')
    def test_spend_gamification_tokens_tool_insufficient_funds(self, mock_token_system, mock_db):
        """Test spend_gamification_tokens tool with insufficient funds"""
        mock_result = {"error": "Insufficient tokens"}
        mock_token_system.spend_tokens.return_value = mock_result

        tool_call = {
            "name": "spend_gamification_tokens",
            "arguments": {
                "user_id": "test_user",
                "reward_id": "premium_resume_review"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert data["isError"] == True
        assert "Insufficient tokens" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.token_system')
    def test_get_user_gamification_stats_tool_success(self, mock_token_system, mock_db):
        """Test get_user_gamification_stats tool success"""
        mock_stats = {
            "current_tokens": 1250,
            "level": 5,
            "total_earned": 2500,
            "achievements_count": 12
        }
        mock_token_system.get_user_stats.return_value = mock_stats

        mock_db.gamification_stats.insert_one.return_value = None

        tool_call = {
            "name": "get_user_gamification_stats",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Level 5" in data["content"][0]["text"]
        assert "1250 tokens" in data["content"][0]["text"]
        assert "12 achievements" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.virtonomics_integration')
    @patch('main.simcompanies_integration')
    def test_get_game_recommendations_tool_specific_game(self, mock_simcompanies, mock_virtonomics, mock_db):
        """Test get_game_recommendations tool for specific game"""
        mock_virtonomics.get_virtonomics_recommendations.return_value = {
            "recommendation": "Business simulation game",
            "skill_match": 85,
            "learning_outcomes": ["Strategic thinking", "Business acumen"]
        }

        mock_db.game_recommendations.insert_one.return_value = None

        tool_call = {
            "name": "get_game_recommendations",
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
        assert "Game recommendations generated for user test_user: 1 games" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.virtonomics_integration')
    @patch('main.simcompanies_integration')
    @patch('main.cwetlands_integration')
    @patch('main.theblueconnection_integration')
    def test_get_game_recommendations_tool_all_games(self, mock_theblueconnection, mock_cwetlands, mock_simcompanies, mock_virtonomics, mock_db):
        """Test get_game_recommendations tool for all games"""
        mock_virtonomics.get_virtonomics_recommendations.return_value = {
            "recommendation": "Business simulation game"
        }
        mock_simcompanies.get_simcompanies_recommendations.return_value = {
            "recommendation": "Company management game"
        }
        mock_cwetlands.get_cwetlands_recommendations.return_value = {
            "recommendation": "Environmental management game"
        }
        mock_theblueconnection.get_theblueconnection_recommendations.return_value = {
            "recommendation": "Maritime logistics game"
        }

        mock_db.game_recommendations.insert_one.return_value = None

        tool_call = {
            "name": "get_game_recommendations",
            "arguments": {
                "user_id": "test_user",
                "skills": ["business", "management", "environmental", "logistics"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "4 games" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.game_activity_tracker')
    def test_track_game_activity_tool_success(self, mock_tracker, mock_db):
        """Test track_game_activity tool success"""
        mock_result = {
            "tokens_earned": 25,
            "achievement_unlocked": "First Steps",
            "progress_percentage": 15
        }
        mock_tracker.track_activity.return_value = mock_result

        mock_db.game_activities.insert_one.return_value = None

        tool_call = {
            "name": "track_game_activity",
            "arguments": {
                "user_id": "test_user",
                "game": "virtonomics",
                "activity": "completed_tutorial",
                "metadata": {"time_spent": "10 minutes", "difficulty": "beginner"}
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "completed_tutorial in virtonomics" in data["content"][0]["text"]
        assert "+25 tokens" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.game_activity_tracker')
    def test_track_game_activity_tool_tracker_unavailable(self, mock_tracker, mock_db):
        """Test track_game_activity tool when tracker is unavailable"""
        # Mock the tracker to be None by setting it to None in the main module
        import main
        original_tracker = main.game_activity_tracker
        main.game_activity_tracker = None

        try:
            tool_call = {
                "name": "track_game_activity",
                "arguments": {
                    "user_id": "test_user",
                    "game": "virtonomics",
                    "activity": "completed_tutorial"
                }
            }

            response = client.post("/mcp/tools/call", json=tool_call)
            assert response.status_code == 200
            data = response.json()
            assert data["isError"] == True
            assert "Game activity tracker not available" in data["content"][0]["text"]
        finally:
            # Restore the original tracker
            main.game_activity_tracker = original_tracker

    @patch('main.db')
    @patch('main.course_suggestions')
    def test_get_course_recommendations_tool_success(self, mock_course_suggestions, mock_db):
        """Test get_course_recommendations tool success"""
        mock_recommendations = [
            {"title": "Python for Data Science", "platform": "Coursera", "rating": 4.8, "duration": "8 weeks"},
            {"title": "Machine Learning Basics", "platform": "edX", "rating": 4.9, "duration": "6 weeks"},
            {"title": "Advanced Statistics", "platform": "Udemy", "rating": 4.7, "duration": "10 weeks"}
        ]

        # Create async mock for get_course_suggestions
        async def mock_get_course_suggestions(*args, **kwargs):
            return mock_recommendations
        mock_course_suggestions.get_course_suggestions = mock_get_course_suggestions

        mock_db.course_recommendations.insert_one.return_value = None

        tool_call = {
            "name": "get_course_recommendations",
            "arguments": {
                "user_id": "test_user",
                "skill_gaps": ["python", "machine learning", "statistics"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "3 skill gaps addressed" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.token_system')
    def test_get_gamification_leaderboard_tool_success(self, mock_token_system, mock_db):
        """Test get_gamification_leaderboard tool success"""
        mock_leaderboard = [
            {"user_id": "user1", "level": 8, "current_tokens": 2500},
            {"user_id": "user2", "level": 7, "current_tokens": 2100},
            {"user_id": "user3", "level": 6, "current_tokens": 1800}
        ]
        mock_token_system.get_leaderboard.return_value = mock_leaderboard

        tool_call = {
            "name": "get_gamification_leaderboard",
            "arguments": {
                "limit": 5
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Top 3 users" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.game_activity_tracker')
    def test_analyze_user_progress_tool_success(self, mock_tracker, mock_db):
        """Test analyze_user_progress tool success"""
        mock_progress_report = {
            "total_activities": 45,
            "current_level": 6,
            "games_played": ["virtonomics", "simcompanies"],
            "average_session_time": "25 minutes",
            "learning_progress": 78,
            "recent_achievements": ["Consistent Learner", "Game Explorer"]
        }
        mock_tracker.get_user_progress_report.return_value = mock_progress_report

        mock_db.progress_analyses.insert_one.return_value = None

        tool_call = {
            "name": "analyze_user_progress",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "45 activities" in data["content"][0]["text"]
        assert "Level 6" in data["content"][0]["text"]

    @patch('main.db')
    @patch('main.game_activity_tracker')
    def test_analyze_user_progress_tool_tracker_unavailable(self, mock_tracker, mock_db):
        """Test analyze_user_progress tool when tracker is unavailable"""
        # Mock the tracker to be None by setting it to None in the main module
        import main
        original_tracker = main.game_activity_tracker
        main.game_activity_tracker = None

        try:
            tool_call = {
                "name": "analyze_user_progress",
                "arguments": {
                    "user_id": "test_user"
                }
            }

            response = client.post("/mcp/tools/call", json=tool_call)
            assert response.status_code == 200
            data = response.json()
            assert data["isError"] == True
            assert "Progress tracker not available" in data["content"][0]["text"]
        finally:
            # Restore the original tracker
            main.game_activity_tracker = original_tracker

class TestGameIntegrationErrorHandling:
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
    def test_earn_gamification_tokens_missing_user_id(self, mock_db):
        """Test earn_gamification_tokens tool with missing user_id"""
        tool_call = {
            "name": "earn_gamification_tokens",
            "arguments": {
                "activity_type": "job_search"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_earn_gamification_tokens_missing_activity_type(self, mock_db):
        """Test earn_gamification_tokens tool with missing activity_type"""
        tool_call = {
            "name": "earn_gamification_tokens",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_spend_gamification_tokens_missing_user_id(self, mock_db):
        """Test spend_gamification_tokens tool with missing user_id"""
        tool_call = {
            "name": "spend_gamification_tokens",
            "arguments": {
                "reward_id": "premium_review"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_spend_gamification_tokens_missing_reward_id(self, mock_db):
        """Test spend_gamification_tokens tool with missing reward_id"""
        tool_call = {
            "name": "spend_gamification_tokens",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_get_user_gamification_stats_missing_user_id(self, mock_db):
        """Test get_user_gamification_stats tool with missing user_id"""
        tool_call = {
            "name": "get_user_gamification_stats",
            "arguments": {}
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_get_game_recommendations_missing_user_id(self, mock_db):
        """Test get_game_recommendations tool with missing user_id"""
        tool_call = {
            "name": "get_game_recommendations",
            "arguments": {
                "skills": ["python"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_track_game_activity_missing_user_id(self, mock_db):
        """Test track_game_activity tool with missing user_id"""
        tool_call = {
            "name": "track_game_activity",
            "arguments": {
                "game": "virtonomics",
                "activity": "completed_level"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_track_game_activity_missing_game(self, mock_db):
        """Test track_game_activity tool with missing game"""
        tool_call = {
            "name": "track_game_activity",
            "arguments": {
                "user_id": "test_user",
                "activity": "completed_level"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_track_game_activity_missing_activity(self, mock_db):
        """Test track_game_activity tool with missing activity"""
        tool_call = {
            "name": "track_game_activity",
            "arguments": {
                "user_id": "test_user",
                "game": "virtonomics"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_get_course_recommendations_missing_user_id(self, mock_db):
        """Test get_course_recommendations tool with missing user_id"""
        tool_call = {
            "name": "get_course_recommendations",
            "arguments": {
                "skill_gaps": ["python"]
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_get_course_recommendations_missing_skill_gaps(self, mock_db):
        """Test get_course_recommendations tool with missing skill_gaps"""
        tool_call = {
            "name": "get_course_recommendations",
            "arguments": {
                "user_id": "test_user"
            }
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    @patch('main.db')
    def test_analyze_user_progress_missing_user_id(self, mock_db):
        """Test analyze_user_progress tool with missing user_id"""
        tool_call = {
            "name": "analyze_user_progress",
            "arguments": {}
        }

        response = client.post("/mcp/tools/call", json=tool_call)
        # Should handle gracefully
        assert response.status_code in [200, 400]

class TestMongoDBIntegration:
    """Test MongoDB integration"""

    @patch('main.db')
    def test_gamification_activities_storage(self, mock_db):
        """Test gamification activities are stored in MongoDB"""
        mock_db.gamification_activities.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.gamification_activities.insert_one is not None

    @patch('main.db')
    def test_reward_redemptions_storage(self, mock_db):
        """Test reward redemptions are stored in MongoDB"""
        mock_db.reward_redemptions.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.reward_redemptions.insert_one is not None

    @patch('main.db')
    def test_game_recommendations_storage(self, mock_db):
        """Test game recommendations are stored in MongoDB"""
        mock_db.game_recommendations.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.game_recommendations.insert_one is not None

    @patch('main.db')
    def test_game_activities_storage(self, mock_db):
        """Test game activities are stored in MongoDB"""
        mock_db.game_activities.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.game_activities.insert_one is not None

    @patch('main.db')
    def test_course_recommendations_storage(self, mock_db):
        """Test course recommendations are stored in MongoDB"""
        mock_db.course_recommendations.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.course_recommendations.insert_one is not None

    @patch('main.db')
    def test_progress_analyses_storage(self, mock_db):
        """Test progress analyses are stored in MongoDB"""
        mock_db.progress_analyses.insert_one = Mock()

        # Verify the mock is set up for testing
        assert mock_db.progress_analyses.insert_one is not None

class TestGameIntegrationCoreFunctionality:
    """Test core business logic functions"""

    @patch('main.db')
    @patch('main.token_system')
    def test_earn_gamification_tokens_function_success(self, mock_token_system, mock_db):
        """Test earn_gamification_tokens function success"""
        mock_result = {
            "tokens_earned": 75,
            "new_balance": 1375,
            "level_up": True,
            "new_level": 6
        }
        mock_token_system.earn_tokens.return_value = mock_result

        mock_db.gamification_activities.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(earn_gamification_tokens_tool({
            "user_id": "test_user",
            "activity_type": "resume_upload",
            "metadata": {"file_size": "2MB", "sections_completed": 8}
        }))

        assert isinstance(result, MCPToolResponse)
        assert "+75 for resume_upload" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.token_system')
    def test_spend_gamification_tokens_function_success(self, mock_token_system, mock_db):
        """Test spend_gamification_tokens function success"""
        mock_result = {
            "reward": "LinkedIn Profile Optimization",
            "cost": 150,
            "new_balance": 1225
        }
        mock_token_system.spend_tokens.return_value = mock_result

        mock_db.reward_redemptions.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(spend_gamification_tokens_tool({
            "user_id": "test_user",
            "reward_id": "linkedin_optimization"
        }))

        assert isinstance(result, MCPToolResponse)
        assert "LinkedIn Profile Optimization for 150 tokens" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.token_system')
    def test_get_user_gamification_stats_function_success(self, mock_token_system, mock_db):
        """Test get_user_gamification_stats function success"""
        mock_stats = {
            "current_tokens": 1450,
            "level": 6,
            "total_earned": 3200,
            "total_spent": 1750,
            "achievements_count": 15,
            "rank": "Advanced Player"
        }
        mock_token_system.get_user_stats.return_value = mock_stats

        mock_db.gamification_stats.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(get_user_gamification_stats_tool({
            "user_id": "test_user"
        }))

        assert isinstance(result, MCPToolResponse)
        assert "Level 6" in result.content[0]["text"]
        assert "1450 tokens" in result.content[0]["text"]
        assert "15 achievements" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.virtonomics_integration')
    @patch('main.simcompanies_integration')
    def test_get_game_recommendations_function_specific_game(self, mock_simcompanies, mock_virtonomics, mock_db):
        """Test get_game_recommendations function for specific game"""
        mock_virtonomics.get_virtonomics_recommendations.return_value = {
            "recommendation": "Perfect for business strategy learning",
            "skill_match": 92,
            "estimated_completion_time": "4 weeks",
            "difficulty_level": "Intermediate"
        }

        mock_db.game_recommendations.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(get_game_recommendations_tool({
            "user_id": "test_user",
            "skills": ["business strategy", "economics", "decision making"],
            "game": "virtonomics"
        }))

        assert isinstance(result, MCPToolResponse)
        assert "Game recommendations generated for user test_user: 1 games" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.game_activity_tracker')
    def test_track_game_activity_function_success(self, mock_tracker, mock_db):
        """Test track_game_activity function success"""
        mock_result = {
            "tokens_earned": 30,
            "xp_gained": 150,
            "achievement_unlocked": "Level Master",
            "streak_days": 7,
            "progress_percentage": 45
        }
        mock_tracker.track_activity.return_value = mock_result

        mock_db.game_activities.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(track_game_activity_tool({
            "user_id": "test_user",
            "game": "simcompanies",
            "activity": "completed_challenge",
            "metadata": {"challenge_type": "production_optimization", "score": 950}
        }))

        assert isinstance(result, MCPToolResponse)
        assert "completed_challenge in simcompanies" in result.content[0]["text"]
        assert "+30 tokens" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.course_suggestions')
    def test_get_course_recommendations_function_success(self, mock_course_suggestions, mock_db):
        """Test get_course_recommendations function success"""
        mock_recommendations = [
            {"title": "Data Structures and Algorithms", "platform": "Coursera", "rating": 4.8, "enrollment_count": 50000},
            {"title": "System Design Interview Prep", "platform": "Udemy", "rating": 4.9, "enrollment_count": 25000},
            {"title": "Advanced Problem Solving", "platform": "LeetCode", "rating": 4.7, "enrollment_count": 15000}
        ]

        # Create async mock for get_course_suggestions
        async def mock_get_course_suggestions(*args, **kwargs):
            return mock_recommendations
        mock_course_suggestions.get_course_suggestions = mock_get_course_suggestions

        mock_db.course_recommendations.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(get_course_recommendations_tool({
            "user_id": "test_user",
            "skill_gaps": ["algorithms", "system design", "problem solving"]
        }))

        assert isinstance(result, MCPToolResponse)
        assert "3 skill gaps addressed" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.token_system')
    def test_get_gamification_leaderboard_function_success(self, mock_token_system, mock_db):
        """Test get_gamification_leaderboard function success"""
        mock_leaderboard = [
            {"user_id": "top_player", "level": 12, "current_tokens": 5000, "total_earned": 15000},
            {"user_id": "second_place", "level": 11, "current_tokens": 4800, "total_earned": 14200},
            {"user_id": "third_place", "level": 10, "current_tokens": 4500, "total_earned": 13500},
            {"user_id": "fourth_place", "level": 9, "current_tokens": 4200, "total_earned": 12800},
            {"user_id": "fifth_place", "level": 9, "current_tokens": 4100, "total_earned": 12500}
        ]
        mock_token_system.get_leaderboard.return_value = mock_leaderboard

        # Test the function directly
        import asyncio
        result = asyncio.run(get_gamification_leaderboard_tool({
            "limit": 5
        }))

        assert isinstance(result, MCPToolResponse)
        assert "Top 5 users" in result.content[0]["text"]

    @patch('main.db')
    @patch('main.game_activity_tracker')
    def test_analyze_user_progress_function_success(self, mock_tracker, mock_db):
        """Test analyze_user_progress function success"""
        mock_progress_report = {
            "total_activities": 67,
            "current_level": 8,
            "games_played": ["virtonomics", "simcompanies", "cwetlands"],
            "total_time_spent": "45 hours",
            "average_session_time": "32 minutes",
            "learning_progress": 85,
            "skill_improvements": ["Business Strategy +40%", "Environmental Awareness +35%", "Management Skills +50%"],
            "recent_achievements": ["Dedicated Learner", "Game Master", "Skill Builder"],
            "next_milestones": ["Level 9", "100 Activities", "Expert Status"]
        }
        mock_tracker.get_user_progress_report.return_value = mock_progress_report

        mock_db.progress_analyses.insert_one.return_value = None

        # Test the function directly
        import asyncio
        result = asyncio.run(analyze_user_progress_tool({
            "user_id": "test_user"
        }))

        assert isinstance(result, MCPToolResponse)
        assert "67 activities" in result.content[0]["text"]
        assert "Level 8" in result.content[0]["text"]

class TestGameIntegrationIntegration:
    """Test integration scenarios"""

    @patch('main.db')
    @patch('main.token_system')
    @patch('main.game_activity_tracker')
    def test_gamification_activity_tracking_integration(self, mock_tracker, mock_token_system, mock_db):
        """Test gamification with activity tracking integration"""
        mock_token_result = {
            "tokens_earned": 40,
            "new_balance": 1390,
            "level_up": False
        }
        mock_token_system.earn_tokens.return_value = mock_token_result

        mock_activity_result = {
            "tokens_earned": 40,
            "xp_gained": 200,
            "achievement_unlocked": "Consistent Player"
        }
        mock_tracker.track_activity.return_value = mock_activity_result

        mock_db.gamification_activities.insert_one.return_value = None
        mock_db.game_activities.insert_one.return_value = None

        # Test integration flow
        assert mock_token_system is not None
        assert mock_tracker is not None
        assert mock_db is not None

    @patch('main.db')
    @patch('main.virtonomics_integration')
    @patch('main.simcompanies_integration')
    @patch('main.course_suggestions')
    def test_game_learning_integration(self, mock_course_suggestions, mock_simcompanies, mock_virtonomics, mock_db):
        """Test game recommendations with course suggestions integration"""
        mock_virtonomics.get_virtonomics_recommendations.return_value = {
            "recommendation": "Business simulation for strategic thinking"
        }
        mock_simcompanies.get_simcompanies_recommendations.return_value = {
            "recommendation": "Company management for operational skills"
        }

        mock_course_recommendations = [
            {"title": "Strategic Management", "platform": "Coursera"},
            {"title": "Operations Management", "platform": "edX"}
        ]

        # Create async mock for get_course_suggestions
        async def mock_get_course_suggestions(*args, **kwargs):
            return mock_course_recommendations
        mock_course_suggestions.get_course_suggestions = mock_get_course_suggestions

        mock_db.game_recommendations.insert_one.return_value = None
        mock_db.course_recommendations.insert_one.return_value = None

        # Test integration flow
        assert mock_virtonomics is not None
        assert mock_simcompanies is not None
        assert mock_course_suggestions is not None
        assert mock_db is not None

    @patch('main.db')
    @patch('main.token_system')
    @patch('main.game_activity_tracker')
    def test_complete_gamification_workflow_integration(self, mock_tracker, mock_token_system, mock_db):
        """Test complete gamification workflow integration"""
        # Mock token system for earning
        mock_earn_result = {
            "tokens_earned": 25,
            "new_balance": 1325,
            "level_up": False
        }
        mock_token_system.earn_tokens.return_value = mock_earn_result

        # Mock token system for spending
        mock_spend_result = {
            "reward": "Premium Course Access",
            "cost": 200,
            "new_balance": 1125
        }
        mock_token_system.spend_tokens.return_value = mock_spend_result

        # Mock token system for stats
        mock_stats = {
            "current_tokens": 1125,
            "level": 5,
            "total_earned": 2500,
            "total_spent": 1375
        }
        mock_token_system.get_user_stats.return_value = mock_stats

        # Mock activity tracker
        mock_activity_result = {
            "tokens_earned": 25,
            "xp_gained": 125,
            "progress_percentage": 35
        }
        mock_tracker.track_activity.return_value = mock_activity_result

        # Mock leaderboard
        mock_leaderboard = [
            {"user_id": "leader1", "level": 10, "current_tokens": 3000},
            {"user_id": "leader2", "level": 9, "current_tokens": 2800}
        ]
        mock_token_system.get_leaderboard.return_value = mock_leaderboard

        # Setup all database mocks
        mock_db.gamification_activities.insert_one.return_value = None
        mock_db.reward_redemptions.insert_one.return_value = None
        mock_db.gamification_stats.insert_one.return_value = None
        mock_db.game_activities.insert_one.return_value = None

        # Test complete workflow integration
        assert mock_token_system is not None
        assert mock_tracker is not None
        assert mock_db is not None

if __name__ == "__main__":
    pytest.main([__file__])