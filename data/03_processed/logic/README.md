## Logic Data Dictionary

Last Updated: 3/5/2026

| Variable            | Data type    | Units          | Description |
| ------------------- | ------------ | -------------- | ----------- |
| `tmk`               | `int`        | —              | Tax Map Key; unique parcel identifier. |
| `class_depth_to_wt` | `category`   | —              | Ordered classification of depth to water table: "Less than 3 ft" / "Between 3 and 6 ft" / "Greater than 6 ft". Null if no valid raster value. |
| `flag_depth_to_wt`  | `Int64`      | binary (0/1)   | 1 if depth to water table < 3 ft (ATU triggered); 0 if ≥ 3 ft (Standard septic tank eligible). Null if depth_to_wt_ft is missing or > 500 ft. |
| `class_lot_size`    | `category`   | —              | Ordered classification of net parcel area: "Less than 10,000 sqft" / "Between 10,000 and 21,000 sqft" / "Greater than 21,000 sqft". Null if net_parcel_area_sqft is missing. |
| `flag_lot_size`     | `Int64`      | binary (0/1)   | 1 if net parcel area < 10,000 sqft (ATU triggered); 0 if ≥ 10,000 sqft (Standard septic tank eligible). Null if net_parcel_area_sqft is missing. |
| `class_slope`       | `category`   | —              | Ordered classification of slope: "Less than 8%" / "Between 8 and 12%" / "Greater than 12%". Null if slope_pct is missing. |
| `flag_slope`        | `Int64`      | binary (0/1)   | 1 if slope > 12% (ATU triggered); 0 if ≤ 12% (Standard septic tank eligible). Null if slope_pct is missing. |
| `flag_count`        | `Int64`      | count (0–3)    | Sum of non-null flags per parcel. Null flags excluded from sum. Range: 0 (no constraints triggered) to 3 (all constraints triggered). |
| `recommendation`    | `category`   | —              | Technology recommendation: "Standard Septic Tank" if flag_count = 0; "ATU NSF 40" if flag_count ≥ 1. Null if all flags are null. |
| `geometry`          | `geometry`   | EPSG:32604     | GeoPackage only: parcel multipolygon geometry. |

### Notes

- All `flag_*` columns use nullable integer (`Int64`) to distinguish between a standard septic tank eligible result (0), a constraint result (1), and data unavailable (null).
- Flag columns export as `float64` in CSV due to NA serialization. Convert back to `Int64` on read.
- `flag_depth_to_wt` is null for 5,404 parcels (72%): 482 parcels had true NoData from the water table raster and were filled with 0.1 m or 0.328084 ft (sea level) per Chris's instruction, plus ~4,921 additional parcels where the raster returned near sea level values at higher elevation locations. Both cases produce depth_to_wt_ft > 500 ft after subtracting from land surface elevation. One additional parcel has a null land surface elevation (outside DEM extent). 
- Deferred variables (SMA, flood zone, coastline, stream proximity, climate) are excluded pending source document verification and feedback.
- `class_*` columns use ordered pandas Categorical dtype and are retained for future multi-technology expansion.