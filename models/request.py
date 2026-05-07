from typing import Optional
from pydantic import BaseModel, Field, field_validator
from models.job import ExtractionMethod

VALID_FORMATS = {"gpkg", "geojson", "fgb", "shp", "kml", "tab"}


class ExtractRequest(BaseModel):
    roi_geojson: dict
    method: ExtractionMethod
    min_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    formats: list[str] = Field(default=["gpkg", "geojson"])
    job_name: Optional[str] = None

    @field_validator("formats")
    @classmethod
    def validate_formats(cls, v: list[str]) -> list[str]:
        invalid = set(v) - VALID_FORMATS
        if invalid:
            raise ValueError(f"Invalid formats: {invalid}. Valid: {VALID_FORMATS}")
        if not v:
            raise ValueError("At least one format required")
        return v

    @field_validator("roi_geojson")
    @classmethod
    def validate_roi(cls, v: dict) -> dict:
        geo_type = v.get("type", "")
        if geo_type == "Feature":
            geom = v.get("geometry", {})
        elif geo_type in ("Polygon", "MultiPolygon"):
            geom = v
        elif geo_type == "FeatureCollection":
            features = v.get("features", [])
            if not features:
                raise ValueError("FeatureCollection has no features")
            geom = features[0].get("geometry", {})
        else:
            raise ValueError(f"Unsupported GeoJSON type: {geo_type}")
        if geom.get("type") not in ("Polygon", "MultiPolygon"):
            raise ValueError("ROI geometry must be Polygon or MultiPolygon")
        return v
