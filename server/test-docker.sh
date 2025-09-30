#!/bin/bash

# Docker Setup Test Script for Kindle Home Display Server
# This script helps verify that the Docker setup is working correctly

set -e

echo "🚀 Testing Kindle Home Display Server Docker Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_status $RED "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

print_status $GREEN "✅ Docker is running"

# Check if required files exist
required_files=("config.toml" "api_keys.json")
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        print_status $YELLOW "⚠️  Required file '$file' not found. You can use the template files."
        if [[ "$file" == "config.toml" && -f "config.docker.toml" ]]; then
            print_status $YELLOW "   Run: cp config.docker.toml config.toml"
        fi
    else
        print_status $GREEN "✅ Found $file"
    fi
done

# Build the Docker image
print_status $YELLOW "🔨 Building Docker image..."
if docker compose build; then
    print_status $GREEN "✅ Docker image built successfully"
else
    print_status $RED "❌ Failed to build Docker image"
    exit 1
fi

# Start the services
print_status $YELLOW "🚀 Starting Docker services..."
if docker compose up -d; then
    print_status $GREEN "✅ Docker services started"
else
    print_status $RED "❌ Failed to start Docker services"
    exit 1
fi

# Wait for the service to be ready
print_status $YELLOW "⏳ Waiting for service to be ready..."
sleep 10

# Test health endpoint
print_status $YELLOW "🏥 Testing health endpoint..."
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    print_status $GREEN "✅ Health check passed"
    echo "   Response: $(curl -s http://localhost:8000/health)"
else
    print_status $RED "❌ Health check failed"
    print_status $YELLOW "📋 Service logs:"
    docker compose logs --tail=20 server
fi

# Test main endpoint
print_status $YELLOW "🌐 Testing main endpoint..."
if curl -f http://localhost:8000/ >/dev/null 2>&1; then
    print_status $GREEN "✅ Main endpoint accessible"
else
    print_status $YELLOW "⚠️  Main endpoint test failed (this might be normal if configuration is incomplete)"
fi

# Show running containers
print_status $YELLOW "📋 Running containers:"
docker compose ps

echo ""
print_status $GREEN "🎉 Docker setup test completed!"
echo ""
echo "Next steps:"
echo "- Visit http://localhost:8000 to see the server"
echo "- Visit http://localhost:8000/dashboard to see the dashboard image"
echo "- Visit http://localhost:8000/docs to see the API documentation"
echo "- Run 'docker compose logs -f server' to view live logs"
echo "- Run 'docker compose down' to stop the services"
echo ""
echo "For development with hot reload:"
echo "- Run 'docker compose --profile dev up server-dev'"
echo "- Development server will be available at http://localhost:8001"