"""The accuracy view — the repo's single, by-name-exempt contact with truth.

This is the ONE module allowed to import ``cinderhaven_promo_response.truth``. It is
exempt from the CI truth gate by name (``tests/test_truth_gate.py``) and by name only,
and nothing imports it (the dependency-direction guard). It scores the two frozen,
blind estimators against quarantined ground truth, following the metrics
pre-registered in ``docs/accuracy-spec.md`` and tagged ``accuracy-preregistration``
before this file existed.

What it publishes is **error metrics derived from truth — never truth values, never
per-row truth, nothing reconstructable** (spec accuracy §7). The artifact's schema is
asserted by a test, because this repo is public and ``.gitignore`` does not protect an
artifact written into the site's data directory by design.
"""

import json
from pathlib import Path

import cinderhaven_promo_response as pr
import numpy as np
import pandas as pd
from cinderhaven_promo_response import truth

from incrementality import method0, method1

SCHEMA = "accuracy/v1"

# A percentage of near-zero is meaningless: events whose |true incremental| is below
# this fixed floor are excluded from the % headline and reported with absolute unit
# error (spec accuracy §4). Fixed in advance, not tuned to results.
FLOOR_UNITS = 1.0

# The four seeded stories: marked and reported separately, never the headline (§5).
STORY_TAGS = ("pantry_trap", "hero_cannibal", "pure_subsidy", "clean_winner")

# Buckets smaller than this are suppressed, so no bucket's error reads back to an
# individual event (spec accuracy §6, §7).
MIN_BUCKET = 5

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = _REPO_ROOT / "web" / "src" / "lib" / "data" / "accuracy.json"


# --- truth-side quantity ----------------------------------------------------


def _truth_causal_per_row(truth_df):
    """Per (sku, store_id, week_ending): the promotion's causal incremental units.

    ``lift - dip + transfer`` in the identity observed = baseline + lift - dip +
    transfer + noise. Noise is excluded — it is not caused by the promotion (spec §2).
    This is the only place a truth column is read; only the aggregated *error* leaves
    this module.
    """
    causal = truth_df["lift_units"] - truth_df["dip_units"] + truth_df["transfer_units"]
    return pd.DataFrame(
        {
            "sku": truth_df["sku"],
            "store_id": truth_df["store_id"],
            "week_ending": truth_df["week_ending"],
            "causal_units": causal,
        }
    )


# --- observed regime features (never truth-derived, spec §6) -----------------


def _depth_band(depth):
    if depth < 0.10:
        return "shallow (<10%)"
    if depth < 0.20:
        return "moderate (10–20%)"
    if depth < 0.30:
        return "deep (20–30%)"
    return "very deep (≥30%)"


def _duration_band(weeks):
    if weeks <= 1:
        return "1 week"
    if weeks == 2:
        return "2 weeks"
    return "3+ weeks"


def _season(month):
    return {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
            6: "Summer", 7: "Summer", 8: "Summer", 9: "Fall", 10: "Fall", 11: "Fall"}[month]


def _relaxed_band(share):
    if pd.isna(share):
        return None
    if share == 0:
        return "full stratum"
    if share >= 1:
        return "fully relaxed"
    return "mixed"


def _observed_features(events):
    """Observed regime labels, one row per event. No truth touched here."""
    duration_weeks = ((events["end_week"] - events["start_week"]).dt.days // 7) + 1
    return pd.DataFrame(
        {
            "promo_id": events["promo_id"],
            "promo_type": events["promo_type"],
            "retailer": events["retailer_id"],
            "product_line": events["sku"].str.split("-").str[1],
            "depth_band": events["discount_depth_pct"].map(_depth_band),
            "duration_band": duration_weeks.map(_duration_band),
            "season": events["start_week"].dt.month.map(_season),
        }
    )


# --- scoring ----------------------------------------------------------------


def _score_method(result, truth_causal):
    """Per-event signed % error for one method, on the rows that method scored.

    Joins the method's estimable store-weeks to truth at the same grain, so error
    measures estimation accuracy, not coverage (spec §2).
    """
    rows = result.rows.merge(truth_causal, on=["sku", "store_id", "week_ending"], how="left")
    rows["est_units"] = rows["observed_units"] - rows["baseline_units"]

    per_event = (
        rows.groupby("promo_id", sort=True)
        .agg(est_incremental=("est_units", "sum"), true_incremental=("causal_units", "sum"))
        .reset_index()
    )
    per_event["abs_unit_error"] = (per_event["est_incremental"] - per_event["true_incremental"]).abs()
    # % error only where the true denominator is meaningfully non-zero.
    defined = per_event["true_incremental"].abs() >= FLOOR_UNITS
    signed = 100.0 * (per_event["est_incremental"] - per_event["true_incremental"]) / per_event["true_incremental"]
    per_event["signed_pct_error"] = np.where(defined, signed, np.nan)
    per_event["pct_defined"] = defined
    return per_event


def _headline(scored):
    defined = scored[scored["pct_defined"]]
    below = scored[~scored["pct_defined"]]
    headline = {
        # One decimal everywhere — false-precision asymmetry reads sloppy on a
        # measurement page (copy-audit 2026-08-22).
        "median_abs_pct_error": round(float(defined["signed_pct_error"].abs().median()), 1),
        "median_signed_pct_error": round(float(defined["signed_pct_error"].median()), 1),
        "n_scored": len(defined),
        "n_below_floor": len(below),
    }
    # Aggregate absolute error for the below-floor bucket, only if it is large enough
    # to not read back to an individual event.
    if len(below) >= MIN_BUCKET:
        headline["median_abs_unit_error_below_floor"] = round(float(below["abs_unit_error"].median()), 3)
    return headline


def _regime(scored_with_features, feature):
    """Median errors per observed-feature bucket, suppressing buckets < MIN_BUCKET."""
    defined = scored_with_features[scored_with_features["pct_defined"]]
    buckets = []
    for label, group in defined.groupby(feature, sort=True):
        if label is None or len(group) < MIN_BUCKET:
            continue  # ≥5 events per bucket, so no bucket reads back to one event
        buckets.append(
            {
                "label": str(label),
                "n_events": len(group),
                "median_abs_pct_error": round(float(group["signed_pct_error"].abs().median()), 1),
                "median_signed_pct_error": round(float(group["signed_pct_error"].median()), 1),
            }
        )
    return buckets


def _method_block(result, truth_causal, features, extra_regimes=None):
    scored = _score_method(result, truth_causal).merge(features, on="promo_id", how="left")
    regimes = {
        feature: _regime(scored, feature)
        for feature in ("promo_type", "retailer", "product_line", "depth_band", "duration_band", "season")
    }
    if extra_regimes:
        for name, column in extra_regimes.items():
            merged = scored.merge(column, on="promo_id", how="left")
            regimes[name] = _regime(merged, name)
    return {"headline": _headline(scored), "regimes": regimes}, scored


def _story_lines(events, scored0, scored1):
    """Per seeded story: each method's signed % error. A percentage, not a truth value
    — true incremental is not published and is not reconstructable from a % alone."""
    s0 = scored0.set_index("promo_id")
    s1 = scored1.set_index("promo_id")
    lines = []
    stories = events[events["story_tag"].isin(STORY_TAGS)]
    for row in stories.itertuples(index=False):
        pid = row.promo_id

        def _pct(scored_indexed, pid=pid):
            if pid not in scored_indexed.index or not bool(scored_indexed.loc[pid, "pct_defined"]):
                return None
            return round(float(scored_indexed.loc[pid, "signed_pct_error"]), 1)

        lines.append(
            {
                "story_tag": row.story_tag,
                "promo_id": pid,
                "method0": {"estimable": pid in s0.index, "signed_pct_error": _pct(s0)},
                "method1": {"estimable": pid in s1.index, "signed_pct_error": _pct(s1)},
            }
        )
    return lines


def compute():
    """Score both methods against truth and return the artifact dict (errors only)."""
    events, delta = pr.load()

    # The one guard that must run before any scoring: refuse observed rows from one
    # generation scored against truth from another (the only silent failure here).
    truth.assert_aligned_with_observed(delta)
    truth_causal = _truth_causal_per_row(truth.load_truth())

    features = _observed_features(events)
    result0 = method0.estimate()
    result1 = method1.estimate()

    # Method 1's match_relaxed_share is an observed regime dimension (spec §6).
    relaxed = result1.events[["promo_id"]].copy()
    relaxed["match_relaxed_share"] = result1.events["match_relaxed_share"].map(_relaxed_band)

    block0, scored0 = _method_block(result0, truth_causal, features)
    block1, scored1 = _method_block(
        result1, truth_causal, features, extra_regimes={"match_relaxed_share": relaxed}
    )

    return {
        "schema": SCHEMA,
        "package_version": pr.__version__,
        "floor_units": FLOOR_UNITS,
        "methods": {"method0": block0, "method1": block1},
        "stories": _story_lines(events, scored0, scored1),
    }


def serialize(payload):
    """Canonical JSON bytes-as-str: sorted keys, fixed separators, trailing LF."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"


def build(out_path=DEFAULT_OUT):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(serialize(compute()).encode("utf-8"))
    return out_path


def main():
    path = build()
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
