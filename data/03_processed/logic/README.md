## Logic Data Dictionary

Last Updated: 3/1/2026

**Notes**
- The `geometry` column exists only in the GeoPackage (`.gpkg`) output.

| Variable                     | Data type  | Units            | Description |
| ---------------------------- | ---------- | ---------------- | ----------- |
| `tmk`                        | `int`      | —                | Tax Map Key; unique parcel identifier. |
| `in_flood_zone`              | `int`      | binary (0/1)     | Parcel analysis point intersects a mapped Special Flood Hazard Area. |
| `in_sma`                     | `int`      | binary (0/1)     | Derived from `dist_to_sma_ft` if distance is equal to 0 (Parcel analysis point within SMA). |
| `coast_within_100_ft`        | `int`      | binary (0/1)     | Parcel analysis point is within 100 feet of coastline. |
| `stream_within_50_ft`        | `float`    | ft               | Parcel analysis point is within 50 ft of a stream. |
| `geometry`                   | `geometry` | EPSG:32604       | GeoPackage only: parcel geometry used for spatial joins/exports (multipolygon/polygon features). |
