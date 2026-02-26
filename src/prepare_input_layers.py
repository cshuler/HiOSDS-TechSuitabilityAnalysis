"""
src/prepare_input_layers.py
Preparation helper functions for MPAT input layers (source inputs > prepared inputs).
"""

from __future__ import annotations

import datetime as _dt
import time
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_step(msg: str) -> None:
    """Print a timestamped log message (12-hour clock, local machine time)."""
    ts = _dt.datetime.now().strftime("%I:%M:%S %p").lstrip("0")
    print(f"[{ts}] {msg}")


def fmt_elapsed(seconds: float) -> str:
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

RASTER_KEYS = {"dem", "watertable", "rainfall", "slope"}


def path_exists(p: str) -> bool:
    return Path(p).exists()


def ensure_dir(p: str | Path) -> None:
    Path(p).mkdir(parents=True, exist_ok=True)


def raster_subfolder_path(prepared_tif_path: str) -> str:
    """Resolve the .tif path inside its named subfolder.

    Example:
      prepared/dem_hi_pacioos_mosaic_32604.tif
      -> prepared/dem_hi_pacioos_mosaic_32604/dem_hi_pacioos_mosaic_32604.tif
    """
    p = Path(prepared_tif_path)
    folder = p.with_suffix("")
    return str(folder / p.name)


def raster_outpath_in_subfolder(prepared_folder: str | Path, raster_name: str) -> str:
    prepared_folder = Path(prepared_folder)
    ensure_dir(prepared_folder)
    return str(prepared_folder / f"{raster_name}.tif")


def prepared_exists(key: str, path: str) -> bool:
    """Check if a prepared output exists (accounts for raster subfolder layout)."""
    if key in RASTER_KEYS:
        return Path(raster_subfolder_path(path)).exists()
    return Path(path).exists()


# ---------------------------------------------------------------------------
# ArcPy helpers
# ---------------------------------------------------------------------------

def epsg_of_dataset(dataset: str, *, arcpy: Any) -> int | None:
    sr = arcpy.Describe(dataset).spatialReference
    if sr is None:
        return None
    code = getattr(sr, "factoryCode", None)
    return int(code) if code not in (None, 0) else None


def gpkg_layer_path(gpkg_path: str, layer_name: str) -> str:
    return str(Path(gpkg_path) / layer_name)


def temp_gpkg_layer(scratch_gpkg: str | Path, layer_name: str) -> str:
    """ArcPy path to a layer inside a GeoPackage."""
    return f"{str(scratch_gpkg)}\\{layer_name}"


def ensure_scratch_gdb(
    temp_dir: str | Path,
    *,
    arcpy: Any,
    name: str = "scratch_vectors.gdb",
) -> str:
    """Create a scratch FileGDB for temp vector outputs."""
    temp_dir = Path(temp_dir)
    ensure_dir(temp_dir)
    gdb_path = str(temp_dir / name)
    if not arcpy.Exists(gdb_path):
        arcpy.management.CreateFileGDB(str(temp_dir), name)
    return gdb_path


def describe_fc(
    fc: str,
    *,
    arcpy: Any,
    label: str | None = None,
    print_fields: bool = True,
) -> None:
    """Print basic QA information for a feature class or layer."""
    prefix = f"{label}: " if label else ""
    desc = arcpy.Describe(fc)
    sr = desc.spatialReference
    count = int(arcpy.management.GetCount(fc)[0])

    print(prefix)
    print(f"  Geometry type: {desc.shapeType}")
    print(f"  CRS: {sr.name} (factoryCode={sr.factoryCode})")
    print(f"  Feature count: {count:,}")

    if print_fields:
        fields = arcpy.ListFields(fc)
        field_names = [f.name for f in fields]
        print(f"  Fields ({len(field_names)}):")
        for name in field_names:
            print(f"    - {name}")


def _rename_field_gpkg_safe(
    fc: str,
    old_name: str,
    new_name: str,
    *,
    arcpy: Any,
) -> None:
    """Rename a field without AlterField (which fails on GPKG layers).

    Workaround: add new field, copy values via UpdateCursor, delete original.
    """
    existing = [f.name for f in arcpy.ListFields(fc)]
    if old_name not in existing or new_name in existing:
        return

    old_field = [f for f in arcpy.ListFields(fc) if f.name == old_name][0]
    arcpy.management.AddField(
        fc, new_name, old_field.type,
        field_length=old_field.length,
        field_alias=new_name,
    )

    with arcpy.da.UpdateCursor(fc, [old_name, new_name]) as cur:
        for row in cur:
            row[1] = row[0]
            cur.updateRow(row)

    arcpy.management.DeleteField(fc, old_name)


# ---------------------------------------------------------------------------
# Vector prep
# ---------------------------------------------------------------------------

def prep_vector_to_gpkg(
    *,
    src_fc: str,
    out_gpkg: str,
    out_layer: str,
    target_epsg: int,
    temp_dir: str | Path,
    arcpy: Any,
    overwrite: bool = True,
) -> str:
    arcpy.env.overwriteOutput = overwrite
    ensure_dir(Path(out_gpkg).parent)

    if not arcpy.Exists(out_gpkg):
        arcpy.management.CreateSQLiteDatabase(out_gpkg, "GEOPACKAGE")

    src_epsg = epsg_of_dataset(src_fc, arcpy=arcpy)
    if src_epsg is None:
        raise ValueError(f"Vector has no readable CRS: {src_fc}")

    if src_epsg != target_epsg:
        scratch_gdb = ensure_scratch_gdb(temp_dir, arcpy=arcpy)
        tmp_fc = str(Path(scratch_gdb) / f"{out_layer}_tmp_{target_epsg}")
        if overwrite and arcpy.Exists(tmp_fc):
            arcpy.management.Delete(tmp_fc)
        arcpy.management.Project(
            in_dataset=src_fc,
            out_dataset=tmp_fc,
            out_coor_system=arcpy.SpatialReference(target_epsg),
        )
        projected_fc = tmp_fc
    else:
        projected_fc = src_fc

    out_layer_path = gpkg_layer_path(out_gpkg, out_layer)
    if overwrite and arcpy.Exists(out_layer_path):
        arcpy.management.Delete(out_layer_path)

    arcpy.conversion.FeatureClassToFeatureClass(
        in_features=projected_fc,
        out_path=out_gpkg,
        out_name=out_layer,
    )
    return out_layer_path


# ---------------------------------------------------------------------------
# Raster prep
# ---------------------------------------------------------------------------

def define_projection_if_missing(
    *,
    raster_path: str,
    assumed_epsg: int,
    temp_dir: str | Path,
    arcpy: Any,
    overwrite: bool = True,
) -> str:
    arcpy.env.overwriteOutput = overwrite
    ensure_dir(temp_dir)
    if epsg_of_dataset(raster_path, arcpy=arcpy) is not None:
        return raster_path
    tmp = str(Path(temp_dir) / f"{Path(raster_path).stem}_defined.tif")
    if overwrite and Path(tmp).exists():
        Path(tmp).unlink()
    arcpy.management.CopyRaster(raster_path, tmp)
    arcpy.management.DefineProjection(tmp, arcpy.SpatialReference(assumed_epsg))
    return tmp


def prep_raster_to_target(
    *,
    src_raster: str,
    prepared_tif: str,
    target_epsg: int,
    temp_dir: str | Path,
    arcpy: Any,
    resampling: str = "BILINEAR",
    assume_src_epsg_if_missing: int | None = None,
    overwrite: bool = True,
) -> str:
    arcpy.env.overwriteOutput = overwrite
    ensure_dir(temp_dir)
    out_raster = raster_outpath_in_subfolder(prepared_tif)

    raster_for_projection = src_raster
    if assume_src_epsg_if_missing is not None:
        raster_for_projection = define_projection_if_missing(
            raster_path=src_raster,
            assumed_epsg=assume_src_epsg_if_missing,
            temp_dir=temp_dir,
            arcpy=arcpy,
            overwrite=overwrite,
        )

    src_epsg = epsg_of_dataset(raster_for_projection, arcpy=arcpy)
    if src_epsg is None:
        raise ValueError(f"Raster has no readable CRS: {src_raster}")

    if src_epsg != target_epsg:
        arcpy.management.ProjectRaster(
            in_raster=raster_for_projection,
            out_raster=out_raster,
            out_coor_system=arcpy.SpatialReference(target_epsg),
            resampling_type=resampling,
        )
    else:
        arcpy.management.CopyRaster(raster_for_projection, out_raster)
    return out_raster


# ---------------------------------------------------------------------------
# Mosaic helper
# ---------------------------------------------------------------------------

def mosaic_dir_to_raster(
    *,
    raster_dir: str,
    out_mosaic: str,
    arcpy: Any,
    overwrite: bool = True,
) -> str:
    arcpy.env.overwriteOutput = overwrite
    tif_paths = sorted([str(p) for p in Path(raster_dir).glob("*.tif")])
    if not tif_paths:
        raise FileNotFoundError(f"No .tif rasters found in: {raster_dir}")

    out_folder = str(Path(out_mosaic).parent)
    out_name = Path(out_mosaic).name
    ensure_dir(out_folder)

    if overwrite and Path(out_mosaic).exists():
        Path(out_mosaic).unlink()

    arcpy.management.MosaicToNewRaster(
        input_rasters=tif_paths,
        output_location=out_folder,
        raster_dataset_name_with_extension=out_name,
        number_of_bands=1,
        pixel_type="32_BIT_FLOAT",
        mosaic_method="FIRST",
        mosaic_colormap_mode="FIRST",
    )
    return out_mosaic


# ---------------------------------------------------------------------------
# Main preprocessing pipeline
# ---------------------------------------------------------------------------

def prepare_source_inputs(
    *,
    source_inputs: dict[str, str],
    prepared_outputs: dict[str, str],
    tempspace: str | Path,
    target_epsg: int,
    arcpy: Any,
    overwrite: bool = True,
) -> dict[str, str]:
    t0_all = time.time()
    tempspace = Path(tempspace)
    ensure_dir(tempspace)

    missing_items = [(k, p) for k, p in prepared_outputs.items() if not prepared_exists(k, p)]
    log_step("Starting prepare_source_inputs()")
    log_step(f"Target CRS: EPSG:{target_epsg}")
    log_step(f"Missing prepared outputs (current total prepared input layers should be 14): {len(missing_items)}")

    if not missing_items:
        log_step("All prepared inputs already exist -> skipping preprocessing")
        log_step(f"Total time: {fmt_elapsed(time.time() - t0_all)}\n")
        return prepared_outputs

    # -- Rasters --
    print("\n" + "-" * 60)
    log_step("Preparing raster inputs")
    print("-" * 60)

    # DEM (dir -> mosaic -> define EPSG:4326 if missing -> project)
    if prepared_exists("dem", prepared_outputs["dem"]):
        log_step("DEM: prepared file exists -> skipping")
    else:
        t0 = time.time()
        dem_tifs = list(Path(source_inputs["dem_dir"]).glob("*.tif"))
        log_step(f"DEM: found {len(dem_tifs)} rasters to mosaic")
        log_step("DEM: mosaicking rasters")
        dem_mosaic = mosaic_dir_to_raster(
            raster_dir=source_inputs["dem_dir"],
            out_mosaic=str(tempspace / "dem_mosaic_tmp.tif"),
            arcpy=arcpy,
            overwrite=overwrite,
        )
        log_step("DEM: projecting to target CRS")
        dem_out = prep_raster_to_target(
            src_raster=dem_mosaic,
            prepared_tif=prepared_outputs["dem"],
            target_epsg=target_epsg,
            temp_dir=tempspace,
            arcpy=arcpy,
            resampling="BILINEAR",
            assume_src_epsg_if_missing=4326,
            overwrite=overwrite,
        )
        log_step(f"DEM: export complete -> {dem_out} ({fmt_elapsed(time.time() - t0)})")

    # Water table (dir -> mosaic -> project)
    if prepared_exists("watertable", prepared_outputs["watertable"]):
        log_step("Water table: prepared file exists -> skipping")
    else:
        t0 = time.time()
        wt_tifs = list(Path(source_inputs["watertable_dir"]).glob("*.tif"))
        log_step(f"Water table: found {len(wt_tifs)} rasters to mosaic")
        log_step("Water table: mosaicking rasters")
        wt_mosaic = mosaic_dir_to_raster(
            raster_dir=source_inputs["watertable_dir"],
            out_mosaic=str(tempspace / "watertable_mosaic_tmp.tif"),
            arcpy=arcpy,
            overwrite=overwrite,
        )
        log_step("Water table: projecting to target CRS")
        wt_out = prep_raster_to_target(
            src_raster=wt_mosaic,
            prepared_tif=prepared_outputs["watertable"],
            target_epsg=target_epsg,
            temp_dir=tempspace,
            arcpy=arcpy,
            resampling="NEAREST",
            overwrite=overwrite,
        )
        log_step(f"Water table: export complete -> {wt_out} ({fmt_elapsed(time.time() - t0)})")

    # Slope (dir -> mosaic -> define EPSG:4326 if missing -> project)
    if prepared_exists("slope", prepared_outputs["slope"]):
        log_step("Slope: prepared file exists -> skipping")
    else:
        t0 = time.time()
        slope_tifs = list(Path(source_inputs["slope_dir"]).glob("*.tif"))
        log_step(f"Slope: found {len(slope_tifs)} rasters to mosaic")
        log_step("Slope: mosaicking rasters")
        slope_mosaic = mosaic_dir_to_raster(
            raster_dir=source_inputs["slope_dir"],
            out_mosaic=str(tempspace / "slope_mosaic_tmp.tif"),
            arcpy=arcpy,
            overwrite=overwrite,
        )
        log_step("Slope: projecting to target CRS")
        slope_out = prep_raster_to_target(
            src_raster=slope_mosaic,
            prepared_tif=prepared_outputs["slope"],
            target_epsg=target_epsg,
            temp_dir=tempspace,
            arcpy=arcpy,
            resampling="BILINEAR",
            assume_src_epsg_if_missing=4326,
            overwrite=overwrite,
        )
        log_step(f"Slope: export complete -> {slope_out} ({fmt_elapsed(time.time() - t0)})")

    # Rainfall (single raster -> project)
    if prepared_exists("rainfall", prepared_outputs["rainfall"]):
        log_step("Rainfall: prepared file exists -> skipping")
    else:
        t0 = time.time()
        log_step("Rainfall: projecting to target CRS")
        rain_out = prep_raster_to_target(
            src_raster=source_inputs["rainfall"],
            prepared_tif=prepared_outputs["rainfall"],
            target_epsg=target_epsg,
            temp_dir=tempspace,
            arcpy=arcpy,
            resampling="BILINEAR",
            overwrite=overwrite,
        )
        log_step(f"Rainfall: export complete -> {rain_out} ({fmt_elapsed(time.time() - t0)})")

    # -- Vectors --
    print("\n" + "-" * 60)
    log_step("Preparing vector inputs")
    print("-" * 60)

    vector_jobs = [
        ("parcels",      "parcels"),
        ("cesspools",    "cesspools"),
        ("coastline",    "coastline"),
        ("sma",          "sma"),
        ("streams",      "streams"),
        ("wells_dom",    "wells_dom"),
        ("wells_mun",    "wells_mun"),
        ("buildings_fps","buildings_fps"),
        ("soils",        "soils"),
        ("flood_zones",  "flood_zones"),
    ]

    for key, layer_name in vector_jobs:
        out_gpkg = prepared_outputs[key]
        if path_exists(out_gpkg):
            log_step(f"{key}: prepared file exists -> skipping")
            continue
        t0 = time.time()
        log_step(f"{key}: projecting to target CRS (if needed)")
        prep_vector_to_gpkg(
            src_fc=source_inputs[key],
            out_gpkg=out_gpkg,
            out_layer=layer_name,
            target_epsg=target_epsg,
            temp_dir=tempspace,
            arcpy=arcpy,
            overwrite=overwrite,
        )
        log_step(f"{key}: export complete ({fmt_elapsed(time.time() - t0)})")

    log_step("Done. Prepared inputs are ready.")
    log_step(f"Total time: {fmt_elapsed(time.time() - t0_all)}\n")
    return prepared_outputs