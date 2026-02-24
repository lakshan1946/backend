# Backend API Architecture

## Overview
This backend API follows industry-standard architecture patterns with clear separation of concerns, implementing SOLID principles, DRY (Don't Repeat Yourself), and proper error handling.

## Architecture Layers

### 1. **Routes Layer** (`app/api/routes/`)
**Responsibility**: HTTP request handling (Controller layer)
- Handle HTTP requests and responses
- Input validation through Pydantic schemas
- Delegate business logic to services
- Return appropriate HTTP status codes
- **NO business logic** - only routing concerns

**Files**:
- `auth.py` - Authentication endpoints
- `jobs.py` - Job management endpoints
- `preprocess.py` - Preprocessing endpoints
- `inference.py` - Inference endpoints

### 2. **Service Layer** (`app/services/`)
**Responsibility**: Business logic
- Implement business rules and workflows
- Coordinate between repositories
- Handle transactions
- Validate business constraints
- Call external services (Celery tasks)

**Files**:
- `auth_service.py` - Authentication business logic
- `job_service.py` - Job management logic
- `file_service.py` - File operations logic

**Benefits**:
- Reusable business logic
- Testable without HTTP layer
- Clear business rules location

### 3. **Repository Layer** (`app/repositories/`)
**Responsibility**: Data access abstraction
- CRUD operations on database models
- Query encapsulation
- Database transaction handling
- No business logic

**Files**:
- `base_repository.py` - Base repository with common operations
- `user_repository.py` - User data access
- `job_repository.py` - Job data access
- `file_repository.py` - File data access

**Benefits**:
- Single source of truth for data access
- Easy to mock for testing
- Database changes isolated to one layer

### 4. **Utils Layer** (`app/utils/`)
**Responsibility**: Reusable utilities
- Custom exception classes
- Validators
- File handling utilities
- Helper functions

**Files**:
- `exceptions.py` - Custom exception classes
- `validators.py` - Validation utilities
- `file_utils.py` - File operation utilities

### 5. **Middleware Layer** (`app/middleware/`)
**Responsibility**: Cross-cutting concerns
- Global error handling
- Request/response logging
- Authentication middleware (future)
- Rate limiting (future)

**Files**:
- `error_handler.py` - Global exception handlers

### 6. **Models Layer** (`app/models.py`)
**Responsibility**: Database schema
- SQLAlchemy models
- Database relationships
- Enums and constants

### 7. **Schemas Layer** (`app/schemas.py`)
**Responsibility**: Data validation and serialization
- Pydantic models for request/response
- Input validation
- Data transformation

## SOLID Principles Implementation

### Single Responsibility Principle (SRP)
- Each class/module has one reason to change
- Routes only handle HTTP concerns
- Services only handle business logic
- Repositories only handle data access

### Open/Closed Principle (OCP)
- `BaseRepository` provides extensible base for all repositories
- Custom exceptions extend base `AppException`
- Services can be extended without modification

### Liskov Substitution Principle (LSP)
- All repositories can substitute `BaseRepository`
- All exceptions can substitute `AppException`

### Interface Segregation Principle (ISP)
- Small, focused interfaces
- Services don't depend on what they don't use
- Repositories expose only needed methods

### Dependency Inversion Principle (DIP)
- High-level modules (routes) depend on abstractions (services)
- Services depend on repository abstractions
- Use dependency injection via FastAPI's `Depends`

## DRY (Don't Repeat Yourself)

### Eliminated Duplication:
1. **Database queries**: Centralized in repositories
2. **File operations**: Reusable `FileHandler` class
3. **Validation logic**: Reusable validators
4. **Exception handling**: Global middleware
5. **CRUD operations**: `BaseRepository` with generics

## Error Handling

### Exception Hierarchy:
```
AppException (Base)
├── ResourceNotFoundException
├── ResourceAlreadyExistsException
├── UnauthorizedException
├── ForbiddenException
├── ValidationException
├── InvalidJobStateException
├── FileTooLargeException
└── InvalidFileTypeException
```

### Global Error Handlers:
- `app_exception_handler` - Custom application exceptions
- `sqlalchemy_exception_handler` - Database errors
- `general_exception_handler` - Unhandled exceptions

### Benefits:
- Consistent error responses
- Proper HTTP status codes
- Detailed error logging
- No try-catch in routes (handled globally)

## Data Flow

```
Client Request
    ↓
Route (Controller)
    ↓
Service (Business Logic)
    ↓
Repository (Data Access)
    ↓
Database
```

## Dependency Injection

Using FastAPI's dependency injection system:

```python
# In routes
@router.get("/jobs")
async def list_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job_service = JobService(db)
    return job_service.get_user_jobs(current_user)
```

## Testing Strategy

### Unit Tests:
- **Services**: Mock repositories
- **Repositories**: Mock database session
- **Validators**: Test different inputs
- **Utils**: Test helper functions

### Integration Tests:
- **Routes**: Test with test database
- **End-to-end**: Test full workflow

## Key Benefits

1. **Maintainability**: Clear structure, easy to find code
2. **Testability**: Each layer can be tested independently
3. **Scalability**: Easy to add new features
4. **Reusability**: Services and repositories are reusable
5. **Consistency**: Uniform error handling and validation
6. **Documentation**: Self-documenting code structure

## Code Examples

### Creating a New Feature

1. **Add Repository Method** (if needed):
```python
# app/repositories/job_repository.py
def get_jobs_by_date(self, user_id: str, date: datetime) -> List[Job]:
    return self.db.query(Job).filter(
        Job.user_id == user_id,
        Job.created_at >= date
    ).all()
```

2. **Add Service Method**:
```python
# app/services/job_service.py
def get_recent_jobs(self, user: User, days: int = 7) -> List[Job]:
    date = datetime.now() - timedelta(days=days)
    return self.job_repository.get_jobs_by_date(user.id, date)
```

3. **Add Route**:
```python
# app/api/routes/jobs.py
@router.get("/recent")
async def get_recent_jobs(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    return job_service.get_recent_jobs(current_user, days)
```

## Migration Guide

### Before (Old Code):
```python
# Direct database access in routes
@router.get("/jobs/{job_id}")
async def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    return job
```

### After (Refactored):
```python
# Clean separation of concerns
@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    return job_service.get_job_by_id(job_id, current_user)
```

## Best Practices

1. **Always use services in routes** - Never access repositories directly
2. **Always use repositories in services** - Never use raw SQLAlchemy queries
3. **Use custom exceptions** - Never raise generic exceptions
4. **Document public methods** - Use docstrings
5. **Keep routes thin** - Delegate everything to services
6. **Single responsibility** - Each method does one thing
7. **Dependency injection** - Use FastAPI's Depends
8. **Type hints** - Always specify types
