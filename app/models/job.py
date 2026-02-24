"""Job model."""

from sqlalchemy import Column, String, Integer, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.base import JobStatus


class Job(Base):
    """Job database model."""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    progress = Column(Integer, default=0)
    job_type = Column(String, nullable=False)  # 'preprocess' or 'inference'
    error_message = Column(String, nullable=True)
    
    # File paths
    input_files = Column(JSON, nullable=True)  # List of input file paths
    output_files = Column(JSON, nullable=True)  # List of output file paths
    lr_file_url = Column(String, nullable=True)
    hr_file_url = Column(String, nullable=True)
    
    # Metrics
    metrics = Column(JSON, nullable=True)  # PSNR, SSIM, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
