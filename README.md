# Job Application Agent

A Python-based agent that assists unemployed users on Ayoba (MTN's free chat platform) by automating job applications. It scans Gmail for job emails, parses details with spaCy, generates ATS-optimized resumes with python-docx, sends them via smtplib, and responds via Ayoba's chatbot API. Orchestrated using LangChain/LangGraph.

## Features

- Gmail API integration for scanning job-related emails
- Job parsing using spaCy NLP
- ATS-optimized resume generation
- Automated email sending
- Ayoba chatbot API integration
- Optimized for zero-rated environments

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Ronaldo-hub/job_application_agent.git
   cd job_application_agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Set up environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in the required values:
     - `GH_TOKEN`: Your GitHub personal access token
     - `GITHUB_REPOSITORY`: Your repository (e.g., Ronaldo-hub/job_application_agent)
     - `GOOGLE_CLIENT_ID`: Google OAuth client ID
     - `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
     - `AYOBA_API_TOKEN`: Ayoba API token
     - `SMTP_USER`: SMTP username
     - `SMTP_PASS`: SMTP password

4. **Set up Google OAuth:**
   - Create a project in Google Cloud Console
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download `credentials.json` and place in the project root

## Running the Project

To run the agent:
```bash
python main.py
```

This will initialize the LangGraph workflow with placeholders for all modules.

## Debugging Steps

1. **Check Python version:**
   ```bash
   python --version
   ```
   Ensure it's Python 3.9 or higher.

2. **Validate environment variables:**
   ```bash
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('GOOGLE_CLIENT_ID:', os.getenv('GOOGLE_CLIENT_ID'))"
   ```
   Ensure all required variables are set.

3. **Run linting:**
   ```bash
   flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
   ```

4. **Run tests:**
   ```bash
   pytest
   ```

5. **Check for missing dependencies:**
   ```bash
   pip list
   ```

## Debugging for Issue #2: Multi-user Gmail OAuth

1. **Set up Google OAuth credentials:**
    - Ensure `credentials.json` is in the project root.
    - Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`.

2. **Start the Flask server:**
    ```bash
    python ayoba_bot.py
    ```
    The server should run on http://localhost:5000.

3. **Test OAuth URL generation:**
    ```bash
    python -c "import gmail_tool; print(gmail_tool.get_oauth_url('test_user'))"
    ```
    Should print an authorization URL.

4. **Simulate OAuth callback:**
    - Manually visit the OAuth URL and authorize.
    - Check the callback logs in the terminal.

5. **Verify token storage:**
    ```bash
    python -c "import gmail_tool; print(gmail_tool.get_token('test_user'))"
    ```
    Should print the refresh token if stored.

6. **Test credential retrieval:**
    ```bash
    python -c "import gmail_tool; creds = gmail_tool.get_credentials('test_user'); print('Credentials valid:', creds.valid)"
    ```

7. **Run Gmail tool tests:**
    ```bash
    pytest tests/test_gmail.py -v
    ```

8. **Test workflow integration:**
    ```bash
    python main.py
    ```
    Check logs for Gmail scanning attempts.

9. **Check logs for errors:**
    - Look for OAuth failures, API errors, or DB issues in the console output.

## Debugging for Issue #4: ATS-optimized Resume Generation, Parsing, Auditing, and Document Selection

1. **Set up API keys:**
    - Add `HUGGINGFACE_API_KEY` for Llama 3.1 8B-Instruct access in `.env`
    - Ensure `master_resume.json` exists with user data
    - Verify `requirements.txt` includes `langchain_huggingface` and `pdfplumber`

2. **Test master resume loading:**
    ```bash
    python -c "import resume_tool; print(resume_tool.load_master_resume())"
    ```
    Should print the master resume JSON data.

3. **Test resume parsing from uploaded files:**
    ```bash
    python -c "
    import resume_parser
    # Test with sample PDF/DOCX file path
    # result = resume_parser.parse_resume_file('path/to/resume.pdf')
    # print('Parsed resume:', result)
    print('Resume parser functions available')
    "
    ```
    Should parse resume files to JSON format.

4. **Test resume generation with sample job:**
    ```bash
    python -c "
    import resume_tool
    job = {'job_title': 'Python Developer', 'skills': ['Python', 'Django'], 'employer_email': 'hr@company.com', 'email_id': 'test123'}
    result = resume_tool.generate_resume(job)
    print('Resume generated:', 'content' in result)
    print('Word file:', result.get('word_file', 'N/A'))
    print('PDF file:', result.get('pdf_file', 'N/A'))
    "
    ```
    Should generate ATS-optimized resume files without errors.

5. **Test audit functionality:**
    ```bash
    python -c "
    import audit_tool
    resume_data = {'content': 'Test resume with Python skills', 'job_title': 'Python Developer', 'employer_email': 'hr@company.com'}
    audit = audit_tool.audit_resume(resume_data)
    print('Audit result:', audit['audit_result'])
    "
    ```
    Should return audit report with accuracy score, hallucinations detected, and approval status.

6. **Test document upload and selection:**
    ```bash
    python -c "
    import documents
    # Test document upload (requires file)
    # result = documents.upload_document(file_obj, 'certificate')
    # print('Upload result:', result)

    # Test document selection
    job_details = {'job_title': 'Python Developer', 'skills': ['Python'], 'description': 'Python development role'}
    selected = documents.select_relevant_documents(job_details)
    print('Selected documents:', len(selected))
    "
    ```
    Should handle document uploads and select job-relevant ones.

7. **Check for hallucinations in audit:**
    - Review audit logs for `hallucinations_detected` field
    - Ensure audit compares against `master_resume.json`
    - Verify job skills are properly matched
    - Check for fabricated experiences or skills

8. **Test PDF/Word file generation:**
    ```bash
    python -c "
    import os
    import resume_tool
    content = '''Ronald Williams
ronald@example.com
+27 123 456 789

Summary
Experienced Python developer.

Skills
- Python
- Django

Experience
Software Engineer
Tech Corp
2023-Present
Developed applications.
'''
    word_file = resume_tool.create_word_resume(content, 'debug_resume')
    pdf_file = resume_tool.create_pdf_resume(content, 'debug_resume')
    print('Word file exists:', os.path.exists(word_file))
    print('PDF file exists:', os.path.exists(pdf_file))
    "
    ```
    Should create ATS-friendly files successfully.

9. **Test Ayoba document upload endpoint:**
    ```bash
    # Start Flask server
    python ayoba_bot.py &
    # Then test upload endpoint
    curl -X POST http://localhost:5000/upload_doc \
      -F "file=@certificate.pdf" \
      -F "doc_type=certificate"
    ```
    Should accept document uploads via HTTP.

10. **Test Ayoba webhook commands:**
    ```bash
    # Test !upload_doc command
    curl -X POST http://localhost:5000/ayoba_webhook \
      -H "Content-Type: application/json" \
      -d '{"message": {"sender": "test", "content": "!upload_doc certificate"}}'
    ```
    Should handle Ayoba commands for document uploads.

11. **Run resume and parser tests:**
    ```bash
    pytest tests/test_resume.py tests/test_resume_parser.py -v
    ```
    All tests should pass, including ATS format and hallucination checks.

12. **Test LangGraph integration with new nodes:**
    ```bash
    python -c "
    from main import app
    from main import AgentState
    state = AgentState(
        messages=[], user_id='test', job_emails=[],
        parsed_jobs=[{'job_title': 'Test Job', 'skills': ['Python'], 'employer_email': 'test@company.com', 'email_id': 'test'}],
        parsed_resume={}, generated_resumes=[], audited_resumes=[],
        selected_documents=[], sent_emails=[], ayoba_responses=[]
    )
    result = app.invoke(state)
    print('Parsed resume:', bool(result['parsed_resume']))
    print('Generated resumes:', len(result['generated_resumes']))
    print('Audited resumes:', len(result['audited_resumes']))
    print('Selected documents:', len(result['selected_documents']))
    "
    ```
    Should process through all resume-related nodes.

13. **Check API rate limits and errors:**
    - Monitor logs for Hugging Face API errors (rate limits ~300 req/hour, authentication)
    - Check API connectivity and response times
    - Verify error handling for failed API calls and JSON parsing

14. **Validate ATS optimization:**
    - Check generated resumes for keyword inclusion from job requirements
    - Ensure format is ATS-friendly (Arial 11pt, no tables/headers/footers, plain text header)
    - Verify contact information format: "Name, email, phone"
    - Check skills are bulleted, experience is reverse chronological
    - Confirm certifications are job-relevant

15. **Test document relevance selection:**
    - Upload various documents (certificates, degrees, IDs)
    - Verify Llama selects only job-relevant documents
    - Check metadata storage in `documents.json`
    - Test document path retrieval

16. **Deploy to Render and test in production:**
    - Ensure all environment variables are set in Render
    - Test document uploads via Ayoba interface
    - Verify resume generation and auditing work with real API calls
    - Check error handling for production scenarios

## Project Structure

- `main.py`: Main script with LangGraph workflow
- `requirements.txt`: Python dependencies
- `tests/`: Unit tests
- `.github/workflows/`: CI/CD pipelines
- `.vscode/`: VS Code configuration

## Next Steps

- **Issue #2**: Integrate Gmail API for email scanning
- **Issue #3**: Implement job parsing with spaCy
- **Issue #4**: Create resume generation module
- **Issue #5**: Implement email sending functionality
- **Issue #6**: Add Ayoba API integration
- **Issue #7**: Optimize for Ayoba's zero-rated environment
- **Issue #8**: Add user authentication and multi-user support

## Contributing

Use the provided VS Code tasks for committing with issue references (e.g., #1).

## License

[Add license information here]