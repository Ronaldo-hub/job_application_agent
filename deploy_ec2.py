"""
AWS EC2 Deployment Script for Job Application Agent

This script automates the deployment of the Job Application Agent to AWS EC2 free tier,
including Docker containerization, environment setup, and Colab integration.
"""

import os
import json
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EC2Deployer:
    """Handles AWS EC2 deployment for the Job Application Agent."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.ec2_instance_id = os.getenv('AWS_EC2_INSTANCE_ID')
        self.ec2_region = os.getenv('AWS_REGION', 'af-south-1')  # Cape Town region
        self.key_pair_name = os.getenv('AWS_KEY_PAIR_NAME', 'job-agent-key')
        self.security_group_name = 'job-agent-sg'

        # Docker configuration
        self.docker_image_name = 'job-application-agent'
        self.docker_container_name = 'job-agent-container'

    def create_dockerfile(self):
        """Create optimized Dockerfile for EC2 deployment."""
        dockerfile_content = '''# Use Python 3.9 slim image for smaller size
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    libffi-dev \\
    libssl-dev \\
    curl \\
    mongodb-clients \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "discord_bot.py"]
'''

        dockerfile_path = self.project_root / 'Dockerfile'
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        logger.info("Dockerfile created successfully")
        return dockerfile_path

    def create_docker_compose(self):
        """Create docker-compose.yml for local development and deployment."""
        compose_content = '''version: '3.8'

services:
  job-agent:
    build: .
    container_name: job-agent-container
    ports:
      - "8000:8000"
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
      - HUGGINGFACE_API_KEY=${HUGGINGFACE_API_KEY}
      - MONGODB_URI=${MONGODB_URI}
      - DATA_ENCRYPTION_KEY=${DATA_ENCRYPTION_KEY}
      - AWS_REGION=${AWS_REGION}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  mongodb:
    image: mongo:5.0
    container_name: job-agent-mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init:/docker-entrypoint-initdb.d
    restart: unless-stopped

volumes:
  mongodb_data:

networks:
  default:
    name: job-agent-network
'''

        compose_path = self.project_root / 'docker-compose.yml'
        with open(compose_path, 'w') as f:
            f.write(compose_content)

        logger.info("docker-compose.yml created successfully")
        return compose_path

    def create_nginx_config(self):
        """Create Nginx configuration for reverse proxy."""
        nginx_content = '''server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
}
'''

        nginx_path = self.project_root / 'nginx.conf'
        with open(nginx_path, 'w') as f:
            f.write(nginx_content)

        logger.info("Nginx configuration created")
        return nginx_path

    def create_systemd_service(self):
        """Create systemd service file for auto-start."""
        service_content = '''[Unit]
Description=Job Application Agent Discord Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/job-application-agent
ExecStart=/usr/bin/python3 /home/ec2-user/job-application-agent/discord_bot.py
Restart=always
RestartSec=10

# Environment variables
Environment=PATH=/usr/bin:/bin
EnvironmentFile=-/home/ec2-user/job-application-agent/.env

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=job-agent

[Install]
WantedBy=multi-user.target
'''

        service_path = self.project_root / 'job-agent.service'
        with open(service_path, 'w') as f:
            f.write(service_content)

        logger.info("Systemd service file created")
        return service_path

    def create_deployment_script(self):
        """Create deployment script for EC2."""
        deploy_script = '''#!/bin/bash

# Job Application Agent EC2 Deployment Script
# This script sets up the application on AWS EC2 free tier

set -e

echo "🚀 Starting Job Application Agent deployment..."

# Update system
echo "📦 Updating system packages..."
sudo yum update -y

# Install required packages
echo "🔧 Installing dependencies..."
sudo yum install -y python3 python3-pip git curl wget

# Install Docker
echo "🐳 Installing Docker..."
sudo amazon-linux-extras install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install MongoDB
echo "🍃 Installing MongoDB..."
sudo tee /etc/yum.repos.d/mongodb-org-5.0.repo > /dev/null <<EOF
[mongodb-org-5.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2/mongodb-org/5.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-5.0.asc
EOF

sudo yum install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# Clone repository
echo "📥 Cloning repository..."
cd /home/ec2-user
git clone https://github.com/Ronaldo-hub/job_application_agent.git
cd job-application-agent

# Set up environment
echo "⚙️ Setting up environment..."
cp .env.example .env
# Note: You need to manually add your API keys to .env

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt
python3 -m spacy download en_core_web_sm

# Set up logging directory
mkdir -p logs

# Create systemd service
echo "🔄 Setting up systemd service..."
sudo cp job-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable job-agent

# Start the service
echo "▶️ Starting Job Application Agent..."
sudo systemctl start job-agent

# Set up monitoring
echo "📊 Setting up monitoring..."
curl -s https://raw.githubusercontent.com/Ronaldo-hub/job_application_agent/main/monitoring/install_monitoring.sh | bash

echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit /home/ec2-user/job-application-agent/.env with your API keys"
echo "2. Restart the service: sudo systemctl restart job-agent"
echo "3. Check logs: sudo journalctl -u job-agent -f"
echo "4. Test the bot in your Discord server"
echo ""
echo "🔗 Useful commands:"
echo "• Status: sudo systemctl status job-agent"
echo "• Logs: sudo journalctl -u job-agent -f"
echo "• Restart: sudo systemctl restart job-agent"
echo "• Stop: sudo systemctl stop job-agent"
'''

        script_path = self.project_root / 'deploy_ec2.sh'
        with open(script_path, 'w') as f:
            f.write(deploy_script)

        # Make script executable
        script_path.chmod(0o755)

        logger.info("EC2 deployment script created")
        return script_path

    def create_monitoring_setup(self):
        """Create monitoring and health check scripts."""
        monitoring_script = '''#!/bin/bash

# Job Application Agent Monitoring Script
# Checks system health and sends alerts if needed

#!/bin/bash

# Check if Discord bot is running
check_discord_bot() {
    if pgrep -f "discord_bot.py" > /dev/null; then
        echo "✅ Discord bot is running"
        return 0
    else
        echo "❌ Discord bot is not running"
        return 1
    fi
}

# Check MongoDB connection
check_mongodb() {
    if pgrep -f "mongod" > /dev/null; then
        echo "✅ MongoDB is running"
        return 0
    else
        echo "❌ MongoDB is not running"
        return 1
    fi
}

# Check system resources
check_resources() {
    # Check CPU usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\\1/" | awk '{print 100 - $1}')
    if (( $(echo "$cpu_usage < 80" | bc -l) )); then
        echo "✅ CPU usage: ${cpu_usage}%"
    else
        echo "⚠️ High CPU usage: ${cpu_usage}%"
    fi

    # Check memory usage
    mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ $mem_usage -lt 80 ]; then
        echo "✅ Memory usage: ${mem_usage}%"
    else
        echo "⚠️ High memory usage: ${mem_usage}%"
    fi

    # Check disk usage
    disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $disk_usage -lt 80 ]; then
        echo "✅ Disk usage: ${disk_usage}%"
    else
        echo "⚠️ High disk usage: ${disk_usage}%"
    fi
}

# Check application health
check_application_health() {
    # Check if port 8000 is listening
    if netstat -tuln | grep :8000 > /dev/null; then
        echo "✅ Application port 8000 is listening"
    else
        echo "❌ Application port 8000 is not listening"
    fi

    # Try to connect to health endpoint
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Health check passed"
    else
        echo "❌ Health check failed"
    fi
}

# Main monitoring function
main() {
    echo "🔍 Job Application Agent Health Check"
    echo "====================================="
    echo "Timestamp: $(date)"
    echo ""

    check_discord_bot
    echo ""
    check_mongodb
    echo ""
    check_resources
    echo ""
    check_application_health
    echo ""

    echo "====================================="
}

# Run main function
main
'''

        monitoring_path = self.project_root / 'monitoring' / 'health_check.sh'
        monitoring_path.parent.mkdir(exist_ok=True)

        with open(monitoring_path, 'w') as f:
            f.write(monitoring_script)

        monitoring_path.chmod(0o755)

        logger.info("Monitoring setup created")
        return monitoring_path

    def create_backup_script(self):
        """Create automated backup script for MongoDB."""
        backup_script = '''#!/bin/bash

# MongoDB Backup Script for Job Application Agent
# Creates daily backups of the database

BACKUP_DIR="/home/ec2-user/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="job_agent_backup_$DATE"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

echo "📦 Creating MongoDB backup: $BACKUP_NAME"

# Create backup using mongodump
mongodump --db job_agent --out $BACKUP_DIR/$BACKUP_NAME

# Compress the backup
tar -czf $BACKUP_DIR/${BACKUP_NAME}.tar.gz -C $BACKUP_DIR $BACKUP_NAME

# Remove uncompressed backup
rm -rf $BACKUP_DIR/$BACKUP_NAME

# Keep only last 7 days of backups
find $BACKUP_DIR -name "job_agent_backup_*.tar.gz" -mtime +7 -delete

echo "✅ Backup completed: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"

# Optional: Upload to S3
# aws s3 cp $BACKUP_DIR/${BACKUP_NAME}.tar.gz s3://your-backup-bucket/
'''

        backup_path = self.project_root / 'backup_mongodb.sh'
        with open(backup_path, 'w') as f:
            f.write(backup_script)

        backup_path.chmod(0o755)

        logger.info("Backup script created")
        return backup_path

    def create_cloudformation_template(self):
        """Create AWS CloudFormation template for infrastructure as code."""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Job Application Agent Infrastructure",
            "Parameters": {
                "InstanceType": {
                    "Type": "String",
                    "Default": "t2.micro",
                    "AllowedValues": ["t2.micro", "t2.small", "t2.medium"],
                    "Description": "EC2 instance type"
                },
                "KeyName": {
                    "Type": "AWS::EC2::KeyPair::KeyName",
                    "Description": "Name of an existing EC2 KeyPair"
                }
            },
            "Resources": {
                "JobAgentSecurityGroup": {
                    "Type": "AWS::EC2::SecurityGroup",
                    "Properties": {
                        "GroupDescription": "Security group for Job Application Agent",
                        "SecurityGroupIngress": [
                            {
                                "IpProtocol": "tcp",
                                "FromPort": 22,
                                "ToPort": 22,
                                "CidrIp": "0.0.0.0/0",
                                "Description": "SSH access"
                            },
                            {
                                "IpProtocol": "tcp",
                                "FromPort": 80,
                                "ToPort": 80,
                                "CidrIp": "0.0.0.0/0",
                                "Description": "HTTP access"
                            }
                        ]
                    }
                },
                "JobAgentInstance": {
                    "Type": "AWS::EC2::Instance",
                    "Properties": {
                        "InstanceType": {"Ref": "InstanceType"},
                        "KeyName": {"Ref": "KeyName"},
                        "ImageId": "ami-0c1c3621b2b4b1b1b",  # Amazon Linux 2 AMI
                        "SecurityGroups": [{"Ref": "JobAgentSecurityGroup"}],
                        "Tags": [
                            {
                                "Key": "Name",
                                "Value": "Job-Application-Agent"
                            },
                            {
                                "Key": "Environment",
                                "Value": "Production"
                            }
                        ],
                        "UserData": {
                            "Fn::Base64": {
                                "Fn::Sub": """#!/bin/bash
yum update -y
yum install -y python3 python3-pip git curl wget
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user
"""
                            }
                        }
                    }
                }
            },
            "Outputs": {
                "InstanceId": {
                    "Description": "Instance ID of the EC2 instance",
                    "Value": {"Ref": "JobAgentInstance"},
                    "Export": {
                        "Name": {"Fn::Sub": "${AWS::StackName}-InstanceId"}
                    }
                },
                "PublicIP": {
                    "Description": "Public IP address of the EC2 instance",
                    "Value": {"Fn::GetAtt": ["JobAgentInstance", "PublicIp"]},
                    "Export": {
                        "Name": {"Fn::Sub": "${AWS::StackName}-PublicIP"}
                    }
                }
            }
        }

        template_path = self.project_root / 'cloudformation_template.json'
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)

        logger.info("CloudFormation template created")
        return template_path

    def deploy_to_ec2(self):
        """Execute full deployment to EC2."""
        try:
            logger.info("Starting EC2 deployment...")

            # Create all deployment files
            self.create_dockerfile()
            self.create_docker_compose()
            self.create_nginx_config()
            self.create_systemd_service()
            self.create_deployment_script()
            self.create_monitoring_setup()
            self.create_backup_script()
            self.create_cloudformation_template()

            logger.info("All deployment files created successfully")
            logger.info("Run './deploy_ec2.sh' on your EC2 instance to complete deployment")

            return True

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

def main():
    """Main deployment function."""
    deployer = EC2Deployer()

    print("🚀 Job Application Agent EC2 Deployment")
    print("=" * 50)

    success = deployer.deploy_to_ec2()

    if success:
        print("✅ Deployment files created successfully!")
        print("\n📋 Next steps:")
        print("1. Launch EC2 instance in AWS Console")
        print("2. SSH into instance: ssh -i your-key.pem ec2-user@your-instance")
        print("3. Run deployment: ./deploy_ec2.sh")
        print("4. Configure .env file with your API keys")
        print("5. Start the service: sudo systemctl start job-agent")
        print("\n🔗 Useful commands:")
        print("• Check status: sudo systemctl status job-agent")
        print("• View logs: sudo journalctl -u job-agent -f")
        print("• Health check: ./monitoring/health_check.sh")
    else:
        print("❌ Deployment failed!")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())