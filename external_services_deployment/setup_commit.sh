#!/bin/bash

# Script to stage, commit, and push files for Issue #1

echo "Staging all files..."
git add .

echo "Committing with message: Closes #1 - Set up project structure and .env for APIs"
git commit -m "Closes #1 - Set up project structure and .env for APIs"

echo "Pushing to remote repository..."
git push

echo "Commit and push completed successfully."