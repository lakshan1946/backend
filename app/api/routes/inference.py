"""
Inference routes (Controller layer).
Handles HTTP requests and delegates business logic to services.
Follows SOLID principles - Single Responsibility (routing only).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models import User
from app.schemas import InferenceRequest
from app.auth import get_current_user
from app.services.job_service import JobService
from app.tasks.inference_tasks import inference_task
from app.constants import APIEndpoints, HTTPStatusMessages, JobConstants, EndpointDocs

router = APIRouter(prefix=APIEndpoints.INFERENCE_PREFIX, tags=["Inference"])


@router.post(
    APIEndpoints.INFERENCE_RUN,
    summary=EndpointDocs.INFERENCE_RUN_SUMMARY,
    description=EndpointDocs.INFERENCE_RUN_DESC
)
async def run_inference(
    request: InferenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Run super-resolution inference on a low-resolution file.
    
    Args:
        request: Inference request with LR file ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Inference job information
        
    Raises:
        ResourceNotFoundException: If LR file/job not found
        InvalidJobStateException: If preprocessing not completed
        ForbiddenException: If user doesn't own the job
    """
    job_service = JobService(db)
    
    # Validate the LR file/job belongs to user and is ready for inference
    lr_job = job_service.validate_job_for_inference(
        request.lr_file_id,
        current_user
    )
    
    # Create inference job
    inference_job = job_service.create_job(
        user=current_user,
        job_type=JobConstants.JOB_TYPE_INFERENCE,
        input_files=lr_job.output_files
    )
    
    # Trigger Celery inference task
    job_service.trigger_celery_task(
        job=inference_job,
        task_function=inference_task,
        args=[inference_job.id, lr_job.output_files],
        queue=JobConstants.QUEUE_INFERENCE
    )
    
    return {
        "inference_job_id": inference_job.id,
        "status": "pending",
        "message": HTTPStatusMessages.INFERENCE_STARTED
    }
