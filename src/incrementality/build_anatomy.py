"""Pipeline step: write the Event Anatomy artifact — the per-event decomposition.

Anatomy explains the estimate; the accuracy view judges it. So this artifact is
**observed and estimated only — never truth.** For each of the 131 events, under
each method, it carries the volume waterfall the anatomy page draws:

    gross promoted volume  →  subsidized baseline (would have sold anyway)  →  net incremental lift

plus the margin and accrued cost alongside. Dip and transfer are *not* here: they
are the demand response a blind estimator must never see (CLAUDE.md), so the page
shows them as narrative on the story events, and the truth-scored error lives one
click away at /accuracy — never inline. (Dip/transfer as real bars are the next
estimation arc — Option B, tools 1c/1d — see DECISIONS 2026-08-22.)

Same blind surface as build_scorecard: consumes only the estimators, which read
`pr.load()` and `pr.economics()`. No truth.
"""

import json
from pathlib import Path

import cinderhaven_promo_response as pr
import pandas as pd

from incrementality import method0, method1

SCHEMA = "anatomy/v1"

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = _REPO_ROOT / "web" / "src" / "lib" / "data" / "anatomy.json"


def _str(v):
    return None if pd.isna(v) else str(v)


def _int(v):
    return None if pd.isna(v) else int(v)


def _float(v):
    return None if pd.isna(v) else round(float(v), 1)


def _bool(v):
    return None if pd.isna(v) else bool(v)


def _volumes(rows):
    """Per event: gross promoted volume, subsidized baseline, net incremental lift.

    Over the method's estimable promoted rows — all of them, complied or not; the
    waterfall is total promoted volume, not the discounted subset. Net = gross −
    baseline is the same incremental the Scorecard's margin is built from.
    """
    grouped = (
        rows.groupby("promo_id", sort=True)
        .agg(
            gross_promoted_units=("observed_units", "sum"),
            subsidized_baseline_units=("baseline_units", "sum"),
        )
        .reset_index()
    )
    grouped["net_incremental_units"] = (
        grouped["gross_promoted_units"] - grouped["subsidized_baseline_units"]
    )
    return grouped.set_index("promo_id")


def _method_block(result, volumes):
    """One method's per-event anatomy fields, keyed by promo_id."""
    events = result.events.set_index("promo_id")
    block = {}
    for promo_id, ev in events.iterrows():
        vol = volumes.loc[promo_id] if promo_id in volumes.index else None
        # Round gross and baseline, then derive net from the rounded pair so the
        # waterfall reconciles exactly on screen (gross − baseline = net to the
        # displayed decimal), never off by a rounding cent.
        gross = _float(vol["gross_promoted_units"]) if vol is not None else None
        baseline = _float(vol["subsidized_baseline_units"]) if vol is not None else None
        net = round(gross - baseline, 1) if vol is not None else None
        block[promo_id] = {
            "estimable": _bool(ev["estimable"]),
            "exclusion_reason": _str(ev["exclusion_reason"]),
            "gross_promoted_units": gross,
            "subsidized_baseline_units": baseline,
            "net_incremental_units": net,
            "net_margin_cents": _int(ev["net_margin_cents"]),
            "accrued_cost_cents": _int(ev["accrued_cost_cents"]),
            "roi": _float(ev["roi"]),
            "lost_money": _bool(ev["lost_money"]),
            "subsidized_cost_share": _float(ev["subsidized_cost_share"]),
            "baseline_exceeds_promoted": _bool(ev["baseline_exceeds_promoted"]),
            "n_stores_estimable": _int(ev["n_stores_estimable"]),
        }
    return block


def compute():
    """The anatomy artifact as a plain dict of JSON-ready primitives."""
    events, _ = pr.load()
    result0 = method0.estimate()
    result1 = method1.estimate()
    block0 = _method_block(result0, _volumes(result0.rows))
    block1 = _method_block(result1, _volumes(result1.rows))

    # Observed event metadata the page shows around the waterfall. Canonical
    # promo_id order so the artifact is deterministic.
    records = []
    for ev in events.sort_values("promo_id", kind="stable").itertuples(index=False):
        pid = ev.promo_id
        records.append(
            {
                "promo_id": pid,
                "sku": _str(ev.sku),
                "retailer_id": _str(ev.retailer_id),
                "promo_type": _str(ev.promo_type),
                "funding_mechanism": _str(ev.funding_mechanism),
                "plan_status": _str(ev.plan_status),
                "story_tag": _str(ev.story_tag),
                "start_week": ev.start_week.strftime("%Y-%m-%d"),
                "end_week": ev.end_week.strftime("%Y-%m-%d"),
                "n_weeks": int((ev.end_week - ev.start_week).days // 7) + 1,
                "discount_depth_pct": _float(ev.discount_depth_pct * 100),
                "method0": block0[pid],
                "method1": block1[pid],
            }
        )

    return {"schema": SCHEMA, "package_version": pr.__version__, "events": records}


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
