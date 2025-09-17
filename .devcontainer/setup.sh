#!/bin/bash
# Configure Git to avoid prompts
git config --global user.name "Dev Container"
git config --global user.email "dev@container.com"
git config --global pull.rebase false
git config --global merge.conflictstyle diff3

# Ensure repo is up-to-date
git pull origin main

# Install dependencies
pip install -r requirements.txt