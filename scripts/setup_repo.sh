#!/bin/bash

# Prompt Stacker - GitHub Repository Setup Script
# This script helps set up the GitHub repository for the project

set -e

echo "🚀 Setting up Prompt Stacker GitHub repository..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
fi

# Add all files
echo "📝 Adding files to git..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "feat: Initial commit - Prompt Stacker automation system

- Add core automation engine with optimized timing
- Implement beautiful Monokai-themed UI
- Add coordinate capture system
- Include process visualization with emoji indicators
- Add get ready pause functionality
- Implement comprehensive error handling
- Add production-ready logging
- Include complete documentation and setup files"

# Create main branch if not exists
if ! git branch --list | grep -q "main"; then
    echo "🌿 Creating main branch..."
    git branch -M main
fi

echo "✅ Repository setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Create a new repository on GitHub named 'prompt-stacker'"
echo "2. Run the following commands:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/prompt-stacker.git"
echo "   git push -u origin main"
echo ""
echo "🔧 Optional: Set up development environment"
echo "   pip install -r requirements-dev.txt"
echo "   pre-commit install"
echo ""
echo "🎉 Your Prompt Stacker project is ready for GitHub!"
