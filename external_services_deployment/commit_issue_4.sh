#!/bin/bash

# Commit script for Issue #4: Generate ATS-optimized resume with python-docx
# This script commits all changes related to resume generation and auditing

echo "Committing changes for Issue #4: Generate ATS-optimized resume with python-docx"

# Add all new and modified files
git add master_resume.json
git add resume_tool.py
git add audit_tool.py
git add resume_parser.py
git add documents.py
git add ayoba_bot.py
git add tests/test_resume.py
git add tests/test_resume_parser.py
git add requirements.txt
git add main.py
git add README.md
git add .github/workflows/test.yml

# Commit with issue reference
git commit -m "feat: Implement ATS-optimized resume generation, parsing, auditing, and document selection

- Add resume_parser.py for parsing uploaded PDF/DOCX resumes to JSON using pdfplumber/python-docx
- Update resume_tool.py to use Hugging Face Llama 3.1 8B-Instruct for ATS-optimized resume generation
- Update audit_tool.py to use Hugging Face API for hallucination detection against master_resume.json
- Create documents.py for handling certificate/degree/diploma/ID uploads and job-relevant selection
- Update ayoba_bot.py with /upload_doc endpoint and !upload_doc command support
- Update main.py to add LangGraph nodes for resume parsing, generation, auditing, and document selection
- Add comprehensive tests in tests/test_resume.py and tests/test_resume_parser.py
- Update requirements.txt with langchain_huggingface and pdfplumber dependencies
- Update README.md with detailed debugging steps for resume parsing, generation, auditing, and uploads
- Update CI/CD pipeline to include new tests with HUGGINGFACE_API_KEY secret
- Ensure ATS-friendly format: Arial 11pt, plain text header, bulleted skills, reverse chronological experience

Closes #4"

echo "Changes committed successfully for Issue #4"
echo "Ready to push to GitHub"