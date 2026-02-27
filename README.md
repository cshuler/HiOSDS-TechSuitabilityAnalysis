# Hawaii OSDS Technology Suitability Analysis

Parcel-level analysis for evaluating cesspool replacement technologies in Hawaiʻi.

## Current Version

v02

## Structure
```
├── data/
│ └── 03_processed/                    # Final, analysis-ready outputs (versioned)
│ ├── mpat_v02_32604.gpkg              # Master Parcel Attribute Table (spatial; EPSG:32604)
│ └── mpat_v02.csv                     # Master Parcel Attribute Table (tabular)
├── notebooks/                         # Executable analysis workflows
│ ├── 00_download_input_layers.ipynb   # Download/collect source layers 
│ ├── 01_prepare_input_layers.ipynb    # Prepare & validate inputs 
│ ├── 02_built_mpat.ipynb              # Construct MPAT + export to CSV/GPKG
│ └── 03_eda.ipynb                     # Conduct exploratory data analysis
└── src/                               # Helper scripts imported by notebooks
├── download_input_layers.py           # Functions used by 00_download_input_layers.ipynb
├── prepare_input_layers.py            # Functions used by 01_prepare_input_layers.ipynb
├── build_mpat.py                      # Functions used by 02_built_mpat.ipynb
└── eda.py                             # Functions used by 03_eda.ipynb
```

## Outputs

- `data/03_processed/mpat_v02.csv` — Master Parcel Attribute Table (non-spatial)
- `data/03_processed/mpat_v02_32604.gpkg` — Spatial MPAT (EPSG:32604), layer: `mpat_v02`

## MPAT v02 Data Dictionary

**Notes**
- Distances are in feet (ft), areas are in square feet (sqft), elevation is in feet (ft), rainfall is in inches (in).
- The `geometry` column exists only in the GeoPackage (`.gpkg`) output.

| Variable                     | Data type  | Units            | Description |
| ---------------------------- | ---------- | ---------------- | ----------- |
| `island`                     | `string`   | —                | Island name/category associated with the parcel. |
| `tmk`                        | `int`      | —                | Tax Map Key; unique parcel identifier. |
| `osds_qty`                   | `int`      | count            | Number of OSDS/cesspool inventory records associated with the parcel. |
| `bedroom_qty`                | `int`      | count            | Total bedrooms associated with OSDS/cesspools on the parcel. |
| `building_fp_qty`            | `float`    | count            | Count of building footprint features within parcel with cesspools (if available). |
| `parcel_area_sqft`           | `float`    | sqft             | Computed area in square feet of parcels with cesspools. |
| `building_fp_total_area_sqft`| `float`    | sqft             | Total building footprint area per parcel with cesspools. |
| `net_parcel_area_sqft`       | `float`    | sqft             | Parcel area minus building footprint area (where available). |
| `dist_to_sma_ft`             | `float`    | ft               | Distance from the parcel analysis point to the nearest SMA (0 if within SMA). |
| `dist_to_coast_ft`           | `float`    | ft               | Distance from the parcel analysis point to the nearest coastline. |
| `dist_to_streams_ft`         | `float`    | ft               | Distance from the parcel analysis point to the nearest stream. |
| `dist_to_dom_well_ft`        | `float`    | ft               | Distance from the parcel analysis point to the nearest domestic well. |
| `dist_to_mun_well_ft`        | `float`    | ft               | Distance from the parcel analysis point to the nearest municipal well. |
| `ksat_h`                     | `float`    | (source-defined) | Soil hydraulic conductivity attribute (high), from the soils layer. |
| `ksat_l`                     | `float`    | (source-defined) | Soil hydraulic conductivity attribute (low), from the soils layer. |
| `ksat_r`                     | `float`    | (source-defined) | Soil hydraulic conductivity attribute (representative), from the soils layer. |
| `avg_rainfall_in`            | `float`    | in               | Average annual rainfall sampled at the parcel analysis point. |
| `land_surface_elev_ft`       | `float`    | ft               | Land surface elevation sampled at the parcel analysis point (from DEM). |
| `wt_elev_ft`                 | `float`    | ft               | Water table elevation sampled at the parcel analysis point. |
| `depth_to_wt_ft`             | `float`    | ft               | Depth to groundwater (`land_surface_elev_ft − wt_elev_ft`) |
| `slope_pct`                  | `float`    | percent (%)      | Slope perentage at the parcel analysis point. |
| `lot_size_req`               | `string`   | ft               | Lot size requirement category/flag used for technology screening. |
| `depth_to_wt_suitability`    | `float`    | ft               | Depth to water-table suitability metric. |
| `sma_constraints`            | `string`   | ft               | SMA constraints classification. |
| `climate_suitability`        | `string`   | in               | Climate suitability classification (Average rainfall in inches). |
| `slope_req`                  | `string`   | percent (%)      | Slope requirement category/flag used for technology screening. |
| `in_flood_zone`              | `int`      | binary (0/1)     | Parcel analysis point intersects a mapped flood zone. |
| `in_sma`                     | `int`      | binary (0/1)     | Derived from `dist_to_sma_ft` if distance is equal to 0 (Parcel analysis point within SMA). |
| `coast_within_100_ft`        | `int`      | binary (0/1)     | Parcel analysis point is within 100 feet of coastline. |
| `stream_within_50_ft`        | `float`    | ft               | Parcel analysis point is within 50 ft of a stream. |
| `analysis_point_source`      | `string`   | —                | Centroid placement logic. |
| `geometry`                   | `geometry` | EPSG:32604       | GeoPackage only: parcel geometry used for spatial joins/exports (multipolygon/polygon features). |

## Reproducibility Notes

- This workflow requires `arcpy`, so it must be run in a Python environment that includes ArcPy
- Run notebooks in order:
  1. `00_download_input_layers.ipynb`
  2. `01_prepare_input_layers.ipynb`
  3. `02_built_mpat.ipynb`
  4. `03_eda.ipynb`
- The spatial output is projected to EPSG:32604 for analysis and export.
- The CSV is intended for visualizations and non-spatial analysis; use the GeoPackage when you need geometry.