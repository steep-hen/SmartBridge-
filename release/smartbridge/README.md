# AI Financial Advisor

**Production-grade AI-powered financial advisory platform combining FastAPI backend with Streamlit frontend.**

## Overview

AI Financial Advisor is a full-stack application that delivers intelligent financial guidance through a modern, interactive interface. This repository contains both backend API services and a user-facing Streamlit dashboard.

### Tech Stack
- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: Streamlit
- **Database**: PostgreSQL 13+
- **Task Queue**: Optional (Celery ready)
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions

## Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- Git
- PostgreSQL CLI (optional, for development)

### Local Development (5 minutes)

1. **Clone and navigate to project**:
   ```bash
   cd SmartBridge
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file** (copy from template):
   ```bash
   cp .env.example .env
   ```

5. **Start services** (requires Docker):
   ```bash
   docker-compose up --build -d
   ```

6. **Verify health check**:
   ```bash
   curl http://localhost:8000/health
   ```
   Expected response: `{"status":"ok"}`

7. **Run Streamlit frontend** (in a separate terminal):
   ```bash
   streamlit run frontend/streamlit_app.py
   ```
   Opens at `http://localhost:8501`

### Docker Compose Startup

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Project Structure

```
SmartBridge/
├── backend/                    # FastAPI application
│   ├── main.py                # Application entry point
│   ├── config.py              # Configuration management
│   ├── db.py                  # Database connections
│   ├── models.py              # SQLAlchemy ORM models
│   ├── routes/                # API endpoint handlers
│   │   └── health.py          # Health check endpoint
│   └── Dockerfile             # Backend container image
├── frontend/                  # Streamlit application
│   └── streamlit_app.py       # Main dashboard
├── tests/                     # Test suite
│   └── test_health.py         # Health endpoint tests
├── scripts/                   # Utility scripts
│   └── run_local.sh          # Local development launcher
├── data/                      # Data storage (not versioned)
├── docs/                      # Documentation
│   └── quick_start.md         # Detailed setup guide
├── infra/                     # Infrastructure configs (future)
├── .github/workflows/         # CI/CD pipelines
│   └── ci.yml                # GitHub Actions workflow
├── docker-compose.yml         # Compose configuration
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── .gitignore                 # SCM exclusions
├── .pre-commit-config.yaml    # Pre-commit hooks
├── LICENSE                    # MIT License
└── README.md                  # This file
```

## Development

### Running Tests

```bash
# Run all tests with coverage
pytest --cov=backend tests/

# Run specific test file
pytest tests/test_health.py -v

# Run with markers
pytest -m "not slow" tests/
```

### Code Quality

```bash
# Format code
black backend/ frontend/

# Sort imports
isort backend/ frontend/

# Lint code
flake8 backend/ frontend/

# All at once (via pre-commit)
pre-commit run --all-files
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### API Documentation

Once backend is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

See `.env.example` for all configurable options:

| Variable | Description | Example |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `true` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/ai_advisor` |
| `SECRET_KEY` | JWT signing key | `your-secret-key-here` |
| `API_PORT` | Backend API port | `8000` |

## CI/CD Pipeline

GitHub Actions automatically:
- Runs `flake8` linter on every push
- Executes full test suite with `pytest`
- Builds and pushes Docker image to registry (on main branch)

View workflow status: `.github/workflows/`

## Deployment

### To Staging/Production

```bash
# Push to main triggers CI/CD
git push origin main

# Monitor deployment
# Check Actions tab on GitHub
```

### Manual Docker Build

```bash
docker build -t ai-advisor:latest backend/
docker run -p 8000:8000 --env-file .env ai-advisor:latest
```

## API Examples

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "ok"}
```

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/my-feature`
4. Open Pull Request

Code style enforced via pre-commit hooks and GitHub Actions.

## License

MIT License - see LICENSE file for details.

## Support

- 📖 [Detailed Setup Guide](docs/quick_start.md)
- 🐛 [Issue Tracker](../../issues)
- 💬 [Discussions](../../discussions)

---

**Current Status**: Production-ready scaffold v1.0  
**Last Updated**: 2026-03-08
