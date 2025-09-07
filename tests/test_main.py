import unittest
from unittest.mock import patch
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, AgentState

class TestMain(unittest.TestCase):

    @patch.dict(os.environ, {
        'GOOGLE_CLIENT_ID': 'test_id',
        'GOOGLE_CLIENT_SECRET': 'test_secret',
        'AYOBA_API_TOKEN': 'test_token',
        'SMTP_USER': 'test_user',
        'SMTP_PASS': 'test_pass'
    })
    def test_workflow_initialization(self):
        """Test that the LangGraph workflow initializes and runs without errors."""
        initial_state = AgentState(
            messages=[],
            user_id="test_user",
            job_emails=[],
            parsed_jobs=[],
            generated_resumes=[],
            sent_emails=[],
            ayoba_responses=[]
        )
        # This should not raise an exception
        result = app.invoke(initial_state)
        self.assertIsInstance(result, dict)
        self.assertIn('user_id', result)
        self.assertEqual(result['user_id'], "test_user")

if __name__ == '__main__':
    unittest.main()