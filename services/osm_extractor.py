import os
import asyncio
from pathlib import Path

import geopandas as gpd
import osmnx as ox
from shapely.geometry import shape

from services.job_store import JobStore
from services.drive_client import upload_file
from models.job import JobStatus


async def run(job_id: str, roi_geojson: dict, job_store: JobStore) -> str:
    await job_store.update_job(job_id, status=JobStatus.PROCESSING, progress_pct=10)

    try:
        roi_geom = _extract_geometry(roi_geojson)

        await job_store.update_job(job_id, progress_pct=20)
        loop = asyncio.get_event_loop()
        gdf = await loop.run_in_executor(None, _query_osm, roi_geom)

        await job_store.update_job(job_id, progress_pct=70)

        out_dir = Path(f"/tmp/{job_id}")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = str(out_dir / "buildings.gpkg")
        gdf.to_file(out_path, driver="GPKG", layer="buildings")

        await job_store.update_job(job_id, progress_pct=85)

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


def _extract_geometry(roi_geojson: dict):
    geo_type = roi_geojson.get("type", "")
    if geo_type == "Feature":
        return shape(roi_geojson["geometry"])
    elif geo_type == "FeatureCollection":
        return shape(roi_geojson["features"][0]["geometry"])
    return shape(roi_geojson)


def _query_osm(roi_geom) -> gpd.GeoDataFrame:
    gdf = ox.features_from_polygon(roi_geom, tags={"building": True})
    buildings = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    buildings = buildings.to_crs(epsg=4326)
    # Keep only geometry + basic attributes
    keep_cols = ["geometry"]
    for col in ["building", "name", "addr:street"]:
        if col in buildings.columns:
            keep_cols.append(col)
    return buildings[keep_cols].reset_index(drop=True)
