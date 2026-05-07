from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PENDING_COLAB = "pending_colab"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionMethod(str, Enum):
    OSM = "osm"
    GEE = "gee"
    SAM2 = "sam2"
    SEGFORMER = "segformer"


class Job(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_name: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    method: ExtractionMethod
    progress_pct: int = 0
    result_file_id: Optional[str] = None
    formats_ready: list[str] = []
    colab_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def model_dump_response(self) -> dict:
        return {
            "job_id": self.job_id,
            "job_name": self.job_name,
            "status": self.status.value,
            "method": self.method.value,
            "progress_pct": self.progress_pct,
            "result_file_id": self.result_file_id,
            "formats_ready": self.formats_ready,
            "colab_url": self.colab_url,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
