import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import tempfile
import shutil

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from email_comm_hub import gmail_tool

class TestGmailTool(unittest.TestCase):

    def setUp(self):
        # Use a temporary DB for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, 'test_users.db')
        gmail_tool.DB_PATH = self.temp_db
        gmail_tool.init_db()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('gmail_tool.sqlite3.connect')
    def test_init_db(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        gmail_tool.init_db()
        mock_conn.cursor().execute.assert_called()
        mock_conn.commit.assert_called()
        mock_conn.close.assert_called()

    def test_store_and_get_token(self):
        user_id = 'test_user'
        refresh_token = 'test_refresh_token'
        gmail_tool.store_token(user_id, refresh_token)
        retrieved = gmail_tool.get_token(user_id)
        self.assertEqual(retrieved, refresh_token)

    def test_get_token_nonexistent(self):
        retrieved = gmail_tool.get_token('nonexistent')
        self.assertIsNone(retrieved)

    @patch('gmail_tool.InstalledAppFlow.from_client_secrets_file')
    def test_get_oauth_url(self, mock_flow_class):
        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = ('https://auth.url', None)
        mock_flow_class.return_value = mock_flow

        url = gmail_tool.get_oauth_url('test_user')
        self.assertEqual(url, 'https://auth.url')
        mock_flow.authorization_url.assert_called_with(state='test_user', prompt='consent')

    @patch('gmail_tool.InstalledAppFlow.from_client_secrets_file')
    def test_exchange_code_for_token(self, mock_flow_class):
        mock_flow = MagicMock()
        mock_creds = MagicMock()
        mock_creds.refresh_token = 'new_refresh_token'
        mock_flow.credentials = mock_creds
        mock_flow_class.return_value = mock_flow

        creds = gmail_tool.exchange_code_for_token('test_code', 'test_user')
        self.assertEqual(creds, mock_creds)
        mock_flow.fetch_token.assert_called_with(code='test_code')

    @patch('gmail_tool.Credentials.from_authorized_user_info')
    @patch('gmail_tool.os.getenv')
    def test_get_credentials(self, mock_getenv, mock_creds_class):
        mock_getenv.side_effect = lambda key: {'GOOGLE_CLIENT_ID': 'client_id', 'GOOGLE_CLIENT_SECRET': 'client_secret'}.get(key)
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_creds_class.return_value = mock_creds

        # First, store a token
        gmail_tool.store_token('test_user', 'refresh_token')

        creds = gmail_tool.get_credentials('test_user')
        self.assertEqual(creds, mock_creds)

    def test_get_credentials_no_token(self):
        with self.assertRaises(ValueError):
            gmail_tool.get_credentials('no_token_user')

    @patch('gmail_tool.build')
    def test_scan_emails(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_creds = MagicMock()
        result = gmail_tool.scan_emails(mock_creds)
        self.assertEqual(result, [])
        mock_build.assert_called_with('gmail', 'v1', credentials=mock_creds)

if __name__ == '__main__':
    unittest.main()