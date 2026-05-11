import asyncio
from datetime import datetime
from typing import Optional
from models.job import Job, JobStatus, ExtractionMethod


class JobStore:
    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = asyncio.Lock()

    async def create_job(
        self,
        job_id: str,
        method: ExtractionMethod,
        requested_formats: Optional[list[str]] = None,
        job_name: Optional[str] = None,
    ) -> Job:
        job = Job(
            job_id=job_id,
            method=method,
            job_name=job_name,
            requested_formats=requested_formats or ["gpkg", "geojson"],
        )
        async with self._lock:
            self._jobs[job_id] = job
        return job

    async def update_job(self, job_id: str, **kwargs) -> Optional[Job]:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            for k, v in kwargs.items():
                setattr(job, k, v)
            job.updated_at = datetime.utcnow()
            return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    async def list_jobs(self, limit: int = 20) -> list[Job]:
        jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]


_store = JobStore()


def get_job_store() -> JobStore:
    return _store
