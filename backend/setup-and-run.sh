#!/bin/bash

# MedEx Backend - Automated Setup Script
# This script sets up and runs the backend locally

set -e  # Exit on error

echo "=================================="
echo "MedEx Backend Setup & Runner"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKEND_DIR"

# Check Python version
echo -e "${BLUE}[1/5] Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check MongoDB
echo -e "${BLUE}[2/5] Checking MongoDB...${NC}"
if command -v docker &> /dev/null; then
    # Check if MongoDB container is running
    if docker ps | grep -q mongo; then
        echo -e "${GREEN}✓ MongoDB container is running${NC}"
    else
        echo -e "${YELLOW}⚠ MongoDB not running. Starting Docker container...${NC}"
        docker run -d -p 27017:27017 --name medex-mongo mongo:latest || {
            echo -e "${YELLOW}⚠ Could not start MongoDB. Please ensure Docker is running.${NC}"
            echo "   Start MongoDB manually: docker run -d -p 27017:27017 mongo"
        }
    fi
else
    echo -e "${YELLOW}⚠ Docker not found. Make sure MongoDB is running on localhost:27017${NC}"
fi

# Create/update virtual environment
echo -e "${BLUE}[3/5] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating new virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade requirements
echo -e "${BLUE}[4/5] Installing/updating dependencies...${NC}"
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check .env file
echo -e "${BLUE}[5/5] Checking configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env created. Update with your API keys if needed.${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Create uploads directory
mkdir -p uploads
echo -e "${GREEN}✓ Uploads directory ready${NC}"

echo ""
echo "=================================="
echo -e "${GREEN}✓ Setup complete!${NC}"
echo "=================================="
echo ""
echo "Starting FastAPI backend..."
echo ""
echo "📍 Server will run at:"
echo -e "${BLUE}   http://localhost:8000${NC}"
echo ""
echo "📚 API Documentation (Swagger):"
echo -e "${BLUE}   http://localhost:8000/docs${NC}"
echo ""
echo "🚀 Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn server:app --reload --host 0.0.0.0 --port 8000
