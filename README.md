# Hawaii OSDS Technology Suitability Analysis

Parcel-level analysis for evaluating cesspool replacement technologies in Hawaiʻi.

## Current Version

v01

## Structure
```
├── data/
│   └── 03_processed/                     # Final, analysis-ready outputs (versioned)
│       ├── mpat_v01_32604.gpkg           # Master Parcel Attribute Table (spatial)
│       └── mpat_v01.csv                  # Master Parcel Attribute Table (tabular)
├── notebooks/                            # Executable analysis workflows
│   ├── 01_prep_mpat_inputs.ipynb         # Prepare & validate spatial inputs (`data/01_inputs/source` → `data/01_inputs/prepared`)
│   ├── 02_build_mpat.ipynb               # Construct MPAT from prepared inputs
│   └── import_building_footprints.ipynb  # Import/processing of building footprint data
└── scripts/                              
    └── download_raw_data.py              # Download and stage raw vendor/source datasets
```

## Outputs

- `mpat_v01.csv` — Master Parcel Attribute Table
- `mpat_v01_32604.gpkg` — Spatial version (EPSG:32604)


## Outputs

- `mpat_v01.csv` — Master Parcel Attribute Table (non-spatial)
- `mpat_v01_32604.gpkg` — Spatial MPAT (EPSG:32604)

## MPAT v01 Variables

| Variable             | Data type | Units        | Description                                                                         |
| -------------------- | --------- | ------------ | ----------------------------------------------------------------------------------- |
| `tmk`                | `string`  | —            | Tax Map Key; unique parcel identifier                                               |
| `n_cesspools`        | `int`     | count        | Number of Class IV cesspools on the parcel                                          |
| `bedroom_sum`        | `float`   | count        | Total number of bedrooms associated with cesspools on the parcel                    |
| `effluent_sum`       | `float`   | gpd          | Total estimated daily effluent volume from cesspools on the parcel                  |
| `nitrogen_sum`       | `float`   | kg/year      | Total estimated annual nitrogen load from cesspools on the parcel                   |
| `phosphorus_sum`     | `float`   | kg/year      | Total estimated annual phosphorus load from cesspools on the parcel                 |
| `area_sqm`           | `float`   | m²           | Parcel area calculated from parcel geometry                                         |
| `elevation_m`        | `float`   | m            | Land surface elevation sampled at parcel centroid                                   |
| `watertable_m`       | `float`   | m            | Water table elevation sampled at parcel centroid                                    |
| `depth_to_water_m`   | `float`   | m            | Depth to groundwater (`elevation_m − watertable_m`; values < 0 constrained to ~1 m) |
| `rainfall_mm`        | `float`   | mm           | Annual rainfall sampled at parcel centroid                                          |
| `dist_to_coast_m`    | `float`   | m            | Geodesic distance from parcel centroid to nearest coastline                         |
| `dist_to_stream_m`   | `float`   | m            | Geodesic distance from parcel centroid to nearest stream                            |
| `dist_to_mun_well_m` | `float`   | m            | Geodesic distance from parcel centroid to nearest municipal well                    |
| `dist_to_dom_well_m` | `float`   | m            | Geodesic distance from parcel centroid to nearest domestic well                     |
| `in_sma`             | `int`     | binary (0/1) | Indicator: parcel intersects Special Management Area                                |


## Method Notes

- All distance-based metrics are calculated from parcel centroids using geodesic distance
- Raster-derived variables represent point samples, not parcel-wide averages
