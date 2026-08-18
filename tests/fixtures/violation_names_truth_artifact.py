"""Deliberate violation: reaching truth by path, importing nothing.

This is the realistic leak the import gate alone would miss — both artifacts
are files on one disk, so `pd.read_parquet(...)` reaches quarantined truth
with a clean import list. The gate's second layer checks string literals for
exactly this reason.
"""

import pandas as pd


def estimate_baseline(delta):
    return pd.read_parquet(".cache/truth-quarantine/promo_scan_truth.parquet")
