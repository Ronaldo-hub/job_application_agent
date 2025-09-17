Job Application Agent Refactor Specification
Refactor the existing Job Application Agent app (originally in https://github.com/Ronaldo-hub/job_application_agent) into a modular MCP + Docker setup, running in VSCode Codespaces with a browser-based Streamlit UI. The app supports resume uploads, job email searches, ATS-optimized resume generation, and team simulations, with serious games integration, gamification, and POPIA compliance for Cape Town job seekers. Fully automate the setup to eliminate all manual prompts (e.g., "Run Command" for Git, Docker, or tests), including running git pull origin main on startup, using devcontainer.json, tasks.json, and setup.sh. Add enhanced team simulation to match resume skills with collaborative activities for economic value and local issue resolution, forming groups. Log errors to MongoDB to track past issues and solutions for LLM debugging. Follow these requirements:
General Requirements

Modular Design: Create separate Docker containers for each function (resume-upload, job-search, ats-optimize, team-sim, discord-bot, game-integration) using FastAPI for MCP endpoints and Streamlit for the UI.
MCP Integration: Expose MCP endpoints (e.g., /mcp/resume/upload) for LLM (e.g., Grok or Llama 3.1 8B via Hugging Face) interaction.
API Keys: Store all keys (HUGGINGFACE_API_KEY, DISCORD_BOT_TOKEN, ADZUNA_APP_ID, ADZUNA_APP_KEY, SERPAPI_API_KEY, CAREERJET_API_KEY, UPWORK_CLIENT_ID, UPWORK_CLIENT_SECRET, RAPIDAPI_KEY, GOOGLE_APPLICATION_CREDENTIALS, MONGODB_URI, DATA_ENCRYPTION_KEY) in .env, loaded with python-dotenv to avoid forgetting (previous issue).
Automation:
Use .devcontainer/devcontainer.json (postCreateCommand) to run setup.sh.
Configure tasks.json to auto-run docker-compose up -d and pytest on folder open.
Include git pull origin main in setup.sh to sync repo on startup.
Add .vscode/settings.json to disable Git prompts (git.confirmSync: false, git.autoRepositoryDetection: false).
Ensure no manual prompts for Git, Docker, or tests.


Error Logging: Store errors (e.g., API failures, runtime exceptions) in MongoDB collection error_logs with fields: timestamp, module, error_message, stack_trace, solution_applied, success. Provide MCP endpoint /mcp/errors/query for LLMs to retrieve past issues/solutions.
Git: Commit changes after each successful generation: git commit -m "Refactored module X".
Commoditization: Ensure modular containers are shareable via Docker Hub for individual sale (e.g., resume-upload tool).<grok:render type="render_inline_citation">

34

Codespaces: Run in VSCode Codespaces with forwarded ports (8001-8006 for servers, 8501 for Streamlit, 27017 for MongoDB).

Features

Resume Upload

Endpoint: POST /mcp/resume/upload
Functionality: Upload txt/pdf resumes via Streamlit, save to ./uploads, anonymize PII (POPIA compliance), return file path for LLM access.
Tech: FastAPI, python-multipart, spacy for PII detection, MongoDB for metadata.


Job Email Search

Endpoint: GET /mcp/jobs/query
Functionality: Use Gmail API (OAuth2) to search emails for "job" or "offer," extract job titles/roles using regex or spacy.
Tech: google-api-python-client, persist token.json in ./uploads.


ATS-Optimized Resume

Endpoint: POST /mcp/resume/optimize
Functionality: Optimize resume for ATS using Llama 3.1 8B (Hugging Face API) based on job description, focusing on keywords and formatting.
Tech: FastAPI, requests, Hugging Face API.


Team Simulation

Endpoint: POST /mcp/team/simulate
Functionality: Extract skills from uploaded resumes (using spacy NLP), match to collaborative activities (e.g., entrepreneurship projects like starting a tech startup, community garden, or water recycling initiative) to create economic value in Cape Town. Address local issues (unemployment, water scarcity, crime) by forming groups (3-5 members) based on skill synergy (e.g., coder + marketer + designer). Output group details and activity plans.
Tech: FastAPI, spacy, scikit-learn for clustering, external APIs (e.g., RapidAPI for market trends).


Discord Bot

Endpoint: POST /mcp/discord/command
Functionality: Handle Discord commands (e.g., /search_jobs, /upload_resume, /policy_dashboard) via MCP, integrating with other services.
Tech: discord.py, FastAPI.


Game Integration

Endpoint: GET /mcp/games/recommend
Functionality: Recommend serious games (Virtonomics, Sim Companies, CWetlands, The Blue Connection) based on resume skills and user progress. Track activities in MongoDB.
Tech: FastAPI, requests for game APIs, MongoDB.



File Structure
community-app/
├── .devcontainer/devcontainer.json
├── .vscode/settings.json
├── .vscode/tasks.json
├── .env
├── docker-compose.yml
├── setup.sh
├── tests/
│   ├── test_resume.py
│   ├── test_jobs.py
│   ├── test_ats.py
│   ├── test_team.py
│   ├── test_discord.py
│   ├── test_games.py
├── resume-upload/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── mcp_resume.py
├── job-search/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── mcp_jobs.py
├── ats-optimize/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── mcp_ats.py
├── team-sim/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── mcp_team.py
├── discord-bot/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── mcp_discord.py
├── game-integration/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── mcp_games.py
├── streamlit-ui/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
├── uploads/
├── credentials.json  # Google OAuth2

Existing Code

Repo: https://github.com/Ronaldo-hub/job_application_agent
Structure: Single-agent system with main.py, discord_bot.py, colab_processor.py, and supporting scripts (llama_integration.py, game_integrations.py, mesa_simulations.py, popia_compliance.py).
Key Logic to Preserve:
Resume parsing: spacy (en_core_web_sm) for PII and skill extraction.
Job search: Regex (re.search(r'(?:position|role):?\s*([A-Za-z\s]+)', body)) and Gmail API.
ATS optimization: Llama 3.1 8B via Hugging Face API.
Game integration: API calls/web scraping for Virtonomics, Sim Companies, etc.
POPIA compliance: Data anonymization and audit logging.
Discord bot: Commands like /search_jobs, /upload_resume.


Fixes to Retain:
Use .env with os.getenv() for all API keys to prevent forgetting.
MongoDB (MONGODB_URI) for token system and now error logging.
OAuth2 token persistence in token.json.



Automation Requirements

Eliminate All Prompts:
Run git pull origin main in setup.sh to sync repo on startup.
Auto-run docker-compose up -d and pytest via tasks.json on folder open.
Install dependencies and handle OAuth2 auth (Google Drive/Gmail) in setup.sh.
Disable Git prompts in .vscode/settings.json (git.confirmSync: false).
Ensure no manual "Run" prompts for Git, Docker, or tests.


OAuth2 Setup: Automate Google Drive/Gmail auth by generating token.json via google-auth-oauthlib in setup.sh.
Error Logging: Create MongoDB collection error_logs with schema:{
  "timestamp": "ISODate",
  "module": "str (e.g., resume-upload)",
  "error_message": "str",
  "stack_trace": "str",
  "solution_applied": "str (e.g., Updated .env loading)",
  "success": "bool"
}

Log errors in each module and provide /mcp/errors/query endpoint for LLMs to retrieve past issues/solutions.

Debugging Notes

Previous Issues:
AI forgot API keys after code regeneration. Fixed by using .env and os.getenv().
Manual "Run Command" prompts for Git operations (e.g., git pull). Fixed by automating in setup.sh and disabling Git prompts in settings.json.


New Issue: Recurring bugs from LLM code gen. Mitigate by:
Logging errors to MongoDB error_logs.
Prompting LLM to query /mcp/errors/query for past solutions or suggest new ones if unresolved.
Committing fixes to Git: git commit -m "Fixed module X".


Tests: Generate pytest tests for each module to verify functionality and catch regressions.

Prompt Instructions

Refactor existing code from https://github.com/Ronaldo-hub/job_application_agent into the modular MCP + Docker structure above.
Incorporate existing logic (resume parsing, job search, etc.) into respective modules.
Generate all files (Dockerfile, requirements.txt, Python scripts, tests, settings.json) with comments for MCP integration and API key handling.
Ensure full automation via devcontainer.json, tasks.json, setup.sh, and settings.json, eliminating all manual prompts (including Git "Run Command").
Add team simulation feature to match resume skills with collaborative activities for Cape Town economic value and issue resolution, forming groups.
Implement error logging to MongoDB with /mcp/errors/query endpoint.
Run in Codespaces with browser access (Streamlit at :8501, MongoDB at :27017).
Preserve all fixes and commit to Git to prevent regressions.
