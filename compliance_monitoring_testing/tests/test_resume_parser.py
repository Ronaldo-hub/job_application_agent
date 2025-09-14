import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from resume_doc_processing import resume_parser
from agent_core import documents

class TestResumeParser(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.sample_resume_text = """
        Ronald Williams
        ronald.williams@example.com
        (555) 123-4567
        New York, NY

        Summary
        Motivated chemical engineering graduate with experience in process optimization and data analysis.

        Skills
        - Python
        - Communication
        - Data Analysis
        - Chemical Engineering

        Experience
        Chemical Engineering Intern
        ABC Manufacturing, New York, NY
        June 2023 - August 2023
        Assisted in process optimization projects.

        Education
        Bachelor of Science in Chemical Engineering
        State University, New York, NY
        May 2023

        Certifications
        - Python Programming Certificate
        """

        self.sample_parsed_resume = {
            "personal_info": {
                "name": "Ronald Williams",
                "email": "ronald.williams@example.com",
                "phone": "(555) 123-4567",
                "location": "New York, NY"
            },
            "summary": "Motivated chemical engineering graduate with experience in process optimization and data analysis.",
            "skills": ["Python", "Communication", "Data Analysis", "Chemical Engineering"],
            "experience": [{
                "title": "Chemical Engineering Intern",
                "company": "ABC Manufacturing",
                "location": "New York, NY",
                "start_date": "June 2023",
                "end_date": "August 2023",
                "description": "Assisted in process optimization projects."
            }],
            "education": [{
                "degree": "Bachelor of Science in Chemical Engineering",
                "institution": "State University",
                "location": "New York, NY",
                "graduation_date": "May 2023",
                "gpa": ""
            }],
            "certifications": ["Python Programming Certificate"]
        }

    def test_extract_header(self):
        """Test header extraction from resume text."""
        header = resume_parser.extract_header(self.sample_resume_text)

        self.assertEqual(header["name"], "Ronald Williams")
        self.assertEqual(header["email"], "ronald.williams@example.com")
        self.assertEqual(header["phone"], "(555) 123-4567")
        self.assertEqual(header["location"], "New York, NY")

    def test_extract_summary(self):
        """Test summary extraction."""
        summary = resume_parser.extract_summary(self.sample_resume_text)
        self.assertIn("chemical engineering graduate", summary.lower())

    def test_extract_skills(self):
        """Test skills extraction."""
        skills = resume_parser.extract_skills(self.sample_resume_text)
        self.assertIn("Python", skills)
        self.assertIn("Chemical Engineering", skills)

    def test_extract_experience(self):
        """Test experience extraction."""
        experience = resume_parser.extract_experience(self.sample_resume_text)
        self.assertTrue(len(experience) > 0)
        self.assertEqual(experience[0]["title"], "Chemical Engineering Intern")

    def test_extract_education(self):
        """Test education extraction."""
        education = resume_parser.extract_education(self.sample_resume_text)
        self.assertTrue(len(education) > 0)
        self.assertIn("Chemical Engineering", education[0]["degree"])

    def test_extract_certifications(self):
        """Test certifications extraction."""
        certifications = resume_parser.extract_certifications(self.sample_resume_text)
        self.assertIn("Python Programming Certificate", certifications)

    def test_parse_resume_text(self):
        """Test full resume text parsing."""
        parsed = resume_parser.parse_resume_text(self.sample_resume_text)

        self.assertEqual(parsed["personal_info"]["name"], "Ronald Williams")
        self.assertIn("Python", parsed["skills"])
        self.assertTrue(len(parsed["experience"]) > 0)

    @patch('resume_parser.extract_pdf_text')
    def test_parse_pdf_resume(self, mock_extract):
        """Test PDF resume parsing."""
        mock_extract.return_value = self.sample_resume_text

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"dummy pdf content")
            temp_file_path = temp_file.name

        try:
            result = resume_parser.parse_pdf_resume(temp_file_path)
            self.assertEqual(result["personal_info"]["name"], "Ronald Williams")
        finally:
            os.unlink(temp_file_path)

    @patch('resume_parser.Document')
    def test_parse_docx_resume(self, mock_document):
        """Test DOCX resume parsing."""
        mock_doc = MagicMock()
        mock_doc.paragraphs = [MagicMock(text=line) for line in self.sample_resume_text.split('\n')]
        mock_document.return_value = mock_doc

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_file.write(b"dummy docx content")
            temp_file_path = temp_file.name

        try:
            result = resume_parser.parse_docx_resume(temp_file_path)
            self.assertEqual(result["personal_info"]["name"], "Ronald Williams")
        finally:
            os.unlink(temp_file_path)

    def test_merge_resume_data(self):
        """Test merging parsed resume data with master resume."""
        master_resume = {
            "personal_info": {"name": "", "email": "", "phone": "", "location": ""},
            "summary": "",
            "skills": ["Existing Skill"],
            "experience": [],
            "education": [],
            "certifications": ["Existing Cert"]
        }

        new_resume = {
            "personal_info": {"name": "John Doe", "email": "john@example.com"},
            "skills": ["New Skill"],
            "certifications": ["New Cert"]
        }

        merged = resume_parser.merge_resume_data(master_resume, new_resume)

        self.assertEqual(merged["personal_info"]["name"], "John Doe")
        self.assertIn("Existing Skill", merged["skills"])
        self.assertIn("New Skill", merged["skills"])
        self.assertIn("Existing Cert", merged["certifications"])
        self.assertIn("New Cert", merged["certifications"])

class TestDocumentSelection(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures for document selection."""
        self.sample_job_details = {
            "job_title": "Python Developer",
            "skills": ["Python", "Django", "SQL"],
            "description": "Looking for a Python developer with web development experience."
        }

        self.sample_documents = {
            "cert1": {
                "id": "cert1",
                "type": "certificate",
                "content_preview": "Python Programming Certificate from Coursera",
                "filename": "python_cert.pdf"
            },
            "cert2": {
                "id": "cert2",
                "type": "certificate",
                "content_preview": "Java Certificate from Oracle",
                "filename": "java_cert.pdf"
            }
        }

    @patch('documents.load_documents_metadata')
    @patch('documents.requests.post')
    def test_select_relevant_documents(self, mock_post, mock_load):
        """Test document selection for job relevance."""
        mock_load.return_value = self.sample_documents

        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'generated_text': '{"selected_documents": [{"doc_id": "cert1", "relevance_score": 9, "reason": "Python certificate matches job requirements"}]}'
        }]
        mock_post.return_value = mock_response

        result = documents.select_relevant_documents(self.sample_job_details)

        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0]["doc_id"], "cert1")

    @patch('documents.load_documents_metadata')
    def test_list_documents(self, mock_load):
        """Test listing documents."""
        mock_load.return_value = self.sample_documents

        docs = documents.list_documents()

        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0]["type"], "certificate")

    def test_allowed_file(self):
        """Test file extension validation."""
        self.assertTrue(documents.allowed_file("test.pdf"))
        self.assertTrue(documents.allowed_file("test.docx"))
        self.assertFalse(documents.allowed_file("test.txt"))
        self.assertFalse(documents.allowed_file("test.jpg"))

if __name__ == '__main__':
    unittest.main()