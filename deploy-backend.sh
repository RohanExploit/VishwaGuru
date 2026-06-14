#!/bin/bash
# VishwaGuru Backend Deployment Script
# This script helps deploy the backend to Render

echo "🚀 VishwaGuru Backend Deployment Script"
echo "========================================"

# Check if required tools are installed
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed. Aborting."; exit 1; }
command -v pip >/dev/null 2>&1 || { echo "❌ pip is required but not installed. Aborting."; exit 1; }

echo "✅ Python and pip are available"

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ backend/main.py not found. Please run this script from the project root directory."
    exit 1
fi

echo "✅ Project structure looks correct"

# Install dependencies locally to check for issues
echo "📦 Installing dependencies..."
cd backend
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies. Please check requirements.txt"
    exit 1
fi
echo "✅ Dependencies installed successfully"

# Test import
echo "🧪 Testing backend import..."
cd ..
PYTHONPATH=backend python3 -c "import backend.main; print('✅ Backend imports successfully')"
if [ $? -ne 0 ]; then
    echo "❌ Backend import failed. Please check the error messages above."
    exit 1
fi

echo ""
echo "🎉 Backend validation completed successfully!"
echo ""
echo "📋 Next steps for deployment:"
echo "1. Create a Render account at https://render.com"
echo "2. Connect your GitHub repository"
echo "3. Use the render.yaml file in the project root for configuration"
echo "4. Set the following environment variables in Render dashboard:"
echo "   - GEMINI_API_KEY: Your Google Gemini API key"
echo "   - TELEGRAM_BOT_TOKEN: Your Telegram bot token"
echo "   - FRONTEND_URL: Your Netlify frontend URL (e.g., https://your-app.netlify.app)"
echo "   - DATABASE_URL: Your PostgreSQL database URL (use Neon, Supabase, etc.)"
echo "   - CORS_ORIGINS: Your frontend URL"
echo ""
echo "5. Deploy and test the API endpoints"
echo ""
echo "📖 For detailed deployment instructions, see DEPLOYMENT_GUIDE.md"