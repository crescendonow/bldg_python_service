import asyncio
from fastapi import APIRouter, HTTPException
from models.request import ExtractRequest
from models.job import ExtractionMethod, JobStatus
from services.job_store import get_job_store
from services import osm_extractor, gee_extractor, colab_trigger
import uuid

router = APIRouter()


@router.post("/extract")
async def submit_extract(req: ExtractRequest):
    job_store = get_job_store()
    job_id = str(uuid.uuid4())
    await job_store.create_job(job_id, req.method, req.formats, req.job_name)

    if req.method == ExtractionMethod.OSM:
        asyncio.create_task(
            osm_extractor.run(job_id, req.roi_geojson, req.formats, job_store)
        )
        return {"job_id": job_id, "status": "processing"}

    elif req.method == ExtractionMethod.GEE:
        asyncio.create_task(
            gee_extractor.run(
                job_id, req.roi_geojson, req.min_confidence, req.formats, job_store
            )
        )
        return {"job_id": job_id, "status": "processing"}

    elif req.method in (ExtractionMethod.SAM2, ExtractionMethod.SEGFORMER):
        try:
            colab_url = colab_trigger.prepare_colab_job(
                job_id, req.model_dump()
            )
        except ValueError as e:
            await job_store.update_job(job_id, status=JobStatus.FAILED, error=str(e))
            raise HTTPException(status_code=400, detail=str(e))

        await job_store.update_job(
            job_id,
            status=JobStatus.PENDING_COLAB,
            colab_url=colab_url,
        )
        return {
            "job_id": job_id,
            "status": "pending_colab",
            "colab_url": colab_url,
            "poll_interval_sec": 30,
        }
