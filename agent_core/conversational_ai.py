"""
Conversational AI Module for Job Application Agent Discord Bot

This module provides natural language conversational capabilities using Llama 3.1 8B
to make interactions with the Discord bot more human-like and helpful for job seekers.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
if not HUGGINGFACE_API_KEY:
    logger.warning("HUGGINGFACE_API_KEY not found in environment variables - conversational AI will use fallback responses")
    HUGGINGFACE_API_KEY = None

class JobSeekerAssistant:
    """Conversational AI assistant for job seekers."""

    def __init__(self):
        self.conversation_history = {}
        self.system_prompt = """
        You are a friendly, knowledgeable job search assistant named "CareerGuide" working with unemployed people in Cape Town, South Africa. Your goal is to help job seekers navigate their career journey through natural, supportive conversations.

        KEY PRINCIPLES:
        1. Be empathetic and encouraging - many users are facing unemployment challenges
        2. Be practical and action-oriented - focus on concrete next steps
        3. Be culturally sensitive - understand South African context (Cape Town, economic challenges, etc.)
        4. Be knowledgeable about local job market and available resources
        5. Guide users toward using the bot's features without being pushy

        AVAILABLE BOT FEATURES:
        - /search_jobs - Find jobs with keywords, location, salary filters
        - /game_recommend - Get game recommendations based on skills
        - /my_progress - View achievements and progress
        - /check_tokens - See token balance and rewards
        - /run_simulation - Explore policy scenarios (advanced)

        CONVERSATION STYLE:
        - Use friendly, conversational language like "Hey there!" or "Great question!"
        - Ask follow-up questions to understand their situation better
        - Share relevant tips about job searching in South Africa
        - Celebrate small wins and progress
        - If they're stuck, gently suggest specific bot commands
        - Keep responses concise but helpful (under 300 words)

        CAPE TOWN CONTEXT:
        - High unemployment rate (around 25%)
        - Key industries: Tourism, Finance, Technology, Logistics
        - Skills in demand: Digital skills, customer service, technical trades
        - Available support: Government programs, NGO assistance, online learning
        - Challenges: Economic inequality, skills gaps, transportation issues

        RESPONSE FORMAT:
        Always respond naturally. If suggesting a command, explain why it would help first.
        Example: "That sounds like a great goal! Have you tried using /search_jobs to find opportunities in your field?"

        Remember: Your role is to guide, support, and empower job seekers to take action using the tools available.
        """

    def generate_response(self, user_id: str, user_message: str, user_context: Dict = None) -> str:
        """Generate a conversational response to user input."""
        # If no API key, use fallback responses
        if not HUGGINGFACE_API_KEY:
            logger.info(f"Using fallback response for user {user_id} (no API key)")
            return self._get_fallback_response(user_message)

        try:
            # Get conversation history
            history = self.conversation_history.get(user_id, [])

            # Build context
            context_info = ""
            if user_context:
                context_info = f"""
                USER CONTEXT:
                - Location: {user_context.get('location', 'Cape Town')}
                - Skills: {', '.join(user_context.get('skills', ['Not specified']))}
                - Current situation: {user_context.get('situation', 'Job seeking')}
                - Recent activity: {user_context.get('recent_activity', 'None')}
                """

            # Build conversation history (last 3 exchanges)
            history_text = ""
            if history:
                recent_history = history[-3:]
                history_text = "\nRECENT CONVERSATION:\n"
                for i, (msg, resp) in enumerate(recent_history):
                    history_text += f"User: {msg}\nAssistant: {resp}\n"

            prompt = f"""
            {self.system_prompt}

            {context_info}
            {history_text}

            CURRENT USER MESSAGE: "{user_message}"

            Respond naturally and helpfully. Focus on being supportive and guiding them toward using bot features when appropriate.
            """

            # Call Hugging Face API
            response = requests.post(
                'https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct',
                headers={
                    'Authorization': f'Bearer {HUGGINGFACE_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'inputs': prompt,
                    'parameters': {
                        'max_new_tokens': 300,
                        'temperature': 0.7,
                        'do_sample': True,
                        'top_p': 0.9
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and result:
                    ai_response = result[0].get('generated_text', '').strip()

                    # Clean up response (remove any prompt leakage)
                    if 'CURRENT USER MESSAGE:' in ai_response:
                        ai_response = ai_response.split('CURRENT USER MESSAGE:')[0].strip()

                    # Update conversation history
                    history.append((user_message, ai_response))
                    self.conversation_history[user_id] = history[-10:]  # Keep last 10 exchanges

                    logger.info(f"Generated conversational response for user {user_id}")
                    return ai_response

                else:
                    logger.error("Unexpected API response format")
                    return self._get_fallback_response(user_message)

            else:
                logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
                return self._get_fallback_response(user_message)

        except Exception as e:
            logger.error(f"Error generating conversational response: {e}")
            return self._get_fallback_response(user_message)

    def _get_fallback_response(self, user_message: str) -> str:
        """Provide a fallback response when AI generation fails."""
        fallbacks = [
            "I'm here to help you with your job search! What specific questions do you have about finding work in Cape Town?",
            "I'd love to assist you with your career goals. Have you tried using /search_jobs to find opportunities?",
            "Job hunting can be challenging, but there are great resources available. What skills or experience do you have?",
            "I'm your job search companion! Let me know what you're looking for and I'll guide you to the right tools.",
            "Welcome! I'm here to support your job search journey. What would you like to focus on today?"
        ]

        # Simple keyword matching for better fallbacks
        message_lower = user_message.lower()

        if any(word in message_lower for word in ['job', 'work', 'employment', 'career']):
            return "Finding work in Cape Town can be competitive, but there are many opportunities! Have you tried /search_jobs with your preferred keywords?"
        elif any(word in message_lower for word in ['skill', 'learn', 'course', 'training']):
            return "Building new skills is a great way to improve your job prospects! Check out /game_recommend for skill-building games."
        elif any(word in message_lower for word in ['help', 'confused', 'lost', 'stuck']):
            return "I understand job searching can feel overwhelming. Let me help! What specific area are you struggling with?"
        elif any(word in message_lower for word in ['game', 'sim', 'simulation']):
            return "The serious games are excellent for skill development! Use /game_recommend to find games that match your interests."
        else:
            import random
            return random.choice(fallbacks)

    def get_user_context(self, user_id: str) -> Dict:
        """Get context information about the user for better responses."""
        # This would integrate with user data storage in a real implementation
        # For now, return basic context
        return {
            'location': 'Cape Town',
            'skills': [],  # Would be populated from user profile
            'situation': 'Active job seeker',
            'recent_activity': 'Engaging with bot'
        }

    def suggest_next_action(self, user_id: str, current_context: str) -> str:
        """Suggest the next helpful action based on user's current context."""
        suggestions = {
            'new_user': "Welcome! Let's start by exploring your skills. Try /game_recommend to see what games match your background.",
            'job_search': "Ready to find jobs? Use /search_jobs with keywords like 'customer service' or 'administration'.",
            'skill_building': "Great focus on skills! The serious games are perfect for this. Check /my_progress to track your development.",
            'discouraged': "Job hunting can be tough, but you're taking positive steps! Remember to check /check_tokens for rewards that keep you motivated.",
            'experienced': "With your experience, you have great potential! Try /search_jobs with specific keywords from your background."
        }

        return suggestions.get(current_context, "What would you like to work on next? I can help with job searching, skill development, or exploring opportunities!")

# Global instance
conversational_assistant = JobSeekerAssistant()

def chat_with_user(user_id: str, message: str, context: Dict = None) -> str:
    """Main function to handle conversational chat with users."""
    return conversational_assistant.generate_response(user_id, message, context)

def get_conversational_suggestion(user_id: str, context: str) -> str:
    """Get a contextual suggestion for next actions."""
    return conversational_assistant.suggest_next_action(user_id, context)

if __name__ == "__main__":
    # Test the conversational AI
    test_responses = [
        "Hi, I'm looking for a job but don't know where to start",
        "What skills are in demand in Cape Town?",
        "I'm feeling discouraged about my job search",
        "Can you help me find customer service jobs?",
        "What games can help me learn new skills?"
    ]

    print("Testing Conversational AI Assistant:")
    print("=" * 50)

    for i, test_msg in enumerate(test_responses, 1):
        print(f"\nTest {i}: User says: '{test_msg}'")
        try:
            response = chat_with_user("test_user", test_msg)
            print(f"Assistant: {response[:200]}...")
        except Exception as e:
            print(f"Error: {e}")
            print(f"Fallback: {conversational_assistant._get_fallback_response(test_msg)}")