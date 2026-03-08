# Quick Start Guide

## Prerequisites

Before getting started, ensure you have installed:

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Docker** - [Download](https://www.docker.com/products/docker-desktop)
- **Docker Compose** (usually included with Docker Desktop)
- **Git** - [Download](https://git-scm.com/)
- **curl** or Postman (for testing APIs)

Verify installations:
```bash
python --version
docker --version
docker-compose --version
git --version
```

## 5-Minute Setup

### 1. Clone Repository
```bash
cd ~/projects  # Or your preferred location
git clone <repository-url>
cd SmartBridge
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows
.venv\Scripts\activate

# Activate on macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create Environment File
```bash
# Copy template to .env
cp .env.example .env

# Edit .env if needed (default values work for local dev)
# nano .env    # or use your preferred editor
```

### 5. Start Services with Docker Compose
```bash
# Start PostgreSQL and spin up services
docker-compose up --build -d

# Verify services are running
docker-compose ps
```

### 6. Verify Backend Health
```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"ok"}
```

### 7. Run Tests (Optional)
```bash
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=backend
```

### 8. Start Frontend (In separate terminal)
```bash
# Make sure .venv is still activated

# Start Streamlit dashboard
streamlit run frontend/streamlit_app.py

# Opens automatically at http://localhost:8501
```

## Accessing the Application

- **Backend API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Frontend Dashboard**: http://localhost:8501
- **PostgreSQL**: localhost:5432

## Common Commands

### Run Backend with Hot Reload (Development)
```bash
# Terminal 1 - Keep docker-compose running
docker-compose up -d

# Terminal 2 - Run backend with auto-reload
source .venv/bin/activate  # Activate venv
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### View Database Logs
```bash
docker-compose logs -f postgres
```

### View Backend Logs
```bash
docker-compose logs -f backend
```

### Stop All Services
```bash
docker-compose down
```

### Remove Database (Clean Slate)
```bash
docker-compose down -v  # -v removes volumes
```

### Run Specific Tests
```bash
# Run only health tests
pytest tests/test_health.py -v

# Run with verbose output
pytest tests/ -vv

# Stop on first failure
pytest tests/ -x

# Show print statements
pytest tests/ -s
```

### Code Quality

```bash
# Format code with black
black backend/ frontend/

# Sort imports with isort
isort backend/ frontend/

# Check with flake8
flake8 backend/ frontend/

# Run all at once (pre-commit hooks)
pre-commit run --all-files
```

### Database Migrations (When Models Change)

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "descriptive message"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### PostgreSQL Connection Refused
```bash
# Check if docker-compose is running
docker-compose ps

# Restart services
docker-compose restart

# Check PostgreSQL logs
docker-compose logs postgres
```

### Virtual Environment Not Activating
```bash
# Recreate virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Python Version Issues
```bash
# Check Python version
python --version

# Use specific Python version
python3.10 -m venv .venv

# Or install Python 3.10+ from https://www.python.org
```

### Docker Permission Denied (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or
newgrp docker
```

## Project Structure

```
SmartBridge/
├── backend/              # FastAPI application
│   ├── main.py          # Entry point
│   ├── config.py        # Configuration
│   ├── db.py            # Database setup
│   ├── models.py        # ORM models
│   ├── routes/          # API endpoints
│   └── Dockerfile       # Container image
├── frontend/            # Streamlit dashboard
│   └── streamlit_app.py
├── tests/               # Test suite
│   └── test_health.py
├── scripts/             # Utility scripts
│   └── run_local.sh
├── docker-compose.yml   # Service orchestration
├── requirements.txt     # Python dependencies
├── .env.example         # Configuration template
└── docs/                # Documentation
```

## Next Steps

1. **Explore API Documentation**: http://localhost:8000/docs
2. **Review Code**: Start with `backend/main.py`
3. **Create Database Migration**: `alembic revision --autogenerate -m "your changes"`
4. **Add New Routes**: Create files in `backend/routes/`
5. **Write Tests**: Add to `tests/` directory
6. **Configure Pre-commit Hooks**: `pre-commit install`

## Environment Variables

Key variables in `.env`:

| Variable | Purpose | Example |
|----------|---------|---------|
| `DEBUG` | Enable debug mode | `true` |
| `ENVIRONMENT` | Deployment environment | `development` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host/db` |
| `SECRET_KEY` | JWT signing key | Long random string |
| `API_PORT` | Backend port | `8000` |

## Getting Help

- 📖 **README**: Full project overview in [README.md](../README.md)
- 🐛 **Issues**: Report problems on GitHub Issues
- 💬 **Discussions**: Ask questions in Discussions
- 📚 **API Docs**: Interactive docs at `/docs`

## Development Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes (code is auto-formatted by pre-commit)
3. Run tests: `pytest tests/ -v`
4. Commit: `git commit -am 'Add my feature'`
5. Push: `git push origin feature/my-feature`
6. Create Pull Request

## Deployment

For production deployment instructions, see the main [README.md](../README.md).

---

**Happy coding! 🚀**

For issues or questions, create an issue on GitHub.
