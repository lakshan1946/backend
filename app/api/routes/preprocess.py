from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Job, File, JobStatus
from app.schemas import UploadResponse
from app.auth import get_current_user
from app.tasks.preprocess_tasks import preprocess_pipeline_task
from app.config import settings
import uuid
import os
import aiofiles

router = APIRouter(prefix="/preprocess", tags=["Preprocessing"])


async def save_upload_file(upload_file: UploadFile, destination: str) -> int:
    """Save uploaded file to destination and return file size."""
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    file_size = 0
    async with aiofiles.open(destination, 'wb') as f:
        while chunk := await upload_file.read(8192):
            await f.write(chunk)
            file_size += len(chunk)
    
    return file_size


@router.post("/upload", response_model=UploadResponse)
async def upload_and_preprocess(
    files: List[UploadFile] = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload MRI files and start preprocessing."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    # Validate file extensions
    for file in files:
        if not (file.filename.endswith('.nii') or 
                file.filename.endswith('.nii.gz') or 
                file.filename.endswith('.gz')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file.filename}. Only NIfTI files are supported."
            )
    
    # Create job
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        user_id=current_user.id,
        status=JobStatus.PENDING,
        job_type="preprocess",
        progress=0
    )
    
    db.add(job)
    db.commit()
    
    # Save uploaded files
    file_paths = []
    file_records = []
    
    for upload_file in files:
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{upload_file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, current_user.id, filename)
        
        # Save file
        file_size = await save_upload_file(upload_file, file_path)
        
        # Check file size
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large: {upload_file.filename}"
            )
        
        # Create file record
        file_record = File(
            id=file_id,
            user_id=current_user.id,
            job_id=job_id,
            filename=filename,
            original_filename=upload_file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type="input"
        )
        
        db.add(file_record)
        file_paths.append(file_path)
        file_records.append(file_id)
    
    # Update job with input files
    job.input_files = file_paths
    db.commit()
    
    # Trigger Celery task
    preprocess_pipeline_task.apply_async(
        args=[job_id, file_paths],
        task_id=job_id
    )
    
    return {
        "job_id": job_id,
        "message": "Files uploaded successfully. Preprocessing started.",
        "files_uploaded": len(files)
    }
