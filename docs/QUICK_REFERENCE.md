# Quick Reference Guide

## Adding a New Feature

### Example: Add "Get Jobs by Status" Feature

#### 1. Add Repository Method (if needed)
**File**: `app/repositories/job_repository.py`

```python
def get_by_status(self, user_id: str, status: JobStatus) -> List[Job]:
    """Get all jobs for a user with specific status."""
    return (
        self.db.query(Job)
        .filter(Job.user_id == user_id, Job.status == status)
        .all()
    )
```

#### 2. Add Service Method
**File**: `app/services/job_service.py`

```python
def get_jobs_by_status(self, user: User, status: JobStatus) -> List[Job]:
    """Get jobs filtered by status."""
    try:
        return self.job_repository.get_by_status(user.id, status)
    except Exception as e:
        raise Exception(f"Failed to get jobs by status: {str(e)}")
```

#### 3. Add Route
**File**: `app/api/routes/jobs.py`

```python
@router.get("/filter/{status}", response_model=List[JobResponse])
async def get_jobs_by_status(
    status: JobStatus,
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
) -> List[JobResponse]:
    """Get jobs filtered by status."""
    return job_service.get_jobs_by_status(current_user, status)
```

---

## Adding Custom Exception

**File**: `app/utils/exceptions.py`

```python
class QuotaExceededException(AppException):
    """Raised when user exceeds quota."""
    
    def __init__(self, resource: str, limit: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"{resource} quota exceeded. Limit: {limit}"
        )
```

**Usage in Service**:
```python
if user_jobs_count >= MAX_JOBS:
    raise QuotaExceededException("Jobs", MAX_JOBS)
```

---

## Adding Validation

**File**: `app/utils/validators.py`

```python
class JobValidator:
    """Validator for jobs."""
    
    @staticmethod
    def validate_job_name(name: str) -> None:
        """Validate job name."""
        if len(name) < 3 or len(name) > 50:
            raise ValidationException(
                "Job name must be between 3 and 50 characters"
            )
```

**Usage in Service**:
```python
JobValidator.validate_job_name(job_data.name)
```

---

## Dependency Injection Patterns

### Pattern 1: Use Service Directly
```python
@router.get("/jobs")
async def list_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job_service = JobService(db)
    return job_service.get_user_jobs(current_user)
```

### Pattern 2: Use Dependency Helper (Recommended)
```python
@router.get("/jobs")
async def list_jobs(
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    return job_service.get_user_jobs(current_user)
```

---

## Error Handling Patterns

### In Services (Throw Custom Exceptions)
```python
def get_job(self, job_id: str) -> Job:
    job = self.job_repository.get_by_id(job_id)
    if not job:
        raise ResourceNotFoundException("Job", job_id)
    return job
```

### In Routes (Let Middleware Handle)
```python
@router.get("/jobs/{job_id}")
async def get_job(job_id: str, service: JobService = Depends()):
    # No try-catch needed - middleware handles exceptions
    return service.get_job(job_id)
```

---

## Testing Patterns

### Test Service (Unit Test)
```python
def test_create_job():
    # Arrange
    mock_repo = Mock(JobRepository)
    service = JobService(mock_db)
    service.job_repository = mock_repo
    
    # Act
    job = service.create_job(user, "preprocess")
    
    # Assert
    assert job.job_type == "preprocess"
    mock_repo.create.assert_called_once()
```

### Test Repository (Unit Test)
```python
def test_get_by_user_id():
    # Arrange
    repo = JobRepository(test_db)
    
    # Act
    jobs = repo.get_by_user_id(user_id)
    
    # Assert
    assert len(jobs) > 0
    assert all(j.user_id == user_id for j in jobs)
```

### Test Route (Integration Test)
```python
def test_list_jobs_endpoint():
    # Arrange
    headers = {"Authorization": f"Bearer {token}"}
    
    # Act
    response = client.get("/api/jobs", headers=headers)
    
    # Assert
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

## Common Commands

### Run Development Server
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests
```bash
pytest tests/ -v
pytest tests/test_services.py -v
pytest tests/test_repositories.py -v
```

### Check Code Quality
```bash
# Format code
black app/

# Check typing
mypy app/

# Lint code
pylint app/
```

---

## File Naming Conventions

- **Services**: `{domain}_service.py` (e.g., `auth_service.py`)
- **Repositories**: `{model}_repository.py` (e.g., `user_repository.py`)
- **Routes**: `{domain}.py` (e.g., `auth.py`, `jobs.py`)
- **Utils**: `{purpose}_utils.py` or `{purpose}.py`

---

## Class Naming Conventions

- **Services**: `{Domain}Service` (e.g., `AuthService`)
- **Repositories**: `{Model}Repository` (e.g., `UserRepository`)
- **Exceptions**: `{Reason}Exception` (e.g., `ResourceNotFoundException`)
- **Validators**: `{Domain}Validator` (e.g., `FileValidator`)

---

## Method Naming Conventions

### Repositories
- `get_by_{field}()` - Get single entity
- `get_all()` - Get all entities
- `create()` - Create entity
- `update()` - Update entity
- `delete()` - Delete entity
- `exists()` - Check existence

### Services
- `create_{entity}()` - Create entity with business logic
- `get_{entity}()` - Get entity with permissions check
- `update_{entity}()` - Update with validation
- `delete_{entity}()` - Delete with cleanup
- `validate_{aspect}()` - Validation methods

### Routes
- `create_{entity}()` - POST endpoints
- `get_{entity}()` - GET endpoints
- `list_{entities}()` - GET collection endpoints
- `update_{entity}()` - PUT/PATCH endpoints
- `delete_{entity}()` - DELETE endpoints

---

## Best Practices Checklist

### When Writing Routes ✅
- [ ] Keep routes thin (< 15 lines)
- [ ] Use proper HTTP status codes
- [ ] Add response models
- [ ] Add comprehensive docstrings
- [ ] Add summary and description
- [ ] Use dependency injection
- [ ] Don't handle exceptions (let middleware do it)
- [ ] Don't access repository directly

### When Writing Services ✅
- [ ] One service per domain
- [ ] Methods have single responsibility
- [ ] Use repositories for data access
- [ ] Throw custom exceptions
- [ ] Add try-except for external calls
- [ ] Add comprehensive docstrings
- [ ] Return domain objects, not DB models

### When Writing Repositories ✅
- [ ] Extend BaseRepository
- [ ] Keep methods focused on data access
- [ ] No business logic
- [ ] Return model instances or lists
- [ ] Handle SQLAlchemy exceptions
- [ ] Add type hints

### When Writing Utilities ✅
- [ ] Keep utilities stateless when possible
- [ ] Use static methods for stateless functions
- [ ] Add comprehensive docstrings
- [ ] Make reusable and generic

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Auth
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Files
UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs
MAX_UPLOAD_SIZE=104857600  # 100MB

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## Troubleshooting

### Import Errors
```bash
# Make sure you're in the backend directory
cd backend

# Run with module syntax
python -m uvicorn main:app --reload
```

### Database Errors
```bash
# Reset database
python -c "from app.database import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"
```

### Celery Not Working
```bash
# Start Celery worker
celery -A app.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.celery_app beat --loglevel=info
```

---

## Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **Celery Docs**: https://docs.celeryproject.org/

---

## Need Help?

1. Check [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture explanation
2. Check [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) for what changed
3. Look at existing code for patterns
4. Follow SOLID principles
5. Keep it DRY (Don't Repeat Yourself)
