# Job Application Agent with Google Colab Integration

A distributed job application agent that prevents bottlenecks in GitHub Codespaces by offloading resource-intensive NLP tasks to Google Colab's free tier. The system searches jobs from free-tier APIs, analyzes fit scores, generates ATS-optimized resumes, and suggests courses for skill gaps.

## Architecture Overview

### Distributed Processing Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   VS Code       │    │  Google Drive   │    │   Google Colab  │
│   (Main Agent)  │◄──►│   (Data Exchange)│◄──►│ (Resource-Intensive│
│                 │    │                 │    │      Tasks)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ├─ Discord Bot         ├─ Job Data            ├─ NLP Processing
         ├─ Workflow Control    ├─ Fit Analysis        ├─ Resume Generation
         ├─ API Orchestration   ├─ Course Suggestions  ├─ Status Updates
         └─ Result Aggregation  └─ Task Coordination   └─ GPU/TPU Access
```

### Key Components

- **VS Code Agent**: Main orchestration, Discord bot, workflow control
- **Google Colab Processor**: Heavy NLP, API batch processing, resume generation
- **Google Drive**: Secure data exchange between VS Code and Colab
- **Free-Tier APIs**: Adzuna, Careerjet, Upwork, SerpApi, RapidAPI

## Features

- **Bottleneck Prevention**: Offloads intensive tasks to Colab's 12GB RAM + GPU
- **Free-Tier APIs**: Uses only free-tier job search APIs
- **Intelligent Fit Analysis**: spaCy + TF-IDF similarity scoring (≥90% threshold)
- **ATS-Optimized Resumes**: Generated only for high-fit jobs
- **Course Suggestions**: Free learning resources for skill gaps
- **Discord Integration**: Real-time notifications and commands
- **Graceful Fallbacks**: Local processing when Colab unavailable

## Setup Instructions

### 1. VS Code Setup

#### Install Dependencies
```bash
git clone https://github.com/your-org/job_application_agent.git
cd job_application_agent
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

#### Environment Variables
Create `.env` file:
```env
# Discord
DISCORD_BOT_TOKEN=your_discord_bot_token

# Google Drive (for Colab integration)
GOOGLE_APPLICATION_CREDENTIALS=credentials.json

# Free-Tier Job APIs
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
SERPAPI_API_KEY=your_serpapi_key
CAREERJET_API_KEY=your_careerjet_key
UPWORK_CLIENT_ID=your_upwork_client_id
UPWORK_CLIENT_SECRET=your_upwork_client_secret
RAPIDAPI_KEY=your_rapidapi_key

# Optional
HUGGINGFACE_API_KEY=your_huggingface_key
```

#### Google Drive Setup for VS Code
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Drive API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download `credentials.json` to project root
6. First run will open browser for authentication

### 2. Google Colab Setup

#### Create Colab Notebook
1. Go to [Google Colab](https://colab.research.google.com/)
2. Create new notebook: `colab_processor.ipynb`
3. Copy the content from `colab_processor.py` into the notebook

#### Mount Google Drive in Colab
```python
from google.colab import drive
drive.mount('/content/drive')
```

#### Install Dependencies in Colab
```python
!pip install discord.py requests httpx spacy scikit-learn beautifulsoup4 lxml
!python -m spacy download en_core_web_sm
```

#### Set up Colab Secrets
```python
# For Colab secrets (optional, can use environment variables)
from google.colab import userdata
# Add secrets in Colab: Settings > Secrets
```

#### Upload Colab Processor
```python
# Copy colab_processor.py content to Colab cell
# Run the processor
```

### 3. Discord Bot Setup

#### Create Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application
3. Go to "Bot" section → Add Bot
4. Copy bot token to `.env`
5. Go to "OAuth2" → "URL Generator"
6. Select scopes: `bot`, `applications.commands`
7. Select permissions: `Send Messages`, `Use Slash Commands`, `Attach Files`
8. Use generated URL to invite bot to your server

## Usage

### Starting the System

#### 1. Start Colab Processor
```python
# In Colab notebook
from colab_processor import ColabProcessor
import asyncio

processor = ColabProcessor()
processor.setup_colab_environment()
asyncio.run(processor.main_processing_loop())
```

#### 2. Start VS Code Agent
```bash
# Terminal 1: Discord Bot
python discord_bot.py

# Terminal 2: Main Agent
python main.py
```

### Discord Commands

- `/search_jobs keywords:"python developer" location:"remote"`: Search and analyze jobs
- `/help`: Show available commands

### Processing Flow

1. **User Command**: Discord bot receives `/search_jobs`
2. **Job Search**: VS Code submits to Colab or processes locally
3. **Fit Analysis**: Colab analyzes job requirements vs resume
4. **Resume Generation**: Only for jobs with ≥90% fit score
5. **Course Suggestions**: Based on skill gaps from low-fit jobs
6. **Notifications**: Results sent back via Discord

## API Configuration

### Free-Tier APIs Used

| API | Free Tier Limits | Purpose |
|-----|------------------|---------|
| **Adzuna** | 100-250 calls/month | Job search with location |
| **Careerjet** | Unlimited | Global job search |
| **Upwork** | Basic searches | Freelance opportunities |
| **SerpApi** | Limited searches | Google Jobs scraping |
| **RapidAPI** | Limited calls | Aggregated job listings |

### API Key Setup

#### Adzuna
1. Sign up at [Adzuna](https://developer.adzuna.com/)
2. Get App ID and App Key
3. Add to `.env` or Colab secrets

#### SerpApi
1. Sign up at [SerpApi](https://serpapi.com/)
2. Get API key
3. Free tier: 100 searches/month

#### RapidAPI
1. Sign up at [RapidAPI](https://rapidapi.com/)
2. Subscribe to JSearch API (free tier available)
3. Get API key

## Testing

### Local Testing (VS Code Only)
```bash
# Test without Colab
python -c "import colab_integration; print('Colab available:', colab_integration.check_colab_status())"

# Test job search
python -c "import asyncio, job_search; result = asyncio.run(job_search.search_jobs_async({'keywords': 'python'})); print(f'Found {len(result)} jobs')"
```

### Colab Integration Testing
```python
# Test Colab connectivity
from colab_integration import check_colab_status, get_colab_status
print("Colab available:", check_colab_status())
print("Status:", get_colab_status())
```

### End-to-End Testing
1. Start Colab processor
2. Start VS Code agent
3. Use Discord command `/search_jobs keywords:"python"`
4. Verify results in Discord channel

## Troubleshooting

### Common Issues

#### Colab Connection Issues
```python
# Check Colab status
from colab_integration import get_colab_status
status = get_colab_status()
print("Colab status:", status)
```

#### API Rate Limits
- **Adzuna**: Monitor usage in dashboard
- **SerpApi**: Check remaining searches
- **RapidAPI**: Monitor call limits

#### Google Drive Issues
```python
# Test Drive connection
from colab_integration import ColabIntegration
integration = ColabIntegration()
print("Drive connected:", integration.drive_service is not None)
```

### Colab Runtime Limits
- **12-24 hour limit**: Save important data to Drive
- **Disconnect handling**: Use Firebase for persistent bot hosting
- **GPU availability**: Enable in Runtime > Change runtime type

## Deployment Options

### Option 1: Colab + VS Code (Recommended)
- Best for development and testing
- Free Colab resources
- Easy to modify and debug

### Option 2: Firebase Functions + Colab
- Deploy Discord bot to Firebase (125K invocations/month free)
- Use Colab for processing
- More production-ready

### Option 3: Local Processing Only
- Remove Colab dependencies
- Use local spaCy and scikit-learn
- Good for high-performance local machines

## Architecture Benefits

### Performance Improvements
- **NLP Processing**: Colab GPU accelerates spaCy operations
- **Parallel API Calls**: Async processing in Colab
- **Memory Management**: 12GB RAM prevents Codespaces bottlenecks

### Cost Optimization
- **Free Resources**: Colab free tier + free API tiers
- **Pay-per-Use**: Only process when needed
- **Scalable**: Easy to upgrade to paid tiers if needed

### Reliability Features
- **Graceful Fallbacks**: Local processing when Colab unavailable
- **Status Monitoring**: Real-time Colab processor status
- **Error Recovery**: Automatic retries and fallbacks

## Contributing

1. Fork the repository
2. Create feature branch
3. Test with both Colab and local processing
4. Submit pull request

## License

MIT License