"""Job schemas."""

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from app.models import JobStatus


class JobBase(BaseModel):
    """Base job schema."""
    job_type: str


class JobCreate(JobBase):
    """Schema for creating a job."""
    input_files: List[str]


class JobResponse(BaseModel):
    """Schema for job response."""
    id: str
    user_id: str
    status: JobStatus
    progress: int
    job_type: str
    error_message: Optional[str] = None
    input_files: Optional[List[str]] = None
    output_files: Optional[List[Dict[str, str]]] = None
    lr_file_url: Optional[str] = None
    hr_file_url: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class JobUpdate(BaseModel):
    """Schema for updating a job."""
    status: Optional[JobStatus] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None
    output_files: Optional[List[Dict[str, str]]] = None
    lr_file_url: Optional[str] = None
    hr_file_url: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
