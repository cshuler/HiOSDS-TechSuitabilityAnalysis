from __future__ import annotations
from pathlib import Path
from typing import Optional
import pandas as pd
import arcpy

try:
    from osgeo import gdal
except ImportError:
    gdal = None

def extract_rast_vals(
    in_raster: str,
    in_points: str,
    col_name: str,
    *,
    tmk_field: str = "tmk",
    source_units: str = "m",
    output_units: str = "m",
    nodata_threshold: float = -100,
    label: str | None = None,
    unit_conversions: dict[tuple[str, str], float] | None = None,
) -> pd.DataFrame:
    """Extract raster values at point locations using GDAL.

    Reads point geometries via ArcPy SearchCursor, samples the raster
    with GDAL, applies unit conversion, and returns a DataFrame.
    """
    if gdal is None:
        raise ImportError("GDAL (osgeo) is required for raster extraction.")

    if label:
        print(f"{label}:\n")

    raster_ds = gdal.Open(in_raster)
    if raster_ds is None:
        raise FileNotFoundError(f"Could not open raster: {in_raster}")

    band = raster_ds.GetRasterBand(1)
    gt = raster_ds.GetGeoTransform()
    nodata = band.GetNoDataValue()

    results = []
    n_total = n_nodata = n_oob = 0

    with arcpy.da.SearchCursor(in_points, [tmk_field, "SHAPE@XY"]) as cursor:
        for tmk, (mx, my) in cursor:
            n_total += 1
            px = int((mx - gt[0]) / gt[1])
            py = int((my - gt[3]) / gt[5])

            if not (0 <= px < raster_ds.RasterXSize and 0 <= py < raster_ds.RasterYSize):
                n_oob += 1
                continue

            value = float(band.ReadAsArray(px, py, 1, 1)[0, 0])
            if (nodata is not None and value == nodata) or value < nodata_threshold:
                n_nodata += 1
                continue

            results.append({tmk_field: tmk, col_name: value})

    band = None
    raster_ds = None

    df = pd.DataFrame(results) if results else pd.DataFrame(columns=[tmk_field, col_name])

    # Unit conversion
    # - If units are the same, do nothing (supports unitless rasters like slope_pct)
    # - Otherwise, look up factor in unit_conversions and apply it
    if source_units == output_units:
        factor = 1.0
    else:
        if unit_conversions is None:
            raise ValueError(
                "unit_conversions must be provided when source_units != output_units"
            )

        conversion_key = (source_units, output_units)
        if conversion_key not in unit_conversions:
            raise ValueError(f"No conversion for {source_units} -> {output_units}")

        factor = unit_conversions[conversion_key]
        if not df.empty and factor != 1.0:
            df[col_name] = df[col_name] * factor

    # Summary
    print(f"  Sampled {n_total:,} points against '{Path(in_raster).name}'")
    print(f"  Extracted {len(df):,} valid values for '{col_name}'")
    if factor != 1.0:
        print(f"  Converted {source_units} -> {output_units} (x{factor:.4f})")
    if n_nodata > 0:
        print(f"  Skipped {n_nodata:,} nodata values")
    if n_oob > 0:
        print(f"  Skipped {n_oob:,} out-of-bounds points")
    print()

    return df

def calculate_slope_percentages(
    *,
    in_dem_raster: str,
    out_slope_raster: str | Path,
    output_measurement: str = "PERCENT_RISE",
    method: str = "GEODESIC",
    z_unit: str = "METER",
    use_gpu_if_available: bool = True,
    overwrite: bool = True,
) -> str:
    """
    Create a slope raster from a DEM using ArcPy Spatial Analyst.

    This helper ONLY creates the slope raster (percent rise).
    You can then use your existing `extract_rast_vals()` helper to
    sample slope values at `analysis_fc`.

    Parameters
    ----------
    in_dem_raster : str
        Path to input DEM raster (e.g., 10m DEM) in your target CRS.
    out_slope_raster : str | Path
        Output path for slope raster (GeoTIFF recommended).
    output_measurement : str
        "PERCENT_RISE" (recommended) or "DEGREE" (if needed).
    method : str
        "GEODESIC" (as your supervisor requested) or "PLANAR".
    z_unit : str
        Vertical units of the DEM (your supervisor said meters -> "METER").
    use_gpu_if_available : bool
        Try to use GPU processing when supported by ArcGIS/your install.
    overwrite : bool
        Overwrite the output if it already exists.

    Returns
    -------
    str
        Path to the created slope raster.
    """
    out_slope_raster = str(Path(out_slope_raster))

    # --- Basic checks ---
    if not Path(in_dem_raster).exists():
        raise FileNotFoundError(f"DEM raster not found: {in_dem_raster}")

    # Ensure output folder exists
    Path(out_slope_raster).parent.mkdir(parents=True, exist_ok=True)

    # Spatial Analyst required
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = overwrite

    # Prefer GPU if available (safe to ignore if unsupported)
    if use_gpu_if_available:
        try:
            arcpy.env.processorType = "GPU"
        except Exception:
            pass

    # If overwriting, delete existing output
    if overwrite and (Path(out_slope_raster).exists() or arcpy.Exists(out_slope_raster)):
        try:
            arcpy.management.Delete(out_slope_raster)
        except Exception:
            # If Delete fails for some reason, fall back to filesystem removal
            if Path(out_slope_raster).exists():
                Path(out_slope_raster).unlink()

    # --- Run Slope tool ---
    from arcpy.sa import Slope  # import inside to keep helper lightweight

    slope_ras = Slope(
        in_raster=in_dem_raster,
        output_measurement=output_measurement,  # "PERCENT_RISE"
        method=method,                          # "GEODESIC"
        z_unit=z_unit,                          # "METER"
    )
    slope_ras.save(out_slope_raster)

    return out_slope_raster
