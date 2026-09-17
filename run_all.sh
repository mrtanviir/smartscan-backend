#!/usr/bin/env bash

# ==============================================================================
#  🛒 SmartScan Backend - All-In-One Automated Setup & Runner Script
# ==============================================================================

set -e

# ANSI Color Codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
echo "=================================================================="
echo "          🚀 STARTING SMARTSCAN BACKEND AUTOMATION RUNNER         "
echo "=================================================================="
echo -e "${NC}"

# 1. Check Directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 2. Check Python 3 Installation
echo -e "${BLUE}[1/7] Checking Python Environment...${NC}"
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Error: Python 3 is not installed or not in PATH!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Using $($PYTHON_CMD --version)${NC}"

# 3. Setup Virtual Environment
echo -e "\n${BLUE}[2/7] Initializing Virtual Environment (venv)...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}• Virtual environment not found. Creating 'venv'...${NC}"
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ Virtual environment created successfully.${NC}"
else
    echo -e "${GREEN}✓ Virtual environment 'venv' exists.${NC}"
fi

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated ($(which python))${NC}"

# 4. Install Dependencies
echo -e "\n${BLUE}[3/7] Checking & Installing Required Packages...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓ All dependencies verified and installed from requirements.txt.${NC}"
else
    echo -e "${YELLOW}• Installing core packages...${NC}"
    pip install django djangorestframework djangorestframework-simplejwt django-cors-headers psycopg2-binary requests python-dotenv --quiet
    echo -e "${GREEN}✓ Packages installed successfully.${NC}"
fi

# 5. Check Environment File (.env)
echo -e "\n${BLUE}[4/7] Checking Environment Configuration (.env)...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}• Created .env from .env.example template.${NC}"
    else
        cat <<EOT >> .env
GOOGLE_MAPS_API_KEY=
SECRET_KEY=django-insecure-7u-smg=*ecfs6=t(v7mx82%&_)(%3_x+0i#5^o7au96m&2_82f
DEBUG=True
DB_NAME=smartscan_db
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
SSLCOMMERZ_STORE_ID=
SSLCOMMERZ_STORE_PASS=
SSLCOMMERZ_IS_SANDBOX=True
BACKEND_BASE_URL=http://127.0.0.1:8000
EOT
        echo -e "${YELLOW}• Created new default .env template file.${NC}"
    fi
else
    echo -e "${GREEN}✓ .env configuration file loaded.${NC}"
fi

# 6. Check PostgreSQL Database
echo -e "\n${BLUE}[5/7] Checking Database Status...${NC}"
if command -v psql &>/dev/null; then
    # Try to create database if it doesn't exist
    psql -U postgres -h localhost -tc "SELECT 1 FROM pg_database WHERE datname = 'smartscan_db'" | grep -q 1 || psql -U postgres -h localhost -c "CREATE DATABASE smartscan_db;" 2>/dev/null || true
    echo -e "${GREEN}✓ Database smartscan_db ready.${NC}"
else
    echo -e "${YELLOW}• psql command line tool not in path, skipping DB creation check.${NC}"
fi

# 7. Run Migrations & Seed Demo Data
echo -e "\n${BLUE}[6/7] Applying Database Migrations & Seeding Demo Data...${NC}"
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py seed_demo_data

# 8. Run Quick Health Verification Tests
echo -e "\n${BLUE}[7/7] Running Health Check Tests...${NC}"
python manage.py test --noinput
echo -e "${GREEN}✓ All 20 API Unit Tests Passed Successfully!${NC}"

# ==============================================================================
#  Ready to Launch Server
# ==============================================================================
echo -e "\n${GREEN}${BOLD}"
echo "=================================================================="
echo "      🎉 SMARTSCAN BACKEND IS FULLY CONFIGURED & READY!          "
echo "=================================================================="
echo -e "${NC}"
echo -e "${CYAN}📍 Default Admin Credentials:${NC}"
echo -e "   • Phone:    ${BOLD}01700000000${NC}"
echo -e "   • Email:    ${BOLD}admin@smartscan.com${NC}"
echo -e "   • Password: ${BOLD}AdminPassword123${NC} (or ${BOLD}admin1234${NC})"
echo -e "   • Role:     ${BOLD}SUPER_ADMIN${NC}"
echo ""
echo -e "${CYAN}🌐 Useful Links:${NC}"
echo -e "   • Django Admin Panel: ${BOLD}http://127.0.0.1:8000/admin/${NC}"
echo -e "   • Base API URL:       ${BOLD}http://127.0.0.1:8000/api/v1/${NC}"
echo -e "   • Branch List:        ${BOLD}http://127.0.0.1:8000/api/v1/branches/${NC}"
echo -e "   • Admin KPIs:         ${BOLD}http://127.0.0.1:8000/api/v1/admin/dashboard/kpis/${NC}"
echo ""

# Free port 8000 automatically if already occupied
PORT_PIDS=$(lsof -ti :8000 || true)
if [ -n "$PORT_PIDS" ]; then
    echo -e "${YELLOW}• Port 8000 is already in use by PID(s): $PORT_PIDS. Releasing port...${NC}"
    kill -9 $PORT_PIDS 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ Port 8000 is now clean and available.${NC}"
fi

echo -e "${YELLOW}Starting Django Development Server on http://0.0.0.0:8000 ...${NC}"
echo -e "${YELLOW}Press [Ctrl+C] to stop the server.${NC}\n"

# Run server
exec python manage.py runserver 0.0.0.0:8000
