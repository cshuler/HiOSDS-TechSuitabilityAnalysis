# Hawaii OSDS Technology Suitability Analysis

Parcel-level analysis for evaluating cesspool replacement technologies in Hawaiʻi.

## Structure
```
├── data/
│   └── 03_processed/                        # Final, analysis-ready outputs (versioned)
│       ├── logic/                           # Logic model outputs
│       │   ├── 20260301_logic.csv           # Logic model (tabular)
│       │   ├── 20260301_logic_32604.gpkg    # Logic model (spatial; EPSG:32604)
│       │   └── README.md
│       └── mpat/                            # Master Parcel Attribute Table outputs
│           ├── 20260301_mpat.csv            # MPAT (tabular)
│           ├── 20260301_mpat_32604.gpkg     # MPAT (spatial; EPSG:32604)
│           └── README.md
├── notebooks/                               # Executable analysis workflows
│   ├── 00_download_input_layers.ipynb       # Download/collect source layers
│   ├── 01_prepare_input_layers.ipynb        # Prepare & validate inputs
│   ├── 02_build_mpat.ipynb                  # Construct MPAT + export to CSV/GPKG
│   ├── 03_build_logic_model.ipynb           # Build logic model + export to CSV/GPKG
│   └── eda.ipynb                            # Conduct exploratory data analysis
└── src/                                     # Helper scripts imported by notebooks
    ├── download_input_layers.py             # Functions used by 00_download_input_layers.ipynb
    ├── prepare_input_layers.py              # Functions used by 01_prepare_input_layers.ipynb
    ├── build_mpat.py                        # Functions used by 02_build_mpat.ipynb
    └── eda.py                               # Functions used by eda.ipynb
```

## Outputs

<<<<<<< HEAD
- `data/03_processed/logic/20260305_logic.csv` — Logic model dataset (non-spatial)
- `data/03_processed/logic/20260305_logic_32604.gpkg` — Spatial logic model dataset (EPSG:32604), layer: `logic`
=======
- `data/03_processed/logic/20260301_logic.csv` — Logic model dataset (non-spatial)
- `data/03_processed/logic/20260301_logic_32604.gpkg` — Spatial logic model dataset (EPSG:32604), layer: `logic`
    - [`README.md`](https://github.com/cshuler/HiOSDS-TechSuitabilityAnalysis/blob/main/data/03_processed/logic/README.md) 
>>>>>>> baebb7b4b1f16db65ceb7e15f4dc3360611e90a3
- `data/03_processed/mpat/20260301_mpat.csv` — Master Parcel Attribute Table (non-spatial)
- `data/03_processed/mpat/20260301_mpat_32604.gpkg` — Spatial MPAT (EPSG:32604), layer: `mpat`
    - [`README.md`](https://github.com/cshuler/HiOSDS-TechSuitabilityAnalysis/blob/main/data/03_processed/mpat/README.md)

## Reproducibility Notes

- This workflow requires `arcpy`, so it must be run in a Python environment that includes ArcPy
- Run notebooks in order:
  1. `00_download_input_layers.ipynb`
  2. `01_prepare_input_layers.ipynb`
  3. `02_built_mpat.ipynb`
  4. `03_build_logic_model.ipynb`
- The spatial output is projected to EPSG:32604 for analysis and export.
- The CSV is intended for visualizations and non-spatial analysis; use the GeoPackage when you need geometry.
