#!/bin/bash

# Company Research Platform Deployment Script
# Supports Render and Railway deployment

set -e

echo "🚀 Company Research Platform Deployment"
echo "========================================"

# Check if environment variables are set
check_env_vars() {
    echo "📋 Checking environment variables..."
    
    required_vars=(
        "ASTRA_DB_TOKEN"
        "ASTRA_DB_ENDPOINT" 
        "LANGFLOW_API_KEY"
        "LANGFLOW_FLOW_URL"
        "EXA_API_KEY"
        "TAVILY_API_KEY"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo "❌ Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "   - $var"
        done
        echo ""
        echo "Please set these variables and try again."
        echo "Example:"
        echo "export ASTRA_DB_TOKEN='your_token_here'"
        exit 1
    fi
    
    echo "✅ All environment variables are set"
}

# Test backend locally
test_backend() {
    echo "🧪 Testing backend..."
    
    cd backend
    
    # Install dependencies
    echo "📦 Installing backend dependencies..."
    pip install -r requirements.txt
    
    # Start backend in background
    echo "🔄 Starting backend..."
    python main.py &
    BACKEND_PID=$!
    
    # Wait for backend to start
    sleep 5
    
    # Test health endpoint
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
    else
        echo "❌ Backend health check failed"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    
    # Stop backend
    kill $BACKEND_PID 2>/dev/null || true
    cd ..
}

# Test frontend locally
test_frontend() {
    echo "🧪 Testing frontend..."
    
    cd frontend
    
    # Install dependencies
    echo "📦 Installing frontend dependencies..."
    npm install
    
    # Build frontend
    echo "🔨 Building frontend..."
    npm run build
    
    if [ $? -eq 0 ]; then
        echo "✅ Frontend build successful"
    else
        echo "❌ Frontend build failed"
        exit 1
    fi
    
    cd ..
}

# Deploy to Render
deploy_render() {
    echo "🌐 Deploying to Render..."
    
    # Check if render.yaml exists
    if [ ! -f "render.yaml" ]; then
        echo "❌ render.yaml not found"
        exit 1
    fi
    
    echo "📋 Render deployment checklist:"
    echo "1. Push your code to GitHub"
    echo "2. Connect your GitHub repo to Render"
    echo "3. Create a new Web Service"
    echo "4. Use the render.yaml configuration"
    echo "5. Set environment variables in Render dashboard:"
    
    required_vars=(
        "ASTRA_DB_TOKEN"
        "ASTRA_DB_ENDPOINT" 
        "LANGFLOW_API_KEY"
        "LANGFLOW_FLOW_URL"
        "EXA_API_KEY"
        "TAVILY_API_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        echo "   - $var"
    done
    
    echo ""
    echo "6. Deploy!"
    echo ""
    echo "Your app will be available at: https://your-app-name.onrender.com"
}

# Deploy to Railway
deploy_railway() {
    echo "🚂 Deploying to Railway..."
    
    # Check if Railway CLI is installed
    if ! command -v railway &> /dev/null; then
        echo "📦 Installing Railway CLI..."
        npm install -g @railway/cli
    fi
    
    echo "🔐 Logging into Railway..."
    railway login
    
    echo "🚀 Initializing Railway project..."
    railway init
    
    echo "📤 Deploying to Railway..."
    railway up
    
    echo "✅ Deployment complete!"
    echo "Your app will be available at the URL provided by Railway"
}

# Main deployment function
deploy() {
    platform=$1
    
    case $platform in
        "render")
            deploy_render
            ;;
        "railway")
            deploy_railway
            ;;
        *)
            echo "❌ Unknown platform: $platform"
            echo "Supported platforms: render, railway"
            exit 1
            ;;
    esac
}

# Show usage
show_usage() {
    echo "Usage: $0 [command] [platform]"
    echo ""
    echo "Commands:"
    echo "  check     - Check environment variables"
    echo "  test      - Test backend and frontend locally"
    echo "  deploy    - Deploy to specified platform"
    echo ""
    echo "Platforms:"
    echo "  render    - Deploy to Render"
    echo "  railway   - Deploy to Railway"
    echo ""
    echo "Examples:"
    echo "  $0 check"
    echo "  $0 test"
    echo "  $0 deploy render"
    echo "  $0 deploy railway"
}

# Main script logic
case $1 in
    "check")
        check_env_vars
        ;;
    "test")
        check_env_vars
        test_backend
        test_frontend
        echo "🎉 All tests passed! Ready for deployment."
        ;;
    "deploy")
        if [ -z "$2" ]; then
            echo "❌ Please specify a platform"
            show_usage
            exit 1
        fi
        check_env_vars
        deploy $2
        ;;
    *)
        show_usage
        ;;
esac
