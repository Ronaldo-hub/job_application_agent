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
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY email_comm_hub/ ./email_comm_hub/
COPY agent_core/ ./agent_core/
COPY job_discovery_matching/ ./job_discovery_matching/
COPY resume_doc_processing/ ./resume_doc_processing/
COPY learning_recommendations/ ./learning_recommendations/
COPY gamification_engine/ ./gamification_engine/
COPY compliance_monitoring_testing/ ./compliance_monitoring_testing/
COPY mesa_abm_simulations.py .
COPY cape_town_data.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import discord; print('Discord bot service healthy')" || exit 1

# Run the application
CMD ["python", "-m", "email_comm_hub.discord_bot"]