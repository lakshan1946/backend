import sys
import os
from datetime import datetime
from pathlib import Path

# Add the MRI pipeline to the Python path
pipeline_path = Path(__file__).parent.parent.parent / "mri_sr_pipeline"
sys.path.insert(0, str(pipeline_path))

from celery import shared_task
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Job, JobStatus
from app.config import settings

# Import the existing MRI preprocessing pipeline
try:
    from src.pipeline import MRIPreprocessingPipeline
    from src.brain_extraction import extract_brain
    from src.normalize import normalize_intensity
    import ants
except ImportError as e:
    print(f"Warning: Could not import MRI pipeline modules: {e}")
    MRIPreprocessingPipeline = None


def update_job_status(
    job_id: str,
    status: JobStatus,
    progress: int = None,
    error_message: str = None,
    output_files: list = None,
    lr_file_url: str = None,
    hr_file_url: str = None
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
            if lr_file_url:
                job.lr_file_url = lr_file_url
            if hr_file_url:
                job.hr_file_url = hr_file_url
            
            if status == JobStatus.PROCESSING and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status == JobStatus.COMPLETED:
                job.completed_at = datetime.utcnow()
                job.progress = 100
            
            db.commit()
    finally:
        db.close()


@shared_task(bind=True, name="app.tasks.preprocess_tasks.preprocess_pipeline_task")
def preprocess_pipeline_task(self, job_id: str, file_paths: list):
    """
    Execute MRI preprocessing pipeline on uploaded files.
    
    Steps:
    1. Load MRI scans
    2. Brain extraction (HD-BET)
    3. N4 bias correction
    4. Intensity normalization
    5. Generate HR and degraded LR pairs
    6. Save outputs
    """
    try:
        update_job_status(job_id, JobStatus.PROCESSING, progress=0)
        
        # Create output directory
        output_dir = os.path.join(settings.OUTPUT_DIR, job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        output_files = []
        
        for idx, file_path in enumerate(file_paths):
            # Update progress
            base_progress = int((idx / len(file_paths)) * 90)
            update_job_status(job_id, JobStatus.PROCESSING, progress=base_progress)
            
            # Load MRI scan
            print(f"Loading: {file_path}")
            img = ants.image_read(file_path)
            
            # Step 1: Brain extraction (10% progress per step)
            update_job_status(job_id, JobStatus.PROCESSING, progress=base_progress + 10)
            print("Extracting brain...")
            brain_img = extract_brain(img)
            
            # Step 2: Bias correction
            update_job_status(job_id, JobStatus.PROCESSING, progress=base_progress + 30)
            print("Applying bias correction...")
            corrected_img = ants.n4_bias_field_correction(brain_img)
            
            # Step 3: Normalization
            update_job_status(job_id, JobStatus.PROCESSING, progress=base_progress + 50)
            print("Normalizing intensity...")
            normalized_img = normalize_intensity(corrected_img)
            
            # Step 4: Save HR image
            update_job_status(job_id, JobStatus.PROCESSING, progress=base_progress + 70)
            hr_filename = f"hr_{idx}.nii.gz"
            hr_path = os.path.join(output_dir, hr_filename)
            ants.image_write(normalized_img, hr_path)
            
            # Step 5: Generate LR image (degradation)
            update_job_status(job_id, JobStatus.PROCESSING, progress=base_progress + 80)
            print("Generating LR image...")
            from src.degradation import degrade_image
            lr_img = degrade_image(normalized_img, scale_factor=2)
            
            lr_filename = f"lr_{idx}.nii.gz"
            lr_path = os.path.join(output_dir, lr_filename)
            ants.image_write(lr_img, lr_path)
            
            output_files.append({
                "hr": hr_path,
                "lr": lr_path
            })
        
        # Complete
        update_job_status(
            job_id,
            JobStatus.COMPLETED,
            progress=100,
            output_files=output_files,
            lr_file_url=f"/api/files/{job_id}/lr_0.nii.gz",
            hr_file_url=f"/api/files/{job_id}/hr_0.nii.gz"
        )
        
        return {
            "status": "success",
            "job_id": job_id,
            "output_files": output_files
        }
        
    except Exception as e:
        print(f"Error in preprocessing task: {str(e)}")
        import traceback
        traceback.print_exc()
        
        update_job_status(
            job_id,
            JobStatus.FAILED,
            error_message=str(e)
        )
        raise
