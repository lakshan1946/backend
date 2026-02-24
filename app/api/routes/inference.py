from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Job, JobStatus
from app.schemas import InferenceRequest
from app.auth import get_current_user
from app.tasks.inference_tasks import inference_task
import uuid

router = APIRouter(prefix="/infer", tags=["Inference"])


@router.post("")
async def run_inference(
    request: InferenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run super-resolution inference on a low-resolution file."""
    # Verify the LR file/job belongs to the user
    lr_job = db.query(Job).filter(
        Job.id == request.lr_file_id,
        Job.user_id == current_user.id
    ).first()
    
    if not lr_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LR file/job not found"
        )
    
    if lr_job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preprocessing must be completed before running inference"
        )
    
    # Create inference job
    inference_job_id = str(uuid.uuid4())
    inference_job = Job(
        id=inference_job_id,
        user_id=current_user.id,
        status=JobStatus.PENDING,
        job_type="inference",
        progress=0,
        input_files=lr_job.output_files  # Use preprocessed outputs as input
    )
    
    db.add(inference_job)
    db.commit()
    
    # Trigger Celery task
    inference_task.apply_async(
        args=[inference_job_id, lr_job.output_files],
        task_id=inference_job_id,
        queue='inference'
    )
    
    return {
        "inference_job_id": inference_job_id,
        "status": "pending",
        "message": "Inference task started"
    }
