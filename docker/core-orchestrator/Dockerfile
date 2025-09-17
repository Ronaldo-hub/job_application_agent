FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent_core/ ./agent_core/
COPY compliance_monitoring_testing/ ./compliance_monitoring_testing/
COPY email_comm_hub/ ./email_comm_hub/
COPY resume_doc_processing/ ./resume_doc_processing/
COPY job_discovery_matching/ ./job_discovery_matching/
COPY learning_recommendations/ ./learning_recommendations/
COPY gamification_engine/ ./gamification_engine/
COPY external_services_deployment/ ./external_services_deployment/
COPY mesa_abm_simulations.py .
COPY cape_town_data.py .
COPY documentation_api.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "agent_core.main"]