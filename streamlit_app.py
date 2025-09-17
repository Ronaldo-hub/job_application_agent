"""
Enhanced Streamlit UI for Job Application Agent
Provides a comprehensive dashboard for the job application workflow
"""

import streamlit as st
import requests
import json
from datetime import datetime
import os
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
import asyncio
import threading

# Configure page
st.set_page_config(
    page_title="Job Application Agent",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoints for all services
API_ENDPOINTS = {
    "core": "http://core-orchestrator:8000",
    "resume": "http://resume-upload:8001",
    "job_search": "http://job-search:8002",
    "ats": "http://ats-optimize:8003",
    "team_sim": "http://team-sim:8004",
    "game": "http://game-integration:8005",
    "discord": "http://discord-bot:8006"
}

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = "user_" + str(int(time.time()))

if 'workflow_status' not in st.session_state:
    st.session_state.workflow_status = {}

if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

def main():
    st.title("🚀 Job Application Agent Dashboard")
    st.markdown("AI-powered comprehensive job search and application platform")

    # User identification
    col1, col2 = st.columns([3, 1])
    with col1:
        st.session_state.user_id = st.text_input("User ID", value=st.session_state.user_id, key="user_id_input")
    with col2:
        if st.button("🔄 Refresh Data"):
            st.rerun()

    # Sidebar navigation with enhanced options
    st.sidebar.title("📋 Navigation")
    page = st.sidebar.radio(
        "Select Module",
        ["📊 Dashboard Overview", "📄 Resume Management", "🔍 Job Discovery",
         "🎯 ATS Optimization", "📈 Team Simulations", "🎮 Gamification Hub",
         "📋 Workflow Monitoring", "⚙️ Settings"],
        index=0
    )

    # Real-time status indicator
    with st.sidebar:
        st.markdown("---")
        st.subheader("🔴 System Status")
        status_col1, status_col2 = st.columns(2)
        with status_col1:
            st.metric("Last Update", f"{(datetime.now() - st.session_state.last_update).seconds}s ago")
        with status_col2:
            st.success("🟢 Online")

    # Route to appropriate page
    page_map = {
        "📊 Dashboard Overview": show_dashboard,
        "📄 Resume Management": show_resume_management,
        "🔍 Job Discovery": show_job_discovery,
        "🎯 ATS Optimization": show_ats_optimization,
        "📈 Team Simulations": show_team_simulations,
        "🎮 Gamification Hub": show_gamification_hub,
        "📋 Workflow Monitoring": show_workflow_monitoring,
        "⚙️ Settings": show_settings
    }

    page_map[page]()

# Utility functions
def make_api_call(service: str, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
    """Make API call to specified service"""
    try:
        url = f"{API_ENDPOINTS[service]}{endpoint}"
        if method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            response = requests.get(url, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return {"error": str(e)}

def update_last_refresh():
    """Update last refresh timestamp"""
    st.session_state.last_update = datetime.now()

# Dashboard Overview
def show_dashboard():
    st.header("📊 Dashboard Overview")

    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Get workflow stats from core orchestrator
        workflow_data = make_api_call("core", "/mcp/resources/mongodb://job_application_agent/workflows")
        workflow_count = len(workflow_data.get("content", []))
        st.metric("Total Workflows", workflow_count, "↗️ Active")

    with col2:
        # Get job search stats
        job_data = make_api_call("job_search", "/mcp/resources/mongodb://job_application_agent/job_searches")
        job_count = len(job_data.get("content", []))
        st.metric("Jobs Searched", job_count, "🔍")

    with col3:
        # Get gamification stats
        game_data = make_api_call("game", "/mcp/tools/call", "POST",
                                {"name": "get_gamification_leaderboard", "arguments": {"limit": 1}})
        st.metric("Active Users", "42", "👥")  # Placeholder

    with col4:
        # Get simulation stats
        sim_data = make_api_call("team_sim", "/mcp/resources/mongodb://job_application_agent/simulations")
        sim_count = len(sim_data.get("content", []))
        st.metric("Simulations Run", sim_count, "📈")

    # Charts Row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Activity Trends")
        # Mock data for demonstration
        activity_data = pd.DataFrame({
            'Date': pd.date_range(start='2024-01-01', periods=7),
            'Workflows': [5, 8, 12, 15, 18, 22, 25],
            'Job Searches': [10, 15, 20, 25, 30, 35, 40]
        })
        fig = px.line(activity_data, x='Date', y=['Workflows', 'Job Searches'],
                     title="Weekly Activity")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🎯 Success Metrics")
        # Mock success metrics
        success_data = pd.DataFrame({
            'Category': ['Resume Upload', 'Job Match', 'Application', 'Interview'],
            'Success Rate': [95, 78, 65, 45]
        })
        fig = px.bar(success_data, x='Category', y='Success Rate',
                    title="Success Rates by Stage")
        st.plotly_chart(fig, use_container_width=True)

    # Recent Activity Feed
    st.subheader("🔔 Recent Activity")
    with st.expander("View Recent Activities", expanded=True):
        activities = [
            {"time": "2 min ago", "action": "Resume optimized for Senior Developer position", "status": "✅ Success"},
            {"time": "15 min ago", "action": "Job search completed: 25 matches found", "status": "✅ Success"},
            {"time": "1 hour ago", "action": "Team simulation: Unemployment policy analysis", "status": "✅ Success"},
            {"time": "2 hours ago", "action": "Gamification: 50 tokens earned", "status": "✅ Success"}
        ]

        for activity in activities:
            col1, col2, col3 = st.columns([2, 6, 2])
            with col1:
                st.write(f"🕒 {activity['time']}")
            with col2:
                st.write(activity['action'])
            with col3:
                st.write(activity['status'])

    # Quick Actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📄 Upload Resume", use_container_width=True):
            st.session_state.page = "📄 Resume Management"
            st.rerun()

    with col2:
        if st.button("🔍 Search Jobs", use_container_width=True):
            st.session_state.page = "🔍 Job Discovery"
            st.rerun()

    with col3:
        if st.button("🎯 Optimize Resume", use_container_width=True):
            st.session_state.page = "🎯 ATS Optimization"
            st.rerun()

    with col4:
        if st.button("🎮 Check Rewards", use_container_width=True):
            st.session_state.page = "🎮 Gamification Hub"
            st.rerun()

# Resume Management
def show_resume_management():
    st.header("📄 Resume Management")

    tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload", "📋 View Resumes", "🔄 Merge", "📊 Analytics"])

    with tab1:
        st.subheader("Upload New Resume")

        uploaded_file = st.file_uploader("Choose a resume file", type=['pdf', 'docx', 'txt'])
        anonymize = st.checkbox("Anonymize personal data (POPIA compliant)", value=True)

        if uploaded_file is not None:
            if st.button("🚀 Upload & Parse Resume"):
                with st.spinner("Uploading and parsing resume..."):
                    # Upload file to resume service
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {"user_id": st.session_state.user_id, "anonymize": anonymize}

                    try:
                        response = requests.post(f"{API_ENDPOINTS['resume']}/upload-resume",
                                               files=files, data=data, timeout=60)

                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ Resume uploaded successfully!")
                            st.json(result)
                            update_last_refresh()
                        else:
                            st.error(f"Upload failed: {response.text}")
                    except Exception as e:
                        st.error(f"Connection error: {str(e)}")

    with tab2:
        st.subheader("Your Resumes")

        # Get user's resumes
        resume_data = make_api_call("resume", "/mcp/resources/mongodb://job_application_agent/resumes")
        resumes = resume_data.get("content", [])

        if resumes:
            for resume in resumes[:5]:  # Show last 5
                with st.expander(f"Resume from {resume.get('timestamp', 'Unknown')}"):
                    st.json(resume)
        else:
            st.info("No resumes found. Upload your first resume!")

    with tab3:
        st.subheader("Merge Resume Data")

        st.info("Select resumes to merge into your master resume")

        # This would implement resume merging functionality
        if st.button("🔄 Merge Selected Resumes"):
            st.info("Resume merging functionality would be implemented here")

    with tab4:
        st.subheader("Resume Analytics")

        # Mock analytics data
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Resumes", "3")
            st.metric("Avg. Completeness", "85%")

        with col2:
            st.metric("Skills Extracted", "24")
            st.metric("Last Updated", "2 days ago")

# Job Discovery
def show_job_discovery():
    st.header("🔍 Job Discovery")

    tab1, tab2, tab3 = st.tabs(["🔎 Search Jobs", "📊 Analytics", "📋 History"])

    with tab1:
        st.subheader("Advanced Job Search")

        col1, col2 = st.columns(2)

        with col1:
            keywords = st.text_input("Job Keywords", "software engineer")
            location = st.text_input("Location", "Cape Town")
            company = st.text_input("Company (optional)")

        with col2:
            max_age = st.slider("Max Job Age (days)", 1, 30, 7)
            salary_min = st.number_input("Min Salary", 0, 1000000, 0)
            remote_work = st.checkbox("Remote work only")

        if st.button("🔍 Search Jobs", type="primary"):
            with st.spinner("Searching across multiple job platforms..."):
                # Call job search API
                search_data = {
                    "name": "search_jobs_multi_api",
                    "arguments": {
                        "keywords": keywords,
                        "location": location,
                        "max_age_days": max_age,
                        "salary_min": salary_min,
                        "user_id": st.session_state.user_id
                    }
                }

                result = make_api_call("job_search", "/mcp/tools/call", "POST", search_data)

                if "error" not in result:
                    st.success("✅ Job search completed!")
                    st.info(f"Found jobs matching '{keywords}' in {location}")
                    update_last_refresh()
                else:
                    st.error(f"Search failed: {result['error']}")

    with tab2:
        st.subheader("Job Market Analytics")

        # Mock analytics
        col1, col2 = st.columns(2)

        with col1:
            # Job distribution by location
            location_data = pd.DataFrame({
                'Location': ['Cape Town', 'Johannesburg', 'Remote', 'Durban', 'Pretoria'],
                'Jobs': [45, 32, 28, 15, 12]
            })
            fig = px.pie(location_data, values='Jobs', names='Location',
                        title="Jobs by Location")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Salary trends
            salary_data = pd.DataFrame({
                'Role': ['Junior Dev', 'Mid Dev', 'Senior Dev', 'Lead Dev', 'Architect'],
                'Avg Salary': [45000, 75000, 110000, 140000, 180000]
            })
            fig = px.bar(salary_data, x='Role', y='Avg Salary',
                        title="Average Salaries")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Search History")

        # Get search history
        history_data = make_api_call("job_search", "/mcp/tools/call", "POST",
                                   {"name": "get_job_search_history",
                                    "arguments": {"user_id": st.session_state.user_id}})

        st.info("Search history would be displayed here")

# ATS Optimization
def show_ats_optimization():
    st.header("🎯 ATS Optimization")

    tab1, tab2, tab3 = st.tabs(["⚡ Quick Optimize", "🔍 Deep Analysis", "📈 Performance"])

    with tab1:
        st.subheader("Quick Resume Optimization")

        job_title = st.text_input("Target Job Title", "Software Engineer")
        job_description = st.text_area("Job Description (paste here)", height=100)

        if st.button("🚀 Optimize Resume", type="primary"):
            with st.spinner("Analyzing and optimizing resume..."):
                # Call ATS optimization API
                optimize_data = {
                    "name": "generate_ats_resume",
                    "arguments": {
                        "user_id": st.session_state.user_id,
                        "job_data": {
                            "title": job_title,
                            "description": job_description
                        },
                        "format": "both"
                    }
                }

                result = make_api_call("ats", "/mcp/tools/call", "POST", optimize_data)

                if "error" not in result:
                    st.success("✅ Resume optimized successfully!")
                    st.info("Optimized resume generated with improved ATS compatibility")
                    update_last_refresh()
                else:
                    st.error(f"Optimization failed: {result['error']}")

    with tab2:
        st.subheader("Deep ATS Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Keyword Match", "78%", "↗️ +5%")
            st.metric("Format Score", "92%", "↗️ +2%")

        with col2:
            st.metric("Readability", "85%", "↗️ +3%")
            st.metric("Completeness", "94%", "↗️ +1%")

        # Analysis details
        with st.expander("View Detailed Analysis"):
            st.write("### Missing Keywords")
            st.write("• Docker, Kubernetes, AWS")
            st.write("• Agile, Scrum, CI/CD")
            st.write("• React, Node.js, TypeScript")

            st.write("### Recommendations")
            st.write("• Add more quantifiable achievements")
            st.write("• Include relevant certifications")
            st.write("• Optimize summary section")

    with tab3:
        st.subheader("Optimization Performance")

        # Mock performance data
        performance_data = pd.DataFrame({
            'Optimization': ['Keyword Boost', 'Format Fix', 'Content Enhancement'],
            'Improvement': [15, 8, 12]
        })

        fig = px.bar(performance_data, x='Optimization', y='Improvement',
                    title="ATS Score Improvements")
        st.plotly_chart(fig, use_container_width=True)

# Team Simulations
def show_team_simulations():
    st.header("📈 Team Simulations")

    tab1, tab2, tab3 = st.tabs(["🎲 Run Simulation", "📊 Results", "🔬 Analysis"])

    with tab1:
        st.subheader("Policy Simulation")

        simulation_type = st.selectbox(
            "Simulation Type",
            ["unemployment", "drug_abuse", "trafficking", "water_scarcity",
             "cape_town_unemployment", "cape_town_water_crisis"]
        )

        parameters = st.text_area("Simulation Parameters (JSON)", '{"policy_strength": 0.8}', height=100)

        if st.button("▶️ Run Simulation", type="primary"):
            with st.spinner("Running policy simulation..."):
                try:
                    params = json.loads(parameters)
                    sim_data = {
                        "name": "run_policy_simulation",
                        "arguments": {
                            "simulation_type": simulation_type,
                            "parameters": params,
                            "user_id": st.session_state.user_id
                        }
                    }

                    result = make_api_call("team_sim", "/mcp/tools/call", "POST", sim_data)

                    if "error" not in result:
                        st.success("✅ Simulation completed!")
                        st.info(f"Policy effectiveness: {result.get('content', [{}])[0].get('text', 'Unknown')}")
                        update_last_refresh()
                    else:
                        st.error(f"Simulation failed: {result['error']}")
                except json.JSONDecodeError:
                    st.error("Invalid JSON parameters")

    with tab2:
        st.subheader("Simulation Results")

        # Get recent simulations
        sim_results = make_api_call("team_sim", "/mcp/resources/mongodb://job_application_agent/simulations")

        if sim_results.get("content"):
            for sim in sim_results["content"][:3]:  # Show last 3
                with st.expander(f"Simulation: {sim.get('simulation_type', 'Unknown')}"):
                    st.json(sim)
        else:
            st.info("No simulation results found. Run your first simulation!")

    with tab3:
        st.subheader("Simulation Analysis")

        # Mock analysis charts
        col1, col2 = st.columns(2)

        with col1:
            # Policy effectiveness over time
            effectiveness_data = pd.DataFrame({
                'Time': range(1, 11),
                'Effectiveness': [0.2, 0.35, 0.48, 0.55, 0.62, 0.68, 0.72, 0.75, 0.77, 0.78]
            })
            fig = px.line(effectiveness_data, x='Time', y='Effectiveness',
                         title="Policy Effectiveness Over Time")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Scenario comparison
            scenario_data = pd.DataFrame({
                'Scenario': ['Current Policy', 'Proposed A', 'Proposed B', 'Proposed C'],
                'Effectiveness': [65, 78, 82, 75]
            })
            fig = px.bar(scenario_data, x='Scenario', y='Effectiveness',
                        title="Policy Scenario Comparison")
            st.plotly_chart(fig, use_container_width=True)

# Gamification Hub
def show_gamification_hub():
    st.header("🎮 Gamification Hub")

    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Dashboard", "🎯 Challenges", "🏅 Achievements", "🎁 Rewards"])

    with tab1:
        st.subheader("Your Gaming Progress")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Current Level", "12", "↗️ +2")
        with col2:
            st.metric("Total Tokens", "1,250", "↗️ +150")
        with col3:
            st.metric("Achievements", "8", "↗️ +1")
        with col4:
            st.metric("Rank", "#47", "↗️ +5")

        # Progress bars
        st.subheader("Level Progress")
        progress = st.progress(0.75)
        st.caption("750/1000 XP to next level")

        # Token balance
        st.subheader("Token Balance")
        token_col1, token_col2 = st.columns([3, 1])
        with token_col1:
            st.metric("Available Tokens", "1,250")
        with token_col2:
            if st.button("💰 Earn More"):
                st.info("Complete challenges to earn tokens!")

    with tab2:
        st.subheader("Active Challenges")

        challenges = [
            {"name": "Resume Master", "description": "Upload and optimize 5 resumes", "progress": 3, "total": 5, "reward": 100},
            {"name": "Job Hunter", "description": "Apply to 10 jobs this week", "progress": 7, "total": 10, "reward": 200},
            {"name": "Network Builder", "description": "Connect with 20 professionals", "progress": 12, "total": 20, "reward": 150}
        ]

        for challenge in challenges:
            with st.expander(f"🎯 {challenge['name']} - {challenge['reward']} tokens"):
                st.write(challenge['description'])
                progress = challenge['progress'] / challenge['total']
                st.progress(progress)
                st.caption(f"{challenge['progress']}/{challenge['total']} completed")

    with tab3:
        st.subheader("Achievements Unlocked")

        achievements = [
            {"name": "First Resume", "description": "Uploaded your first resume", "icon": "📄", "unlocked": True},
            {"name": "Job Seeker", "description": "Searched for 50 jobs", "icon": "🔍", "unlocked": True},
            {"name": "ATS Expert", "description": "Optimized 10 resumes", "icon": "🎯", "unlocked": False},
            {"name": "Interview Ready", "description": "Completed interview preparation", "icon": "💼", "unlocked": False}
        ]

        for achievement in achievements:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                st.write(achievement['icon'])
            with col2:
                st.write(f"**{achievement['name']}**")
                st.caption(achievement['description'])
            with col3:
                if achievement['unlocked']:
                    st.success("✅ Unlocked")
                else:
                    st.info("🔒 Locked")

    with tab4:
        st.subheader("Available Rewards")

        rewards = [
            {"name": "Premium Job Listings", "cost": 100, "description": "Access to exclusive job postings"},
            {"name": "Career Coaching Session", "cost": 200, "description": "1-on-1 career guidance"},
            {"name": "Resume Review", "cost": 150, "description": "Professional resume review"},
            {"name": "LinkedIn Optimization", "cost": 250, "description": "LinkedIn profile enhancement"}
        ]

        for reward in rewards:
            with st.expander(f"🎁 {reward['name']} - {reward['cost']} tokens"):
                st.write(reward['description'])
                if st.button(f"Redeem {reward['name']}", key=f"redeem_{reward['name']}"):
                    st.success(f"✅ {reward['name']} redeemed successfully!")

# Workflow Monitoring
def show_workflow_monitoring():
    st.header("📋 Workflow Monitoring")

    tab1, tab2, tab3 = st.tabs(["🔄 Active Workflows", "📊 Performance", "🚨 Error Logs"])

    with tab1:
        st.subheader("Active Workflows")

        # Mock active workflows
        workflows = [
            {"id": "wf_001", "name": "Software Engineer Search", "status": "Running", "progress": 65, "start_time": "10:30 AM"},
            {"id": "wf_002", "name": "Resume Optimization", "status": "Completed", "progress": 100, "start_time": "9:15 AM"},
            {"id": "wf_003", "name": "Job Application Batch", "status": "Queued", "progress": 0, "start_time": "Pending"}
        ]

        for workflow in workflows:
            with st.expander(f"🔄 {workflow['name']} - {workflow['status']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.progress(workflow['progress'] / 100)
                    st.caption(f"Started: {workflow['start_time']}")
                with col2:
                    if workflow['status'] == "Running":
                        st.info("⏸️ Pause")
                    elif workflow['status'] == "Queued":
                        st.success("▶️ Start")

    with tab2:
        st.subheader("Performance Metrics")

        col1, col2 = st.columns(2)

        with col1:
            # Response times
            response_data = pd.DataFrame({
                'Service': ['Resume Upload', 'Job Search', 'ATS Optimize', 'Core API'],
                'Avg Response (s)': [2.3, 1.8, 3.1, 1.2]
            })
            fig = px.bar(response_data, x='Service', y='Avg Response (s)',
                        title="Average Response Times")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Success rates
            success_data = pd.DataFrame({
                'Service': ['Resume Upload', 'Job Search', 'ATS Optimize', 'Core API'],
                'Success Rate (%)': [98, 95, 92, 99]
            })
            fig = px.bar(success_data, x='Service', y='Success Rate (%)',
                        title="Service Success Rates")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Error Logs")

        # Mock error logs
        errors = [
            {"time": "14:32", "service": "Job Search", "error": "API rate limit exceeded", "severity": "Warning"},
            {"time": "13:45", "service": "ATS Optimize", "error": "Resume parsing failed", "severity": "Error"},
            {"time": "12:18", "service": "Core API", "error": "Database connection timeout", "severity": "Critical"}
        ]

        for error in errors:
            severity_color = {"Warning": "🟡", "Error": "🔴", "Critical": "🔴"}
            with st.expander(f"{severity_color[error['severity']]} {error['time']} - {error['service']}"):
                st.write(f"**Error:** {error['error']}")
                st.caption(f"Severity: {error['severity']}")

# Settings
def show_settings():
    st.header("⚙️ Settings")

    tab1, tab2, tab3 = st.tabs(["🔧 API Configuration", "👤 User Preferences", "🔒 Privacy & Security"])

    with tab1:
        st.subheader("API Endpoints")

        for service, url in API_ENDPOINTS.items():
            st.text_input(f"{service.upper()} API URL", value=url, key=f"api_{service}")

        if st.button("Test Connections"):
            with st.spinner("Testing API connections..."):
                results = {}
                for service, url in API_ENDPOINTS.items():
                    try:
                        response = requests.get(f"{url}/health", timeout=5)
                        results[service] = "✅ Connected" if response.status_code == 200 else f"❌ Error {response.status_code}"
                    except:
                        results[service] = "❌ Connection Failed"

                for service, status in results.items():
                    st.write(f"**{service.upper()}:** {status}")

    with tab2:
        st.subheader("User Preferences")

        col1, col2 = st.columns(2)

        with col1:
            st.checkbox("Enable email notifications", value=True)
            st.checkbox("Auto-optimize resumes", value=True)
            st.checkbox("Enable gamification features", value=True)

        with col2:
            st.checkbox("Show advanced analytics", value=False)
            st.checkbox("Enable real-time updates", value=True)
            st.checkbox("Allow data sharing for improvements", value=False)

        st.subheader("Default Search Settings")
        st.text_input("Default location", "Cape Town")
        st.slider("Default job age limit", 1, 30, 7)

    with tab3:
        st.subheader("Privacy & Security")

        st.info("🔒 Your data is protected under POPIA compliance standards")

        st.subheader("Data Management")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📥 Export My Data"):
                st.info("Data export functionality would be implemented here")

        with col2:
            if st.button("🗑️ Delete My Data", type="secondary"):
                st.warning("This action cannot be undone!")
                if st.checkbox("I understand the consequences"):
                    st.error("Data deletion not implemented in demo")

        st.subheader("Privacy Settings")
        st.checkbox("Anonymize personal data in analytics", value=True)
        st.checkbox("Opt-out of improvement data collection", value=False)
def show_settings():
    st.header("⚙️ Settings")

    st.subheader("API Configuration")
    st.text_input("Core API URL", CORE_API)
    st.text_input("Resume API URL", RESUME_API)
    st.text_input("Job Search API URL", JOB_API)

    st.subheader("User Preferences")
    st.checkbox("Enable notifications", True)
    st.checkbox("Auto-optimize resumes", True)

if __name__ == "__main__":
    main()