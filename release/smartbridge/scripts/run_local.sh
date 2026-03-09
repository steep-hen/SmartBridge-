#!/bin/bash
# Local development launcher script
# Activates virtual environment and starts both backend and frontend services
# 
# Usage:
#   chmod +x scripts/run_local.sh
#   ./scripts/run_local.sh
#
# This script assumes:
#   - Python 3.10+ is installed
#   - docker and docker-compose are available
#   - .env file exists in the project root
#
# It will:
#   1. Create virtual environment if it doesn't exist
#   2. Activate virtual environment
#   3. Install dependencies
#   4. Start PostgreSQL via docker-compose
#   5. Start FastAPI backend with uvicorn
#   6. Start Streamlit frontend

set -e  # Exit on error

echo "=========================================="
echo "AI Financial Advisor - Local Dev Launcher"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR=".venv"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}Project Root: ${PROJECT_ROOT}${NC}"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "$PROJECT_ROOT/$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$PROJECT_ROOT/$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

echo ""

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$PROJECT_ROOT/$VENV_DIR/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"

echo ""

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r "$PROJECT_ROOT/requirements.txt"
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""

# Create .env if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    echo -e "${GREEN}✓ .env file created (update with your values)${NC}"
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

echo ""
echo "=========================================="
echo "Starting Services"
echo "=========================================="
echo ""

# Start Docker Compose services
echo -e "${YELLOW}Starting PostgreSQL and dependencies...${NC}"
cd "$PROJECT_ROOT"
docker-compose up -d --build
echo -e "${GREEN}✓ PostgreSQL is starting${NC}"

# Wait for database to be ready
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
sleep 5

echo ""
echo "=========================================="
echo -e "${GREEN}Services are starting!${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}Backend API:${NC}"
echo -e "  URL:  http://localhost:8000"
echo -e "  Docs: http://localhost:8000/docs"
echo -e "  ReDoc: http://localhost:8000/redoc"
echo ""
echo -e "${BLUE}Note:${NC} Backend is running in docker-compose"
echo "To run backend locally with hot-reload instead:"
echo -e "  ${GREEN}uvicorn backend.main:app --reload${NC}"
echo ""
echo -e "${BLUE}Frontend (Streamlit):${NC}"
echo -e "  ${YELLOW}Open another terminal and run:${NC}"
echo -e "  ${GREEN}streamlit run frontend/streamlit_app.py${NC}"
echo ""
echo -e "${BLUE}Run Tests:${NC}"
echo -e "  ${GREEN}pytest tests/ -v${NC}"
echo ""
echo -e "${BLUE}Check Backend Health:${NC}"
echo -e "  ${GREEN}curl http://localhost:8000/health${NC}"
echo ""
echo -e "${BLUE}View Logs:${NC}"
echo -e "  ${GREEN}docker-compose logs -f backend${NC}"
echo ""
echo -e "${BLUE}Stop Services:${NC}"
echo -e "  ${GREEN}docker-compose down${NC}"
echo ""

# Optional: Start backend in background if needed
# echo -e "${YELLOW}Starting FastAPI backend...${NC}"
# uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
# BACKEND_PID=$!
# echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# Optional: Start Streamlit frontend
# echo -e "${YELLOW}Starting Streamlit frontend...${NC}"
# streamlit run frontend/streamlit_app.py &
# FRONTEND_PID=$!
# echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

echo -e "${GREEN}Setup complete!${NC}"
echo ""
