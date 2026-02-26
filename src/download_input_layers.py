"""
src/download_input_layers.py
Download helper functions for MPAT input layers.
"""

from __future__ import annotations

from pathlib import Path
import requests
import zipfile
import time
import shutil
import subprocess


def download_and_unzip(dataset_id: str, url: str, *, raw_dir: Path) -> None:
    out_folder = raw_dir / dataset_id
    out_folder.mkdir(parents=True, exist_ok=True)

    zip_path = out_folder / f"{dataset_id}.zip"
    print(f"\n=== Downloading ZIP dataset: {dataset_id} ===")
    print(f"Source: {url}")

    start = time.perf_counter()

    resp = requests.get(url)
    resp.raise_for_status()
    zip_path.write_bytes(resp.content)

    print(f"Unzipping {zip_path} into {out_folder}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_folder)

    zip_path.unlink()
    elapsed = time.perf_counter() - start

    print(f"Deleted ZIP file: {zip_path}")
    print(f"{dataset_id}: completed in {elapsed:,.1f} seconds.")


def download_github_folder(
    dataset_id: str,
    api_url: str,
    *,
    raw_dir: Path,
    overwrite: bool = False,
) -> None:
    """
    Download all files in a GitHub folder (recursively) using the GitHub Contents API.
    Saves them into <raw_dir>/<dataset_id>/.
    If overwrite=False, existing files are skipped.
    """
    out_folder = raw_dir / dataset_id
    out_folder.mkdir(parents=True, exist_ok=True)

    print(f"\n=== Downloading GitHub dataset: {dataset_id} ===")
    print(f"Source: {api_url}")

    start = time.perf_counter()

    def _download_folder(url: str, dest: Path) -> None:
        resp = requests.get(url)
        resp.raise_for_status()
        items = resp.json()

        for item in items:
            if item["type"] == "file":
                filename = item["name"]
                dst = dest / filename

                if dst.exists() and not overwrite:
                    print(f"  Skipping existing file: {filename}")
                    continue

                print(f"  Downloading {filename}...")
                file_bytes = requests.get(item["download_url"]).content
                dst.write_bytes(file_bytes)

            elif item["type"] == "dir":
                subfolder = dest / item["name"]
                subfolder.mkdir(exist_ok=True)
                _download_folder(item["url"], subfolder)

    _download_folder(api_url, out_folder)

    elapsed = time.perf_counter() - start
    print(f"Done. Files saved to: {out_folder}")
    print(f"{dataset_id}: completed in {elapsed:,.1f} seconds.")


def pacioos_build_ncss_url(ncss_base: str, dataset_id: str) -> str:
    # NOTE: requests NetCDF; converted to GeoTIFF with gdal_translate.
    return f"{ncss_base}/{dataset_id}?var=elev&horizStride=1&accept=netcdf"


def download_streaming(
    url: str,
    out_path: Path,
    *,
    overwrite: bool = False,
    retries: int = 8,
    chunk_size: int = 1024 * 1024,
    timeout: tuple[int, int] = (30, 300),
) -> None:
    """
    Stream download with optional resume (.part) and retries.
    """
    if out_path.exists() and not overwrite:
        print(f"SKIP (exists): {out_path.name}")
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".part")

    resume_pos = tmp_path.stat().st_size if tmp_path.exists() else 0
    headers: dict[str, str] = {}
    if resume_pos > 0 and not overwrite:
        headers["Range"] = f"bytes={resume_pos}-"

    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, stream=True, timeout=timeout, headers=headers) as r:
                r.raise_for_status()

                mode = "ab" if ("Range" in headers and resume_pos > 0) else "wb"
                with open(tmp_path, mode) as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)

            tmp_path.replace(out_path)
            print(f"DONE: {out_path.name}")
            return

        except Exception as e:
            wait = min(60, 2 ** attempt)
            print(f"ERROR attempt {attempt}/{retries} for {out_path.name}: {e}")
            print(f"Retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"Failed after {retries} attempts: {out_path.name}")


def nc_to_geotiff_and_delete(
    nc_path: Path,
    tif_path: Path,
    *,
    overwrite_tif: bool = False,
) -> None:
    """
    Convert NetCDF:elev -> GeoTIFF using gdal_translate, then delete the NetCDF.
    Requires GDAL CLI (gdal_translate) on PATH.
    """
    if tif_path.exists() and not overwrite_tif:
        print(f"SKIP (tif exists): {tif_path.name}")
        if nc_path.exists():
            nc_path.unlink()
        part = nc_path.with_suffix(nc_path.suffix + ".part")
        if part.exists():
            part.unlink()
        return

    gdal_translate = shutil.which("gdal_translate")
    if not gdal_translate:
        raise RuntimeError(
            "gdal_translate not found on PATH. "
            "Install GDAL (CLI) or switch to a pure-Python conversion approach."
        )

    if not nc_path.exists():
        raise RuntimeError(f"Expected NetCDF does not exist: {nc_path}")

    src = f'NETCDF:"{nc_path}":elev'
    cmd = [
        gdal_translate,
        "-of", "GTiff",
        "-co", "TILED=YES",
        "-co", "COMPRESS=DEFLATE",
        "-co", "PREDICTOR=2",
        "-co", "BIGTIFF=IF_SAFER",
        src,
        str(tif_path),
    ]

    subprocess.run(cmd, check=True)
    print(f"TIFF: {tif_path.name}")
    nc_path.unlink()


def download_pacioos_dems(
    *,
    raw_dir: Path,
    dem_dir: str,
    ncss_base: str,
    dataset_ids: list[str],
    overwrite_tif: bool = False,
    overwrite_nc: bool = False,
) -> None:
    """
    Download PacIOOS NCSS DEM NetCDFs and convert them to GeoTIFFs.
    Saves outputs in <raw_dir>/<dem_dir>/.
    Pass a subset of dataset_ids to download specific islands only.
    """
    out_dir = raw_dir / dem_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== Downloading PacIOOS DEMs -> {out_dir} ===")
    start = time.perf_counter()

    for ds in dataset_ids:
        url = pacioos_build_ncss_url(ncss_base, ds)
        nc_path = out_dir / f"{ds}.nc"
        tif_path = out_dir / f"{ds}.tif"

        print(f"\n--- {ds} ---")

        if tif_path.exists() and not overwrite_tif:
            print(f"SKIP (already have tif): {tif_path.name}")
            part = nc_path.with_suffix(nc_path.suffix + ".part")
            if part.exists():
                part.unlink()
            if nc_path.exists():
                nc_path.unlink()
            continue

        download_streaming(url, nc_path, overwrite=overwrite_nc)
        nc_to_geotiff_and_delete(nc_path, tif_path, overwrite_tif=overwrite_tif)

    elapsed = time.perf_counter() - start
    print(f"\nPacIOOS DEMs: completed in {elapsed/60:,.1f} minutes.")


def main(
    *,
    raw_dir: Path,
    zip_sources: dict[str, str],
    github_datasets: dict[str, str],
    pacioos_dem_dir: str,
    pacioos_ncss_base: str,
    pacioos_dem_dataset_ids: list[str],
    overwrite: bool = False,
    overwrite_dem_tif: bool = False,
    overwrite_dem_nc: bool = False,
) -> None:
    overall_start = time.perf_counter()

    # ZIPs
    for name, url in zip_sources.items():
        download_and_unzip(name, url, raw_dir=raw_dir)

    # GitHub folders
    for dataset_id, api_url in github_datasets.items():
        download_github_folder(dataset_id, api_url, raw_dir=raw_dir, overwrite=overwrite)

    # PacIOOS DEMs
    download_pacioos_dems(
        raw_dir=raw_dir,
        dem_dir=pacioos_dem_dir,
        ncss_base=pacioos_ncss_base,
        dataset_ids=pacioos_dem_dataset_ids,
        overwrite_tif=overwrite_dem_tif,
        overwrite_nc=overwrite_dem_nc,
    )

    overall_elapsed = time.perf_counter() - overall_start
    print(f"\nAll downloads completed in {overall_elapsed/60:,.1f} minutes.")