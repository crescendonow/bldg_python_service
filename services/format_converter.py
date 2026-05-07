import zipfile
from pathlib import Path

import geopandas as gpd


def convert_gpkg(gpkg_path: str, job_id: str, formats: list[str]) -> dict[str, str]:
    """Convert .gpkg to requested formats. Returns {fmt -> local_file_path}."""
    out_dir = Path(f"/tmp/{job_id}")
    out_dir.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(gpkg_path)
    results: dict[str, str] = {}

    if "gpkg" in formats:
        results["gpkg"] = gpkg_path

    if "geojson" in formats:
        path = out_dir / "buildings.geojson"
        gdf.to_file(str(path), driver="GeoJSON")
        results["geojson"] = str(path)

    if "fgb" in formats:
        path = out_dir / "buildings.fgb"
        gdf.to_file(str(path), driver="FlatGeobuf")
        results["fgb"] = str(path)

    if "shp" in formats:
        shp_dir = out_dir / "shp"
        shp_dir.mkdir(exist_ok=True)
        gdf.to_file(str(shp_dir / "buildings.shp"), driver="ESRI Shapefile")
        zip_path = out_dir / "buildings_shp.zip"
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            for f in shp_dir.iterdir():
                zf.write(f, arcname=f.name)
        results["shp"] = str(zip_path)

    if "kml" in formats:
        path = out_dir / "buildings.kml"
        gdf.to_file(str(path), driver="KML")
        results["kml"] = str(path)

    if "tab" in formats:
        tab_dir = out_dir / "tab"
        tab_dir.mkdir(exist_ok=True)
        tab_path = tab_dir / "buildings.tab"
        try:
            gdf.to_file(str(tab_path), driver="MapInfo File")
            zip_path = out_dir / "buildings_tab.zip"
            with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
                for f in tab_dir.iterdir():
                    zf.write(f, arcname=f.name)
            results["tab"] = str(zip_path)
        except Exception:
            # MapInfo driver not available — skip silently, endpoint returns 404
            pass

    return results


MIME_TYPES: dict[str, str] = {
    "gpkg": "application/geopackage+sqlite3",
    "geojson": "application/geo+json",
    "fgb": "application/octet-stream",
    "shp": "application/zip",
    "kml": "application/vnd.google-earth.kml+xml",
    "tab": "application/zip",
}

DOWNLOAD_NAMES: dict[str, str] = {
    "gpkg": "buildings.gpkg",
    "geojson": "buildings.geojson",
    "fgb": "buildings.fgb",
    "shp": "buildings_shp.zip",
    "kml": "buildings.kml",
    "tab": "buildings_tab.zip",
}
