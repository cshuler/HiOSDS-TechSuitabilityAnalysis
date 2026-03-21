"""
export_config.py
================
Reads the three rules tabs from HCPT_Matrix_v5.x.xlsx and writes
validated YAML config files for use by the screening engine.

Usage
-----
  # Export baseline config (run from HiOSDS-TechSuitabilityAnalysis root):
  python src/export_config.py --input "path/to/HCPT_Matrix_v5.3.xlsx"

  # Export a named scenario:
  python src/export_config.py --input "path/to/HCPT_Matrix_v5.3.xlsx" ^
      --output config/scenarios/well_setback_750ft/ ^
      --scenario-name "750 ft well setback test"

Notes
-----
- Reads THRESHOLDS, CRITERIA_RULES, and ENDPOINT_RULES tabs.
- Validates operators, threshold references, and action types before writing.
- Exits with an error list if validation fails — no partial output.
- All MPAT field names are in feet/sqft matching the MPAT CSV.
- Run from the HiOSDS-TechSuitabilityAnalysis project root.

Output files
------------
  thresholds.yaml      - numeric regulatory limits
  criteria.yaml        - comparison rules (field / operator / threshold ref)
  endpoint_rules.yaml  - per-system actions for each criterion
  config_manifest.yaml - checksum, timestamp, source version
"""

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml


# ── Tab header rows (0-indexed for pandas) ────────────────────────────────────
# Accounts for banner rows and legend rows in each tab of the spreadsheet.
HEADER_ROWS = {
    "THRESHOLDS":     1,   # row 2 in Excel  (row 1 = banner)
    "CRITERIA_RULES": 6,   # row 7 in Excel  (rows 1-6 = banner + legend)
    "ENDPOINT_RULES": 7,   # row 8 in Excel  (rows 1-7 = banner + legend)
}

VALID_OPERATORS   = {">=", "<=", ">", "<", "==", "= ="}
VALID_ACTIONS_CR  = {"EXCLUDE", "FLAG", "DISPLAY_ONLY", "TRIGGER", "PREFER"}
VALID_ACTIONS_ER  = {"EXCLUDE", "FLAG", "DISPLAY_ONLY", "PREFER", "N/A"}


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_thresholds(xlsx_path: Path) -> pd.DataFrame:
    df = pd.read_excel(
        xlsx_path,
        sheet_name="THRESHOLDS",
        header=HEADER_ROWS["THRESHOLDS"],
    )
    df.columns = [
        "id", "description", "value", "unit",
        "mpat_field", "har_source", "verify_status", "notes",
    ]
    df = df[
        df["id"].notna() &
        ~df["id"].astype(str).str.startswith("HAR") &
        ~df["id"].astype(str).str.startswith("Perc")
    ].copy()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.reset_index(drop=True)


def load_criteria(xlsx_path: Path) -> pd.DataFrame:
    df = pd.read_excel(
        xlsx_path,
        sheet_name="CRITERIA_RULES",
        header=HEADER_ROWS["CRITERIA_RULES"],
    )
    df.columns = [
        "criterion_id", "threshold_id", "parcel_field", "operator",
        "threshold_value", "unit", "action_type", "description",
        "har_source", "verify_status", "notes",
    ]
    df = df[df["criterion_id"].notna()].copy()
    df["operator"] = df["operator"].astype(str).str.strip()
    return df.reset_index(drop=True)


def load_endpoint_rules(xlsx_path: Path) -> pd.DataFrame:
    df = pd.read_excel(
        xlsx_path,
        sheet_name="ENDPOINT_RULES",
        header=HEADER_ROWS["ENDPOINT_RULES"],
    )
    df.columns = [
        "endpoint_id", "criterion_id", "action",
        "pass_condition", "fail_condition", "plain_english", "notes",
    ]
    df = df[df["endpoint_id"].notna()].copy()
    df["action"] = df["action"].astype(str).str.strip().str.upper()
    return df.reset_index(drop=True)


# ── Validation ────────────────────────────────────────────────────────────────

def validate(thresholds, criteria, ep_rules) -> list:
    errors = []
    thresh_ids = set(thresholds["id"].dropna().astype(str))
    crit_ids   = set(criteria["criterion_id"].dropna().astype(str))

    for _, row in thresholds.iterrows():
        if pd.isna(row["value"]):
            if "VERIFY" not in str(row.get("verify_status", "")).upper():
                errors.append(
                    f"THRESHOLDS: '{row['id']}' has non-numeric value "
                    f"and is not marked VERIFY"
                )

    for _, row in criteria.iterrows():
        op = str(row.get("operator", "")).strip()
        if op not in VALID_OPERATORS:
            errors.append(
                f"CRITERIA_RULES: '{row['criterion_id']}' "
                f"has unrecognised operator '{op}'"
            )
        tid = str(row.get("threshold_id", ""))
        if tid and tid not in thresh_ids:
            errors.append(
                f"CRITERIA_RULES: '{row['criterion_id']}' "
                f"references unknown threshold '{tid}'"
            )
        at = str(row.get("action_type", "")).upper()
        if at not in VALID_ACTIONS_CR:
            errors.append(
                f"CRITERIA_RULES: '{row['criterion_id']}' "
                f"has unknown action_type '{at}'"
            )

    for _, row in ep_rules.iterrows():
        cid = str(row.get("criterion_id", ""))
        if cid and cid not in crit_ids:
            errors.append(
                f"ENDPOINT_RULES: endpoint '{row['endpoint_id']}' "
                f"references unknown criterion '{cid}'"
            )
        action = str(row.get("action", "")).upper()
        if action not in VALID_ACTIONS_ER:
            errors.append(
                f"ENDPOINT_RULES: endpoint '{row['endpoint_id']}' "
                f"criterion '{cid}' has unknown action '{action}'"
            )

    return errors


# ── Helpers ───────────────────────────────────────────────────────────────────

def df_to_records(df: pd.DataFrame) -> list:
    """DataFrame to list of dicts, NaN replaced with None."""
    return [
        {k: (None if (isinstance(v, float) and pd.isna(v)) else v)
         for k, v in row.items()}
        for _, row in df.iterrows()
    ]


def file_checksum(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()[:10]


# ── Main export ───────────────────────────────────────────────────────────────

def export(
    xlsx_path: Path,
    output_dir: Path,
    scenario_name: str = "baseline",
    scenario_notes: str = "",
) -> None:

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nReading: {xlsx_path.name}")
    thresholds = load_thresholds(xlsx_path)
    criteria   = load_criteria(xlsx_path)
    ep_rules   = load_endpoint_rules(xlsx_path)

    print(f"  Thresholds:     {len(thresholds):>3} rows")
    print(f"  Criteria rules: {len(criteria):>3} rows")
    print(f"  Endpoint rules: {len(ep_rules):>3} rows")

    print("\nValidating...")
    errors = validate(thresholds, criteria, ep_rules)
    if errors:
        print("\n  VALIDATION ERRORS -- config not written:")
        for e in errors:
            print(f"    {e}")
        sys.exit(1)
    print("  Passed.")

    ts   = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta = {
        "scenario":  scenario_name,
        "notes":     scenario_notes,
        "source":    xlsx_path.name,
        "exported":  ts,
    }

    files = {
        "thresholds.yaml":     {"meta": meta, "thresholds":     df_to_records(thresholds)},
        "criteria.yaml":       {"meta": meta, "criteria":       df_to_records(criteria)},
        "endpoint_rules.yaml": {"meta": meta, "endpoint_rules": df_to_records(ep_rules)},
    }

    print("\nWriting config files:")
    for filename, data in files.items():
        path = output_dir / filename
        path.write_text(
            yaml.dump(data, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(f"  {path}")

    manifest = {
        "scenario":   scenario_name,
        "exported":   ts,
        "source":     xlsx_path.name,
        "checksums":  {f: file_checksum(output_dir / f) for f in files},
        "counts": {
            "thresholds":     len(thresholds),
            "criteria":       len(criteria),
            "endpoint_rules": len(ep_rules),
        },
    }
    manifest_path = output_dir / "config_manifest.yaml"
    manifest_path.write_text(
        yaml.dump(manifest, default_flow_style=False),
        encoding="utf-8",
    )
    print(f"  {manifest_path}")
    print(f"\nDone. Config written to: {output_dir}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Export HCPT Matrix spreadsheet rules to YAML config files."
    )
    ap.add_argument(
        "--input", required=True,
        help="Path to HCPT_Matrix_v5.x.xlsx",
    )
    ap.add_argument(
        "--output", default="config/baseline/",
        help="Output directory (default: config/baseline/)",
    )
    ap.add_argument(
        "--scenario-name", default="baseline",
        help="Scenario name (default: baseline)",
    )
    ap.add_argument(
        "--scenario-notes", default="",
        help="Optional notes about this scenario",
    )
    args = ap.parse_args()

    export(
        xlsx_path=Path(args.input),
        output_dir=Path(args.output),
        scenario_name=args.scenario_name,
        scenario_notes=args.scenario_notes,
    )
