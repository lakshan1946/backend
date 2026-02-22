from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
from app.models import JobStatus


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Job Schemas
class JobBase(BaseModel):
    job_type: str


class JobCreate(JobBase):
    input_files: List[str]


class JobResponse(BaseModel):
    id: str
    user_id: str
    status: JobStatus
    progress: int
    job_type: str
    error_message: Optional[str] = None
    input_files: Optional[List[str]] = None
    output_files: Optional[List[str]] = None
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
    status: Optional[JobStatus] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None
    output_files: Optional[List[str]] = None
    lr_file_url: Optional[str] = None
    hr_file_url: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None


# File Schemas
class FileResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Upload Response
class UploadResponse(BaseModel):
    job_id: str
    message: str
    files_uploaded: int


# Inference Request
class InferenceRequest(BaseModel):
    lr_file_id: str
