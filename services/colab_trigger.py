import os
from datetime import datetime
from typing import Optional

from services.drive_client import write_json, ensure_folder

COLAB_NOTEBOOK_IDS: dict[str, str] = {}


def _get_notebook_id(method: str) -> Optional[str]:
    key = f"COLAB_NOTEBOOK_{method.upper()}"
    return os.environ.get(key) or COLAB_NOTEBOOK_IDS.get(method)


def prepare_colab_job(job_id: str, request_data: dict) -> str:
    """Write params to Drive and return the Colab URL for this job."""
    results_folder_id = os.environ["DRIVE_RESULTS_FOLDER_ID"]
    jobs_folder_id = os.environ["DRIVE_JOBS_FOLDER_ID"]

    params = {
        "job_id": job_id,
        "roi_geojson": request_data["roi_geojson"],
        "method": request_data["method"],
        "formats": request_data.get("formats", ["gpkg"]),
        "drive_result_folder_id": results_folder_id,
        "tile_size_deg": request_data.get("tile_size_deg", 0.0025),
        "tile_overlap_deg": request_data.get("tile_overlap_deg", 0.00025),
        "min_area_m2": request_data.get("min_area_m2", 12),
        "max_area_m2": request_data.get("max_area_m2", 5000),
        "zoom": request_data.get("zoom", 18),
        "created_at": datetime.utcnow().isoformat(),
    }

    write_json(params, f"{job_id}_params.json", jobs_folder_id)

    notebook_id = _get_notebook_id(request_data["method"])
    if not notebook_id:
        raise ValueError(
            f"Colab notebook ID not configured for method: {request_data['method']}. "
            f"Set env var COLAB_NOTEBOOK_{request_data['method'].upper()}"
        )

    return f"https://colab.research.google.com/drive/{notebook_id}"
