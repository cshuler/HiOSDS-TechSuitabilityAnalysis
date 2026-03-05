## MPAT Data Dictionary

Last Updated: 3/1/2026

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
| `net_parcel_area_sqft`       | `float`    | sqft             | Useable parcel area. (`parcel_area_sqft` - `building_fp_total_area_sqft`) |
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
| `depth_to_wt_ft`             | `float`    | ft               | Depth to groundwater. (`land_surface_elev_ft − wt_elev_ft`) |
| `slope_pct`                  | `float`    | percent (%)      | Slope perentage at the parcel analysis point. |
| `sfha_tf`                    | `string`   | —                | Special Flood Hazard Area (coded as A or V flood zone area) equals "T". |
| `analysis_point_source`      | `string`   | —                | Centroid placement logic. |
| `geometry`                   | `geometry` | EPSG:32604       | GeoPackage only: parcel geometry used for spatial joins/exports (multipolygon/polygon features). |
