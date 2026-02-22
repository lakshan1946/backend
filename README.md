# MRI Super-Resolution Backend API

FastAPI backend for the MRI Super-Resolution web application with Celery task queue for async processing.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 15+
- Redis 7+
- (Optional) Docker & Docker Compose

### Local Development Setup

1. **Create virtual environment:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Start PostgreSQL and Redis** (if not using Docker):
```bash
# PostgreSQL
docker run -d --name mri_postgres -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=mri_sr_db \
  postgres:15-alpine

# Redis
docker run -d --name mri_redis -p 6379:6379 redis:7-alpine
```

5. **Run database migrations:**
```bash
# The tables will be auto-created on first run
# Or use Alembic for migrations (optional)
```

6. **Start the FastAPI server:**
```bash
uvicorn main:app --reload --port 8000
```

7. **Start Celery workers** (in separate terminals):
```bash
# Preprocessing worker
celery -A app.celery_app worker --loglevel=info -Q preprocessing --concurrency=2

# Inference worker
celery -A app.celery_app worker --loglevel=info -Q inference --concurrency=1
```

8. **Access the API:**
- API: http://localhost:8000
- Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Docker Setup (Recommended)

```bash
# From the project root directory
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── preprocess.py    # File upload & preprocessing
│   │       ├── jobs.py          # Job management
│   │       └── inference.py     # SR inference
│   ├── tasks/
│   │   ├── preprocess_tasks.py  # Celery preprocessing tasks
│   │   └── inference_tasks.py   # Celery inference tasks
│   ├── models.py                # SQLAlchemy models
│   ├── schemas.py               # Pydantic schemas
│   ├── database.py              # Database connection
│   ├── config.py                # Configuration
│   ├── auth.py                  # Authentication utilities
│   └── celery_app.py           # Celery configuration
├── main.py                      # FastAPI application
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker image
└── .env.example                 # Environment variables template
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user info

### Preprocessing
- `POST /api/preprocess/upload` - Upload MRI files and start preprocessing

### Jobs
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{job_id}` - Get job details
- `DELETE /api/jobs/{job_id}` - Delete job

### Inference
- `POST /api/infer` - Run super-resolution inference

### Files
- `GET /api/files/{job_id}/{filename}` - Download processed files

## 🛠️ Technology Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Relational database
- **Redis** - Message broker and cache
- **Celery** - Distributed task queue
- **Pydantic** - Data validation
- **JWT** - Authentication tokens
- **ANTs** - Medical image processing
- **PyTorch** - Deep learning inference

## 🔧 Configuration

Edit `.env` file:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS (Frontend URL)
CORS_ORIGINS=["http://localhost:3000"]

# JWT
JWT_SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Storage
UPLOAD_DIR=./data/uploads
OUTPUT_DIR=./data/outputs
MAX_UPLOAD_SIZE=524288000  # 500MB

# Model
MODEL_PATH=./models/best_model.pth
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## 📊 Monitoring Celery

```bash
# Monitor Celery tasks
celery -A app.celery_app events

# Flower (Web UI for Celery)
pip install flower
celery -A app.celery_app flower
# Access at http://localhost:5555
```

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS configuration
- File size limits
- Input validation with Pydantic

## 📝 Database Models

### User
- id, email, name, hashed_password
- created_at, updated_at
- Relationship: jobs

### Job
- id, user_id, status, progress, job_type
- input_files, output_files
- lr_file_url, hr_file_url, metrics
- created_at, started_at, completed_at

### File
- id, user_id, job_id
- filename, file_path, file_size, file_type

## 🚧 Celery Tasks

### Preprocessing Task
1. Load MRI scan
2. Brain extraction (HD-BET)
3. Bias correction (N4)
4. Intensity normalization
5. Generate HR/LR pairs
6. Save outputs

### Inference Task
1. Load LR image
2. Preprocess for model
3. Run model inference
4. Post-process output
5. Save SR image
6. Calculate metrics

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -U postgres -d mri_sr_db
```

### Celery Worker Not Starting
```bash
# Check Redis is running
redis-cli ping

# Clear Celery queue
celery -A app.celery_app purge
```

### Import Errors
```bash
# Ensure MRI pipeline is accessible
export PYTHONPATH="${PYTHONPATH}:../mri_sr_pipeline"
```

## 📦 Dependencies

Key Python packages:
- fastapi==0.109.2
- celery==5.3.6
- sqlalchemy==2.0.25
- psycopg2-binary==2.9.9
- redis==5.0.1
- python-jose[cryptography]==3.3.0
- ants==0.4.2
- torch==2.2.0

## 🚀 Production Deployment

### Environment Variables
Set secure values for production:
- Strong `SECRET_KEY` and `JWT_SECRET_KEY`
- Production database URL
- Disable `DEBUG=False`
- Configure proper CORS origins

### Gunicorn (Production Server)
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### HTTPS/SSL
Use nginx reverse proxy with SSL certificates

### Supervisor (Process Management)
```bash
sudo apt-get install supervisor
# Configure supervisor to manage Celery workers
```

## 📄 License

Part of MRI Super-Resolution Pipeline FYP Project

## 👥 Support

For issues and questions, please check:
- API Documentation: http://localhost:8000/api/docs
- Frontend README: ../frontend/README.md
- Architecture Doc: ../mri_sr_pipeline/docs/web_application_architecture.md
