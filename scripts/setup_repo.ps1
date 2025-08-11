# Prompt Stacker - GitHub Repository Setup Script (PowerShell)
# This script helps set up the GitHub repository for the project

param(
    [string]$GitHubUsername = ""
)

Write-Host "🚀 Setting up Prompt Stacker GitHub repository..." -ForegroundColor Green

# Check if git is installed
try {
    git --version | Out-Null
} catch {
    Write-Host "❌ Git is not installed. Please install Git first." -ForegroundColor Red
    exit 1
}

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "📁 Initializing git repository..." -ForegroundColor Yellow
    git init
}

# Add all files
Write-Host "📝 Adding files to git..." -ForegroundColor Yellow
git add .

# Create initial commit
Write-Host "💾 Creating initial commit..." -ForegroundColor Yellow
$commitMessage = @"
feat: Initial commit - Prompt Stacker automation system

- Add core automation engine with optimized timing
- Implement beautiful Monokai-themed UI
- Add coordinate capture system
- Include process visualization with emoji indicators
- Add get ready pause functionality
- Implement comprehensive error handling
- Add production-ready logging
- Include complete documentation and setup files
"@

git commit -m $commitMessage

# Create main branch if not exists
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    Write-Host "🌿 Creating main branch..." -ForegroundColor Yellow
    git branch -M main
}

Write-Host "✅ Repository setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Create a new repository on GitHub named 'prompt-stacker'"
Write-Host "2. Run the following commands:"

if ($GitHubUsername) {
    Write-Host "   git remote add origin https://github.com/$GitHubUsername/prompt-stacker.git" -ForegroundColor White
} else {
    Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/prompt-stacker.git" -ForegroundColor White
}

Write-Host "   git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Optional: Set up development environment" -ForegroundColor Cyan
Write-Host "   pip install -r requirements-dev.txt" -ForegroundColor White
Write-Host "   pre-commit install" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Your Prompt Stacker project is ready for GitHub!" -ForegroundColor Green
