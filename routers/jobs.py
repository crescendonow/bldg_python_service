import os
from fastapi import APIRouter, HTTPException
from services.job_store import get_job_store
from services.drive_client import find_file
from models.job import JobStatus

router = APIRouter()


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job_store = get_job_store()
    job = await job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # For GPU jobs still pending, check Drive for completion
    if job.status == JobStatus.PENDING_COLAB:
        results_folder_id = os.environ.get("DRIVE_RESULTS_FOLDER_ID", "")
        if results_folder_id:
            file_id = find_file(f"{job_id}_result.gpkg", results_folder_id)
            if file_id:
                await job_store.update_job(
                    job_id,
                    status=JobStatus.COMPLETED,
                    result_file_id=file_id,
                    progress_pct=100,
                    formats_ready=job.requested_formats,
                )
                job = await job_store.get_job(job_id)

    return job.model_dump_response()


@router.get("/jobs")
async def list_jobs():
    job_store = get_job_store()
    jobs = await job_store.list_jobs(limit=20)
    return [j.model_dump_response() for j in jobs]


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    job_store = get_job_store()
    job = await job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    async with job_store._lock:
        del job_store._jobs[job_id]
    return {"deleted": job_id}
