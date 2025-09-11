# Job Application Agent with Serious Games Integration

A comprehensive job application and career development platform that integrates serious games with AI-powered job matching, featuring gamification, policy simulations, and POPIA-compliant data handling. The system helps job seekers in Cape Town develop skills, find employment, and explore entrepreneurship through interactive serious games.

**🎮 Serious Games Integration**: Virtonomics, Sim Companies, CWetlands, The Blue Connection
**🤖 AI-Powered**: Llama 3.1 8B for resume generation and recommendations
**🎯 Gamification**: Token system with achievements and leaderboards
**📊 Policy Simulations**: Mesa ABM for social impact analysis
**🔒 POPIA Compliant**: South African data protection standards
**🌍 Cape Town Focus**: Local economic and social data integration

## Architecture Overview

### Single-Agent Architecture with Game Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    Job Application Agent                    │
│                    Single-Agent System                      │
├─────────────────────────────────────────────────────────────┤
│  🤖 Llama 3.1 8B    🎮 Game Integrations    📊 Mesa ABM     │
│  ├─ Resume Gen      ├─ Virtonomics         ├─ Policy Sim    │
│  ├─ Recommendations ├─ Sim Companies       ├─ Social Impact │
│  └─ NLP Processing  ├─ CWetlands          └─ Cape Town Data │
│                      └─ The Blue Connection                 │
├─────────────────────────────────────────────────────────────┤
│  💎 Token System    🔒 POPIA Compliance    🌍 Cape Town     │
│  ├─ Achievements    ├─ Data Anonymization ├─ Local Data     │
│  ├─ Leaderboards    ├─ Audit Logging      ├─ Social Issues  │
│  └─ Rewards         └─ User Rights        └─ Economic Stats │
├─────────────────────────────────────────────────────────────┤
│  🤖 LangGraph Workflow    💬 Discord Bot    ☁️ AWS EC2      │
│  ├─ Job Processing        ├─ Commands       ├─ Free Tier     │
│  ├─ Game Recommendations  ├─ Notifications  ├─ Auto-scaling  │
│  └─ Token Management      └─ Progress       └─ 24/7 Uptime  │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

- **Single AI Agent**: Llama 3.1 8B handles all processing in unified architecture
- **Serious Games**: 4 integrated games for skill development and entrepreneurship
- **Gamification Engine**: Token system with achievements, leaderboards, rewards
- **Policy Simulations**: Mesa ABM for unemployment, water crisis, crime analysis
- **POPIA Compliance**: South African data protection with anonymization
- **Cape Town Focus**: Local economic, social, and environmental data
- **Discord Integration**: Comprehensive bot with 15+ commands
- **AWS EC2**: Free tier deployment with Colab integration

## Features

### 🎮 Serious Games Integration
- **Virtonomics**: Economic simulation for business and logistics skills
- **Sim Companies**: Business management and entrepreneurship training
- **CWetlands**: Environmental management and water conservation
- **The Blue Connection**: Circular economy and sustainability education

### 🤖 AI-Powered Capabilities
- **Resume Generation**: ATS-optimized resumes using Llama 3.1 8B
- **Skill Matching**: Intelligent job-game role recommendations
- **Personalized Learning**: Adaptive course and activity suggestions
- **Policy Analysis**: Data-driven insights for social interventions

### 💎 Gamification & Rewards
- **Token System**: Earn tokens for activities, redeem for premium features
- **Achievements**: Unlock badges for milestones and accomplishments
- **Leaderboards**: Community competition and social comparison
- **Progress Tracking**: Detailed analytics and personalized goals

### 📊 Policy Simulations
- **Unemployment Modeling**: Cape Town-specific job market analysis
- **Water Crisis Scenarios**: Day Zero prevention strategies
- **Crime Prevention**: Social intervention effectiveness
- **Education Investment**: Skills development impact assessment

### 🔒 POPIA Compliance
- **Data Anonymization**: Automatic PII removal and pseudonymization
- **Audit Logging**: Complete data processing records
- **User Rights**: Access, correction, deletion, and portability
- **Consent Management**: Granular permission controls

### 🌍 Cape Town Focus
- **Local Data Integration**: Unemployment, crime, water usage statistics
- **Social Impact**: Addressing youth unemployment, water scarcity, crime
- **Economic Context**: Tourism, finance, technology sector focus
- **Community Benefits**: Skills development and entrepreneurship support

## Setup Instructions

### 1. System Requirements

- **Python**: 3.8 or higher
- **MongoDB**: For token system (local or cloud)
- **Discord Bot Token**: From Discord Developer Portal
- **Hugging Face API Key**: For Llama 3.1 8B integration
- **Game Accounts**: Free accounts for serious games

### 2. Installation

#### Clone and Install Dependencies
```bash
git clone https://github.com/Ronaldo-hub/job_application_agent.git
cd job_application_agent
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

#### MongoDB Setup
```bash
# Install MongoDB locally or use cloud service (MongoDB Atlas free tier)
# For local installation:
# Ubuntu/Debian:
sudo apt-get install mongodb

# macOS:
brew install mongodb-community

# Windows: Download from mongodb.com
```

### 3. Environment Configuration

Create comprehensive `.env` file:
```env
# Discord Bot
DISCORD_BOT_TOKEN=your_discord_bot_token

# AI Models
HUGGINGFACE_API_KEY=your_huggingface_api_key

# Job Search APIs (Free Tiers)
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
SERPAPI_API_KEY=your_serpapi_key
CAREERJET_API_KEY=your_careerjet_key
UPWORK_CLIENT_ID=your_upwork_client_id
UPWORK_CLIENT_SECRET=your_upwork_client_secret
RAPIDAPI_KEY=your_rapidapi_key

# Game Credentials (Optional - for enhanced features)
VIRTONOMICS_USERNAME=your_virtonomics_username
VIRTONOMICS_PASSWORD=your_virtonomics_password
SIMCOMPANIES_USERNAME=your_simcompanies_username
SIMCOMPANIES_PASSWORD=your_simcompanies_password

# Database
MONGODB_URI=mongodb://localhost:27017/job_agent
# Or for MongoDB Atlas:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/job_agent

# POPIA Compliance
DATA_ENCRYPTION_KEY=your_strong_encryption_key_here
DATA_RETENTION_DAYS=2555

# AWS EC2 (for deployment)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=af-south-1

# Google Colab (optional)
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
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

### 4. Serious Games Setup

#### Virtonomics (Free-to-Play Economic Simulation)
1. Visit [virtonomics.com](https://virtonomics.com)
2. Create free account
3. Add credentials to `.env` (optional, enhances recommendations)
4. Explore logistics and business management scenarios

#### Sim Companies (Free Business Management)
1. Visit [simcompanies.com](https://www.simcompanies.com)
2. Create free account via Steam/web
3. Focus on manufacturing and retail business simulations
4. Add credentials to `.env` for enhanced integration

#### CWetlands (Free Environmental Simulation)
1. Visit [constructedwetlands.socialsimulations.org](https://constructedwetlands.socialsimulations.org)
2. Request free moderator access: contact@socialsimulations.org
3. Include project description: "Cape Town job seeker water conservation education"
4. Download offline version for local simulations

#### The Blue Connection (Free Circular Economy)
1. Visit [inchainge.com/business-games/tbc](https://inchainge.com/business-games/tbc)
2. Submit contact form for free trial access
3. Include project details: "Cape Town youth entrepreneurship training"
4. Focus on sustainable business and circular economy principles

### 5. Discord Bot Setup

#### Create Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application: "Job Application Agent"
3. Go to "Bot" section → Add Bot
4. Copy bot token to `.env`
5. Go to "OAuth2" → "URL Generator"
6. Select scopes: `bot`, `applications.commands`
7. Select permissions: `Send Messages`, `Use Slash Commands`, `Attach Files`, `Embed Links`
8. Use generated URL to invite bot to your server

#### Bot Permissions
- **Send Messages**: For recommendations and notifications
- **Use Slash Commands**: For all bot commands
- **Attach Files**: For resume sharing and downloads
- **Embed Links**: For rich content display
- **Read Message History**: For context-aware responses

## Usage Guide

### Starting the System

#### Local Development Setup
```bash
# Terminal 1: Start MongoDB (if using local)
mongod

# Terminal 2: Start Discord Bot
python discord_bot.py

# Terminal 3: Start Main Agent (optional, for background processing)
python main.py
```

#### AWS EC2 Deployment
```bash
# Connect to EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-instance

# Install dependencies
git clone https://github.com/Ronaldo-hub/job_application_agent.git
cd job_application_agent
pip install -r requirements.txt

# Configure environment
nano .env  # Add your configuration

# Start services
python discord_bot.py
```

### Discord Commands Reference

#### 🎯 Job Search & Career Development
- `/search_jobs keywords:"python developer" location:"Cape Town"`: Search and analyze jobs with AI matching
- `/upload_resume`: Upload resume for parsing and game recommendations
- `/my_progress`: View personal progress, achievements, and statistics
- `/track_activity game:"virtonomics" activity:"company_created"`: Track game activities for rewards

#### 🎮 Serious Games Integration
- `/game_recommendations`: Get personalized game recommendations based on skills
- `/virtonomics_help`: Get Virtonomics integration guide and tips
- `/simcompanies_help`: Get Sim Companies business simulation guide
- `/cwetlands_help`: Get CWetlands environmental simulation guide
- `/blueconnection_help`: Get The Blue Connection circular economy guide

#### 💎 Gamification & Rewards
- `/check_tokens`: View current token balance and transaction history
- `/redeem_reward reward_id:"premium_job_listings"`: Redeem tokens for premium features
- `/leaderboard`: View community leaderboard and top performers
- `/achievements`: View available achievements and progress

#### 📊 Policy & Analytics (Policy Makers)
- `/policy_dashboard`: View policy simulation dashboard and key metrics
- `/run_simulation type:"unemployment"`: Run ABM simulation for policy analysis
- `/policy_impact area:"water" timeframe:12`: Analyze policy impact scenarios
- `/cape_town_report`: Generate comprehensive Cape Town impact report
- `/set_policy_priority priority:"education"`: Set policy focus areas

#### 🔒 POPIA Compliance
- `/data_privacy`: View privacy policy and data handling information
- `/delete_my_data`: Request deletion of personal data
- `/export_my_data`: Request export of personal data for download
- `/consent_settings`: Manage data processing consents

#### 🤖 AI & Support
- `/help`: Show all available commands with descriptions
- `/system_status`: Check system health and component status
- `/feedback`: Provide feedback and suggestions

### Complete User Workflow

#### For Job Seekers:
1. **Join Discord Server** and complete onboarding
2. **Upload Resume**: `/upload_resume` for AI parsing and anonymization
3. **Get Recommendations**: Receive personalized game and job suggestions
4. **Play Games**: Engage with serious games for skill development
5. **Track Progress**: Use `/my_progress` to monitor achievements
6. **Earn Rewards**: Accumulate tokens for premium features
7. **Apply for Jobs**: Use AI-generated optimized resumes

#### For Policy Makers:
1. **Access Dashboard**: `/policy_dashboard` for overview
2. **Run Simulations**: `/run_simulation` for policy testing
3. **Analyze Impact**: `/policy_impact` for detailed analysis
4. **Generate Reports**: `/cape_town_report` for comprehensive insights
5. **Set Priorities**: `/set_policy_priority` for focus areas

### Processing Flow

1. **User Interaction**: Discord commands trigger the single-agent system
2. **Data Processing**: Llama 3.1 8B processes requests with POPIA compliance
3. **Game Integration**: Real-time recommendations from serious games
4. **Token Rewards**: Automatic token allocation for completed activities
5. **Progress Tracking**: Continuous monitoring and achievement unlocking
6. **Policy Analysis**: Mesa ABM simulations for data-driven insights
7. **Cape Town Context**: Local data integration for relevant recommendations

## API Configuration & Integrations

### Job Search APIs (Free Tiers)

| API | Free Tier Limits | Purpose | Setup |
|-----|------------------|---------|-------|
| **Adzuna** | 100-250 calls/month | Job search with location | [developer.adzuna.com](https://developer.adzuna.com/) |
| **Careerjet** | Unlimited | Global job search | [careerjet.net](https://www.careerjet.net/) |
| **Upwork** | Basic searches | Freelance opportunities | [developers.upwork.com](https://developers.upwork.com/) |
| **SerpApi** | 100 searches/month | Google Jobs scraping | [serpapi.com](https://serpapi.com/) |
| **RapidAPI** | Limited calls | Aggregated job listings | [rapidapi.com](https://rapidapi.com/) |

### Serious Games APIs

| Game | Access Method | Purpose | Setup |
|------|----------------|---------|-------|
| **Virtonomics** | Community Framework | Economic simulation | [github.com/antonsolomko/virtonomics](https://github.com/antonsolomko/virtonomics) |
| **Sim Companies** | Web Scraping/API | Business management | [simcompanies.com](https://www.simcompanies.com/) |
| **CWetlands** | Email Request | Environmental simulation | contact@socialsimulations.org |
| **The Blue Connection** | Trial Request | Circular economy | info@inchainge.com |

### AI & ML Services

| Service | Purpose | Free Tier | Setup |
|---------|---------|-----------|-------|
| **Hugging Face** | Llama 3.1 8B inference | 30K tokens/month | [huggingface.co](https://huggingface.co/) |
| **spaCy** | NLP processing | Unlimited | `python -m spacy download en_core_web_sm` |
| **scikit-learn** | ML algorithms | Unlimited | pip install scikit-learn |

### Infrastructure & Database

| Service | Purpose | Free Tier | Setup |
|---------|---------|-----------|-------|
| **MongoDB Atlas** | Token system database | 512MB storage | [mongodb.com/atlas](https://www.mongodb.com/atlas) |
| **AWS EC2** | Application hosting | 750 hours/month | [aws.amazon.com/ec2](https://aws.amazon.com/ec2/) |
| **Google Colab** | Resource-intensive processing | Unlimited | [colab.research.google.com](https://colab.research.google.com/) |

### API Key Setup Guide

#### Hugging Face (Required)
1. Sign up at [huggingface.co](https://huggingface.co/join)
2. Navigate to Settings → Access Tokens
3. Create new token with "Read" permissions
4. Add to `.env`: `HUGGINGFACE_API_KEY=your_token_here`

#### Discord Bot (Required)
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application
3. Go to "Bot" section → Add Bot
4. Copy token to `.env`: `DISCORD_BOT_TOKEN=your_token_here`

#### MongoDB Atlas (Recommended)
1. Sign up at [mongodb.com/atlas](https://www.mongodb.com/atlas)
2. Create free cluster
3. Get connection string
4. Add to `.env`: `MONGODB_URI=your_connection_string`

#### Game Credentials (Optional)
```env
# Virtonomics (optional)
VIRTONOMICS_USERNAME=your_username
VIRTONOMICS_PASSWORD=your_password

# Sim Companies (optional)
SIMCOMPANIES_USERNAME=your_username
SIMCOMPANIES_PASSWORD=your_password
```

### Cost Estimation

| Component | Free Tier Limits | Estimated Monthly Cost |
|-----------|------------------|------------------------|
| **Hugging Face** | 30K tokens | $0 (sufficient for 100 users) |
| **Discord** | Unlimited | $0 |
| **MongoDB Atlas** | 512MB | $0 |
| **AWS EC2** | 750 hours | $0 (t2.micro free tier) |
| **Job APIs** | Various | $0 (free tiers) |
| **Serious Games** | All free | $0 |
| **Total** | - | **$0/month** for basic usage |

*Costs may increase with high usage or premium features*

## Testing & Quality Assurance

### Automated System Testing

#### Run Comprehensive Test Suite
```bash
# Run full system test
python test_single_agent.py

# Expected output: All components tested and validated
# ✅ Llama integration test passed
# ✅ Game integrations working
# ✅ ABM simulations functional
# ✅ Token system operational
# ✅ POPIA compliance verified
# ✅ Cape Town data integrated
# ✅ Activity tracking working
# 🎉 All tests passed! Single-agent architecture is ready for deployment.
```

#### Component-Specific Testing
```bash
# Test individual components
python -c "import llama_integration; print('Llama:', llama_integration.test_connection())"
python -c "import game_integrations; print('Games:', game_integrations.test_all())"
python -c "import mesa_simulations; print('ABM:', mesa_simulations.test_simulations())"
python -c "import popia_compliance; print('POPIA:', popia_compliance.test_compliance())"
```

### Manual Testing Scenarios

#### User Journey Testing
1. **Onboarding**: New user joins Discord, uploads resume
2. **AI Processing**: System parses resume, generates recommendations
3. **Game Integration**: User receives personalized game suggestions
4. **Progress Tracking**: User completes activities, earns tokens
5. **Achievement Unlocking**: System recognizes milestones
6. **Policy Analysis**: Policy makers run simulations

#### Discord Bot Testing
```bash
# Test bot commands
/search_jobs keywords:"data scientist" location:"Cape Town"
/my_progress
/track_activity game:"virtonomics" activity:"company_created"
/policy_dashboard
/run_simulation type:"unemployment"
/cape_town_report
```

#### Game Integration Testing
- **Virtonomics**: Test company creation and logistics activities
- **Sim Companies**: Test business setup and profit generation
- **CWetlands**: Test water management scenarios
- **The Blue Connection**: Test circular economy activities

### Performance Testing

#### Load Testing
```bash
# Test concurrent users
python -m pytest tests/ -v --tb=short -k "load"

# Test API rate limits
python -c "import api_rate_limiter; api_rate_limiter.test_limits()"

# Test database performance
python -c "import db_performance; db_performance.benchmark()"
```

#### Memory and Resource Testing
```bash
# Monitor system resources
python -c "import resource_monitor; resource_monitor.start_monitoring()"

# Test large dataset processing
python -c "import data_processing; data_processing.test_large_dataset()"
```

### Quality Assurance Checklist

#### Functional Testing ✅
- [ ] Resume upload and parsing
- [ ] Job search and matching
- [ ] Game recommendations
- [ ] Token system transactions
- [ ] Achievement unlocking
- [ ] Progress tracking
- [ ] Discord bot commands
- [ ] Policy simulations

#### Security Testing ✅
- [ ] POPIA compliance verification
- [ ] Data anonymization testing
- [ ] API key security validation
- [ ] User consent management
- [ ] Audit logging verification

#### Performance Testing ✅
- [ ] Response time validation (<2s for commands)
- [ ] Memory usage monitoring
- [ ] Database query optimization
- [ ] API rate limit handling
- [ ] Concurrent user support

#### Integration Testing ✅
- [ ] Discord bot integration
- [ ] Game API connectivity
- [ ] Database operations
- [ ] AI model inference
- [ ] External API dependencies

### Deployment Testing

#### Local Development
```bash
# Start all services locally
docker-compose up -d mongodb
python discord_bot.py &
python main.py &

# Test full workflow
curl -X POST localhost:5000/test_workflow
```

#### AWS EC2 Testing
```bash
# Deploy to EC2
eb deploy job-application-agent

# Test deployed system
curl https://your-app.elasticbeanstalk.com/health

# Monitor logs
eb logs --stream
```

### Monitoring & Debugging

#### System Health Checks
```bash
# Check all components
python -c "import system_health; system_health.full_check()"

# Monitor performance metrics
python -c "import metrics_collector; metrics_collector.show_dashboard()"
```

#### Error Handling
```bash
# Test error scenarios
python -c "import error_testing; error_testing.run_error_scenarios()"

# Validate fallback mechanisms
python -c "import fallback_testing; fallback_testing.test_fallbacks()"
```

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