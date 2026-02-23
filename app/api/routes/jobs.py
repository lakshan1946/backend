from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Job, JobStatus
from app.schemas import JobResponse
from app.auth import get_current_user
from app.tasks.preprocess_tasks import preprocess_pipeline_task
from app.tasks.inference_tasks import inference_task

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all jobs for current user."""
    jobs = db.query(Job).filter(
        Job.user_id == current_user.id
    ).order_by(Job.created_at.desc()).all()
    
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get job details by ID."""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a job and its associated files."""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # TODO: Delete associated files from storage
    
    db.delete(job)
    db.commit()
    
    return None


@router.post("/{job_id}/trigger")
async def trigger_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger a job that's stuck in PENDING status."""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status != JobStatus.PENDING:
        return {
            "message": f"Job is already {job.status.value}",
            "job_id": job_id,
            "current_status": job.status.value
        }
    
    # Re-trigger the appropriate task
    if job.job_type == "preprocess":
        if not job.input_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No input files found for this job"
            )
        
        preprocess_pipeline_task.apply_async(
            args=[job_id, job.input_files],
            task_id=job_id,
            queue='preprocessing'
        )
        return {
            "message": "Preprocessing task triggered",
            "job_id": job_id,
            "job_type": "preprocess"
        }
    
    elif job.job_type == "inference":
        if not job.input_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No input files found for this job"
            )
        
        inference_task.apply_async(
            args=[job_id, job.input_files],
            task_id=job_id,
            queue='inference'
        )
        return {
            "message": "Inference task triggered",
            "job_id": job_id,
            "job_type": "inference"
        }
    
    return {
        "message": f"Unknown job type: {job.job_type}",
        "job_id": job_id
    }
