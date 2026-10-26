"""
Export Results Module for Air Pollution Analysis.
Consolidates analytics, summaries, and figures into distributable tables, charts, and metrics.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import logging
import pandas as pd
from src.config import (
    OUTPUTS_CHARTS_DIR,
    OUTPUTS_TABLES_DIR,
    OUTPUTS_METRICS_DIR,
    DATA_PROCESSED_DIR,
)

logger = logging.getLogger("ExportResults")

def summarize_all_outputs():
    """Compiles a manifest of all generated analytical tables, charts, and metrics."""
    manifest = {
        "tables": [str(p.name) for p in OUTPUTS_TABLES_DIR.glob("*.csv")],
        "charts": [str(p.name) for p in OUTPUTS_CHARTS_DIR.glob("*.*")],
        "metrics": [str(p.name) for p in OUTPUTS_METRICS_DIR.glob("*.json")],
    }
    
    summary_path = OUTPUTS_METRICS_DIR / "project_output_manifest.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print("=" * 60)
    print("PROJECT OUTPUTS MANIFEST GENERATED")
    print("=" * 60)
    print(f"Tables ({len(manifest['tables'])}): {manifest['tables']}")
    print(f"Charts ({len(manifest['charts'])}): {manifest['charts']}")
    print(f"Metrics ({len(manifest['metrics'])}): {manifest['metrics']}")
    print(f"Saved to: {summary_path}")
    print("=" * 60)
    return manifest

if __name__ == "__main__":
    summarize_all_outputs()
