"""Dependency injection helpers for services."""

from typing import Callable
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService
from app.services.job_service import JobService
from app.services.file_service import FileService


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Dependency injection for AuthService.
    
    Args:
        db: Database session
        
    Returns:
        AuthService instance
    """
    return AuthService(db)


def get_job_service(db: Session = Depends(get_db)) -> JobService:
    """
    Dependency injection for JobService.
    
    Args:
        db: Database session
        
    Returns:
        JobService instance
    """
    return JobService(db)


def get_file_service(db: Session = Depends(get_db)) -> FileService:
    """
    Dependency injection for FileService.
    
    Args:
        db: Database session
        
    Returns:
        FileService instance
    """
    return FileService(db)
