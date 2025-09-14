#!/bin/bash

echo "Staging all files for Issue #2..."
git add .

echo "Committing with message: Closes #2 - Implement multi-user Gmail OAuth"
git commit -m "Closes #2 - Implement multi-user Gmail OAuth"

echo "Pushing to remote repository..."
git push

echo "Commit and push completed successfully."