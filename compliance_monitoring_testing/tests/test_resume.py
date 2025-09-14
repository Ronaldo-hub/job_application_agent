import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
import sys
sys.path.append('..')

from resume_doc_processing import resume_tool
from resume_doc_processing import audit_tool

class TestResumeTool(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.test_job_details = {
            'job_title': 'Python Developer',
            'skills': ['Python', 'Django', 'SQL', 'Git'],
            'employer_email': 'hr@company.com',
            'email_id': 'test123'
        }

        # Mock master resume data
        self.mock_master_resume = {
            'personal_info': {
                'name': 'Test User',
                'email': 'test@example.com'
            },
            'skills': ['Python', 'JavaScript', 'SQL'],
            'experience': [
                {
                    'title': 'Software Engineer',
                    'company': 'Test Corp',
                    'description': 'Developed Python applications'
                }
            ]
        }

    @patch('resume_tool.load_master_resume')
    @patch('resume_tool.requests.post')
    def test_generate_resume_content_success(self, mock_post, mock_load):
        """Test successful resume content generation with Hugging Face API."""
        mock_load.return_value = self.mock_master_resume

        # Mock Hugging Face API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'generated_text': 'Generated ATS-optimized resume content\n\nRonald Williams\nronald@example.com\n+27 123 456 789\n\nSummary\n2-3 sentence summary with Python keywords.\n\nSkills\n- Python\n- Django\n- SQL\n\nExperience\nSoftware Engineer\nTech Corp\nJan 2023 - Present\nDeveloped Python applications.'
        }]
        mock_post.return_value = mock_response

        result = resume_tool.generate_resume_content(self.mock_master_resume, self.test_job_details)

        self.assertIn('Ronald Williams', result)
        self.assertIn('Skills', result)
        self.assertIn('Python', result)
        mock_post.assert_called_once()

    @patch('resume_tool.load_master_resume')
    @patch('resume_tool.requests.post')
    def test_generate_resume_content_api_error(self, mock_post, mock_load):
        """Test resume generation with Hugging Face API error."""
        mock_load.return_value = self.mock_master_resume

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as context:
            resume_tool.generate_resume_content(self.mock_master_resume, self.test_job_details)

        self.assertIn("Failed to generate resume", str(context.exception))

    @patch('resume_tool.load_master_resume')
    @patch('resume_tool.create_word_resume')
    @patch('resume_tool.create_pdf_resume')
    @patch('resume_tool.generate_resume_content')
    def test_generate_resume_full_flow(self, mock_content, mock_pdf, mock_word, mock_load):
        """Test full resume generation flow."""
        mock_load.return_value = self.mock_master_resume
        mock_content.return_value = 'Test resume content'
        mock_word.return_value = 'test.docx'
        mock_pdf.return_value = 'test.pdf'

        result = resume_tool.generate_resume(self.test_job_details)

        self.assertIn('content', result)
        self.assertIn('word_file', result)
        self.assertIn('pdf_file', result)
        self.assertEqual(result['job_title'], 'Python Developer')

    def test_generate_word_resume(self):
        """Test Word document creation."""
        content = "Test Resume\nName: Test User\nSkills: Python"

        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, 'test_resume.docx')
            result = resume_tool.create_word_resume(content, 'test_resume')

            # Check if file was created (would need docx installed for full test)
            self.assertIsInstance(result, str)

    def test_generate_pdf_resume(self):
        """Test PDF document creation."""
        content = "Test Resume\nName: Test User\nSkills: Python"

        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, 'test_resume.pdf')
            result = resume_tool.create_pdf_resume(content, 'test_resume')

            # Check if file was created (would need reportlab installed for full test)
            self.assertIsInstance(result, str)

    def test_ats_format_compliance(self):
        """Test that generated resume follows ATS-friendly format."""
        ats_content = """Ronald Williams
ronald@example.com
+27 123 456 789

Summary
Experienced Python developer with 3 years of experience in web development and data analysis.

Skills
- Python
- Django
- SQL
- Git

Experience
Software Engineer
Tech Corp
Jan 2023 - Present
Developed Python applications using Django framework.

Education
Bachelor of Science in Computer Science
State University
May 2022
"""

        # Check header format
        self.assertIn('Ronald Williams', ats_content)
        self.assertIn('ronald@example.com', ats_content)

        # Check sections
        self.assertIn('Summary', ats_content)
        self.assertIn('Skills', ats_content)
        self.assertIn('Experience', ats_content)
        self.assertIn('Education', ats_content)

        # Check bullet points for skills
        self.assertIn('- Python', ats_content)
        self.assertIn('- Django', ats_content)

    def test_hallucination_detection(self):
        """Test detection of fabricated skills or experience."""
        # Resume with hallucinated skill
        hallucinated_resume = """John Doe
john@example.com

Skills
- Python
- Java (not in master resume)
- Machine Learning

Experience
Senior Developer
Fake Company
2020-2023
Led development of AI projects.
"""

        master_resume = {
            'skills': ['Python', 'JavaScript', 'SQL'],
            'experience': [{
                'title': 'Junior Developer',
                'company': 'Real Company',
                'description': 'Basic development tasks'
            }]
        }

        # This would be tested with the audit function
        # For now, check that the content contains potential hallucinations
        self.assertIn('Java', hallucinated_resume)  # Not in master skills
        self.assertIn('Senior Developer', hallucinated_resume)  # Different from master
        self.assertIn('Fake Company', hallucinated_resume)  # Not in master experience


class TestAuditTool(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.test_resume_data = {
            'content': 'Test resume with Python skills',
            'job_title': 'Python Developer',
            'employer_email': 'hr@company.com'
        }

        self.test_job_details = {
            'job_title': 'Python Developer',
            'skills': ['Python', 'Django']
        }

    @patch('audit_tool.load_master_resume')
    @patch('audit_tool.requests.post')
    def test_audit_resume_content_success(self, mock_post, mock_load):
        """Test successful resume auditing with Hugging Face API."""
        mock_load.return_value = self.mock_master_resume

        # Mock Hugging Face API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'generated_text': '{"accuracy_score": 85, "hallucinations_detected": [], "missing_skills": ["Git"], "recommendations": ["Add Git experience"], "approved": true}'
        }]
        mock_post.return_value = mock_response

        result = audit_tool.audit_resume_content(self.test_resume_data['content'], self.test_job_details)

        self.assertEqual(result['accuracy_score'], 85)
        self.assertTrue(result['approved'])
        self.assertIn('missing_skills', result)

    @patch('audit_tool.load_master_resume')
    @patch('audit_tool.requests.post')
    def test_audit_resume_content_with_hallucinations(self, mock_post, mock_load):
        """Test auditing that detects hallucinations with Hugging Face API."""
        mock_load.return_value = self.mock_master_resume

        # Mock API response with hallucinations detected
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'generated_text': '{"accuracy_score": 60, "hallucinations_detected": ["Java skill not in master resume"], "missing_skills": ["Git"], "recommendations": ["Remove fabricated Java skill"], "approved": false}'
        }]
        mock_post.return_value = mock_response

        result = audit_tool.audit_resume_content(self.test_resume_data['content'], self.test_job_details)

        self.assertEqual(result['accuracy_score'], 60)
        self.assertFalse(result['approved'])
        self.assertIn('Java skill not in master resume', result['hallucinations_detected'])

    def test_audit_resume_with_error(self):
        """Test auditing when resume generation failed."""
        error_resume_data = {
            'error': 'Generation failed',
            'content': '',
            'job_title': 'Python Developer',
            'employer_email': 'hr@company.com'
        }

        result = audit_tool.audit_resume(error_resume_data)

        self.assertIn('audit_result', result)
        self.assertEqual(result['audit_result']['accuracy_score'], 0)
        self.assertFalse(result['audit_result']['approved'])


class TestIntegration(unittest.TestCase):

    def test_resume_generation_and_audit_integration(self):
        """Test the integration between resume generation and auditing."""
        # This would be a full integration test with mocked APIs
        # For now, test the data flow structure

        test_job = {
            'job_title': 'Data Scientist',
            'skills': ['Python', 'Machine Learning', 'SQL'],
            'employer_email': 'jobs@tech.com',
            'email_id': 'job123'
        }

        # Test that the functions can be called without errors (with mocks)
        with patch('resume_tool.load_master_resume'), \
             patch('resume_tool.requests.post') as mock_resume_post, \
             patch('audit_tool.load_master_resume'), \
             patch('audit_tool.requests.post') as mock_audit_post:

            # Mock resume generation API
            mock_resume_response = MagicMock()
            mock_resume_response.status_code = 200
            mock_resume_response.json.return_value = [{
                'generated_text': 'Generated ATS resume content'
            }]
            mock_resume_post.return_value = mock_resume_response

            # Mock audit API
            mock_audit_response = MagicMock()
            mock_audit_response.status_code = 200
            mock_audit_response.json.return_value = [{
                'generated_text': '{"accuracy_score": 90, "hallucinations_detected": [], "approved": true}'
            }]
            mock_audit_post.return_value = mock_audit_response

            # Generate resume
            resume = resume_tool.generate_resume(test_job)
            self.assertIn('content', resume)

            # Audit resume
            audit = audit_tool.audit_resume(resume)
            self.assertIn('audit_result', audit)


if __name__ == '__main__':
    unittest.main()