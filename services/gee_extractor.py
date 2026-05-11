import os
import asyncio
from pathlib import Path

import geopandas as gpd
import ee
from shapely.geometry import shape, mapping

from services.job_store import JobStore
from services.drive_client import upload_file
from models.job import JobStatus


def _init_ee():
    sa_json_str = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    sa_email = os.environ["EE_SERVICE_ACCOUNT_EMAIL"]
    project = os.environ.get("EE_PROJECT", "myearthengine-495505")
    credentials = ee.ServiceAccountCredentials(sa_email, key_data=sa_json_str)
    ee.Initialize(credentials, project=project)


def _geom_to_ee(geom) -> ee.Geometry:
    coords = list(geom.exterior.coords)
    return ee.Geometry.Polygon([list(c) for c in coords])


async def run(
    job_id: str,
    roi_geojson: dict,
    min_confidence: float,
    job_store: JobStore,
) -> str:
    await job_store.update_job(job_id, status=JobStatus.PROCESSING, progress_pct=10)

    try:
        loop = asyncio.get_event_loop()
        out_path = await loop.run_in_executor(
            None, _run_sync, job_id, roi_geojson, min_confidence
        )
        results_folder_id = os.environ.get("DRIVE_RESULTS_FOLDER_ID", "")
        if results_folder_id:
            file_id = upload_file(out_path, f"{job_id}_result.gpkg", results_folder_id)
            await job_store.update_job(job_id, result_file_id=file_id)

        await job_store.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            progress_pct=100,
            formats_ready=["gpkg"],
        )
        return out_path

    except Exception as exc:
        await job_store.update_job(job_id, status=JobStatus.FAILED, error=str(exc))
        raise


def _run_sync(job_id: str, roi_geojson: dict, min_confidence: float) -> str:
    _init_ee()

    geo_type = roi_geojson.get("type", "")
    if geo_type == "Feature":
        geom = shape(roi_geojson["geometry"])
    elif geo_type == "FeatureCollection":
        geom = shape(roi_geojson["features"][0]["geometry"])
    else:
        geom = shape(roi_geojson)

    roi_ee = _geom_to_ee(geom)
    collection = (
        ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons")
        .filterBounds(roi_ee)
        .filter(ee.Filter.gte("confidence", min_confidence))
    )

    fc_dict = collection.getInfo()
    features = fc_dict.get("features", [])
    if not features:
        # Return empty GeoDataFrame
        gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    else:
        gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
        gdf = gdf.clip(geom)

    out_dir = Path(f"/tmp/{job_id}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(out_dir / "buildings.gpkg")
    gdf.to_file(out_path, driver="GPKG", layer="buildings")
    return out_path
