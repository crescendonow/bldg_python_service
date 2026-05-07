import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from services.job_store import get_job_store
from services.drive_client import download_file
from services.format_converter import convert_gpkg, MIME_TYPES, DOWNLOAD_NAMES
from models.job import JobStatus

router = APIRouter()

VALID_FORMATS = {"gpkg", "geojson", "fgb", "shp", "kml", "tab"}


@router.get("/download/{job_id}/{fmt}")
async def download(job_id: str, fmt: str):
    if fmt not in VALID_FORMATS:
        raise HTTPException(status_code=400, detail=f"Invalid format: {fmt}")

    job_store = get_job_store()
    job = await job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Job not completed yet")

    out_dir = Path(f"/tmp/{job_id}")
    gpkg_path = str(out_dir / "buildings.gpkg")

    # Re-download from Drive if not cached locally
    if not Path(gpkg_path).exists():
        if not job.result_file_id:
            raise HTTPException(status_code=404, detail="Result file not found")
        out_dir.mkdir(parents=True, exist_ok=True)
        download_file(job.result_file_id, gpkg_path)

    # Determine target file path
    converted = convert_gpkg(gpkg_path, job_id, [fmt])
    file_path = converted.get(fmt)
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail=f"Format {fmt} not available")

    # Update formats_ready
    if fmt not in job.formats_ready:
        job.formats_ready.append(fmt)

    return FileResponse(
        path=file_path,
        media_type=MIME_TYPES.get(fmt, "application/octet-stream"),
        filename=DOWNLOAD_NAMES.get(fmt, f"buildings.{fmt}"),
    )
