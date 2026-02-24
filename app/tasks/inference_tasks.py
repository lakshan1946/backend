import sys
import os
from pathlib import Path
from datetime import datetime

# Add the MRI pipeline to the Python path
pipeline_path = Path(__file__).parent.parent.parent / "mri_sr_pipeline"
sys.path.insert(0, str(pipeline_path))

from celery import shared_task
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import Job, JobStatus
from app.core.config import settings
import torch
import ants
import numpy as np


def update_job_status(
    job_id: str,
    status: JobStatus,
    progress: int = None,
    error_message: str = None,
    output_files: list = None,
    hr_file_url: str = None,
    metrics: dict = None
):
    """Update job status in database."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            if progress is not None:
                job.progress = progress
            if error_message:
                job.error_message = error_message
            if output_files:
                job.output_files = output_files
            if hr_file_url:
                job.hr_file_url = hr_file_url
            if metrics:
                job.metrics = metrics
            
            if status == JobStatus.PROCESSING and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status == JobStatus.COMPLETED:
                job.completed_at = datetime.utcnow()
                job.progress = 100
            
            db.commit()
    finally:
        db.close()


class ModelManager:
    """Singleton for model management."""
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(self):
        """Load the super-resolution model."""
        if self._model is None:
            model_path = settings.MODEL_PATH
            if os.path.exists(model_path):
                print(f"Loading model from {model_path}")
                self._model = torch.load(model_path, map_location='cpu')
                self._model.eval()
            else:
                print(f"Warning: Model not found at {model_path}")
                self._model = None
        return self._model


model_manager = ModelManager()


@shared_task(bind=True, name="app.tasks.inference_tasks.inference_task")
def inference_task(self, job_id: str, input_files: list):
    """
    Execute super-resolution inference on preprocessed LR images.
    
    Steps:
    1. Load LR image
    2. Preprocess for model input
    3. Run model inference
    4. Post-process output
    5. Save SR image
    """
    try:
        update_job_status(job_id, JobStatus.PROCESSING, progress=0)
        
        # Load model
        update_job_status(job_id, JobStatus.PROCESSING, progress=10)
        model = model_manager.load_model()
        
        if model is None:
            raise Exception("Model not loaded. Please ensure model file exists.")
        
        # Create output directory
        output_dir = os.path.join(settings.OUTPUT_DIR, job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        output_files = []
        
        # Process each file
        for idx, file_info in enumerate(input_files):
            # Get LR file path
            if isinstance(file_info, dict):
                lr_path = file_info.get('lr')
            else:
                lr_path = file_info
            
            if not os.path.exists(lr_path):
                print(f"Warning: File not found: {lr_path}")
                continue
            
            base_progress = 20 + int((idx / len(input_files)) * 70)
            update_job_status(job_id, JobStatus.PROCESSING, progress=base_progress)
            
            # Load LR image
            print(f"Loading LR image: {lr_path}")
            lr_image = ants.image_read(lr_path)
            lr_array = lr_image.numpy()
            
            # Preprocess for model
            update_job_status(job_id, JobStatus.PROCESSING, progress=base_progress + 10)
            lr_tensor = torch.from_numpy(lr_array).float()
            lr_tensor = lr_tensor.unsqueeze(0).unsqueeze(0)  # Add batch and channel dims
            
            # Run inference
            update_job_status(job_id, JobStatus.PROCESSING, progress=base_progress + 30)
            print("Running inference...")
            with torch.no_grad():
                sr_tensor = model(lr_tensor)
            
            # Post-process
            update_job_status(job_id, JobStatus.PROCESSING, progress=base_progress + 50)
            sr_array = sr_tensor.squeeze().numpy()
            
            # Create ANTs image with preserved metadata
            sr_image = ants.from_numpy(
                sr_array,
                origin=lr_image.origin,
                spacing=lr_image.spacing,
                direction=lr_image.direction
            )
            
            # Save SR image
            update_job_status(job_id, JobStatus.PROCESSING, progress=base_progress + 70)
            sr_filename = f"sr_{idx}.nii.gz"
            sr_path = os.path.join(output_dir, sr_filename)
            ants.image_write(sr_image, sr_path)
            
            output_files.append(sr_path)
        
        # Calculate metrics (if HR reference available)
        metrics = {}
        # TODO: Add PSNR, SSIM calculation
        
        # Complete
        update_job_status(
            job_id,
            JobStatus.COMPLETED,
            progress=100,
            output_files=output_files,
            hr_file_url=f"/api/files/{job_id}/sr_0.nii.gz",
            metrics=metrics
        )
        
        return {
            "status": "success",
            "job_id": job_id,
            "output_files": output_files,
            "metrics": metrics
        }
        
    except Exception as e:
        print(f"Error in inference task: {str(e)}")
        import traceback
        traceback.print_exc()
        
        update_job_status(
            job_id,
            JobStatus.FAILED,
            error_message=str(e)
        )
        raise
