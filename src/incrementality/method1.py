"""Method 1 — comparable-store baseline.

The second baseline, pre-registered in ``docs/estimators.md`` §3 before this file
existed. Where Method 0 asks "what did this store sell *before* the promo?", Method
1 asks "what did comparable stores sell *during* the promo weeks, while not running
it?" — a concurrent counterfactual that Method 0 is blind to.

For each promoted store-week the baseline is the **median velocity of comparable
control stores in that same week** (spec §3.4). Comparable = carries the SKU, clean
of any promo in the event weeks, and matched to the test store on store identity:
same ``region`` (``store_card()``) + same **format class** (a consumer JUDGMENT
mapping, §3.2, since ``store_card()`` ships no format) + observed volume band. The
pool is drawn **cross-banner** because same-banner control pools are empty for ~80%
of events (§3.7). A store-event with fewer than ``MIN_POOL`` comparables is excluded
with ``insufficient_comparable_pool``, visibly, never given a thin-pool median.

Once the baseline is set, margin, roll-up, ROI, giveaway share and reconciliation
are the shared ``common`` machinery — identical to Method 0, so the Scorecard toggle
compares like with like.

Blind: consumes only ``pr.load()``, ``pr.economics()`` and ``pr.store_card()``. No
``truth``/``config``/``constants``.
"""

import cinderhaven_promo_response as pr
import pandas as pd

from incrementality.common import (
    MIN_PRE_PERIOD_WEEKS,
    PRE_PERIOD_WEEKS,
    assemble,
    attach_margin_cents,
)

METHOD_LABEL = "Method 1 — comparable-store"

# The one way a Method 1 store-event drops out: too few comparable controls for a
# trustworthy median (spec §3.5). Distinct from Method 0's insufficient_pre_period.
EXCLUSION_REASON = "insufficient_comparable_pool"

# Format class — a consumer-side JUDGMENT mapping from retailer, because store_card()
# ships no store_format (spec §3.2, DECISIONS.md). Coarser than banner on purpose:
# two natural banners share a class, which is what makes the cross-banner pool usable.
FORMAT_CLASS = {
    "RET-COSTCO": "club",
    "RET-WALMART": "supercenter",
    "RET-WHOLEFOODS": "natural",
    "RET-SPROUTS": "natural",
    "RET-KROGER": "conventional",
    "RET-REGIONAL": "conventional",
}

# Provisional, tuned against pool size (observed), never against error (truth), and
# logged before first scoring (spec §3.5). MIN_POOL: fewest comparables a median is
# allowed to rest on. VOLUME_BAND_FACTOR: a control's pre-period velocity must fall
# within [v / f, v * f] of the test store's to count as the same volume band.
MIN_POOL = 5
VOLUME_BAND_FACTOR = 2.0


def _store_attributes(store_card):
    """store_id -> (region, format_class). Region is package-assigned identity
    (never joined to platform data — DECISIONS.md); format_class is the JUDGMENT map."""
    sc = store_card.copy()
    sc["format_class"] = sc["retailer_id"].map(FORMAT_CLASS)
    return (
        dict(zip(sc["store_id"], sc["region"])),
        dict(zip(sc["store_id"], sc["format_class"])),
    )


def _comparable_rows(events, delta, store_card):
    """Estimable promoted rows with a per-week comparable-median ``baseline_units``.

    Matches each store-event by the §3.3 two-stratum hierarchy — the tightest
    stratum that clears ``MIN_POOL``: full (region + format class + volume band),
    else relaxed (region + volume band, format dropped). Each emitted row carries
    ``relaxed`` (the store-event's stratum) so the coverage/relaxation can be rolled
    up to an observed per-event regime dimension (§3.3). Where the test store has no
    usable pre-period the volume band is simply not applied (no band to apply); the
    baseline itself never needs the test store's own pre-period.
    """
    region, fmt = _store_attributes(store_card)
    window = PRE_PERIOD_WEEKS * pd.Timedelta(weeks=1)
    by_sku = {sku: g for sku, g in delta.groupby("sku", sort=False)}

    out_rows = []

    for ev in events.itertuples(index=False):
        g = by_sku.get(ev.sku)
        if g is None:
            continue
        weeks = set(pd.date_range(ev.start_week, ev.end_week, freq="7D"))

        # Pre-period velocity per store over [start - 8wk, start), non-promo weeks.
        pre = g[
            (g["week_ending"] < ev.start_week)
            & (g["week_ending"] >= ev.start_week - window)
            & (g["promo_id"].isna())
        ]
        pre_agg = pre.groupby("store_id")["observed_units"].agg(["mean", "size"])
        velocity = pre_agg["mean"].to_dict()
        pre_weeks = pre_agg["size"].to_dict()

        promoted_stores = set(g.loc[g["promo_id"] == ev.promo_id, "store_id"].unique())

        # Rows inside the event weeks; a store with ANY promo in those weeks is not a
        # clean control (covers this event's promoted stores and any other overlap).
        during = g[g["week_ending"].isin(weeks)]
        promo_in_weeks = set(during.loc[during["promo_id"].notna(), "store_id"].unique())
        clean = during[~during["store_id"].isin(promo_in_weeks)]
        clean_stores = set(clean["store_id"].unique())

        for test_store in sorted(promoted_stores):
            region_t = region.get(test_store)
            format_t = fmt.get(test_store)
            if region_t is None or format_t is None:
                continue

            # Base candidates: clean same-region controls, not the test store or a
            # promoted store. Volume band applied only when the test store has a
            # usable pre-period (§3.6); a control needs its own usable pre-period to
            # be band-comparable (the pre_weeks check short-circuits before velocity).
            base = {
                c
                for c in clean_stores
                if c != test_store and c not in promoted_stores and region.get(c) == region_t
            }
            has_volume = pre_weeks.get(test_store, 0) >= MIN_PRE_PERIOD_WEEKS
            if has_volume:
                lo = velocity[test_store] / VOLUME_BAND_FACTOR
                hi = velocity[test_store] * VOLUME_BAND_FACTOR
                region_pool = {
                    c
                    for c in base
                    if pre_weeks.get(c, 0) >= MIN_PRE_PERIOD_WEEKS and lo <= velocity[c] <= hi
                }
            else:
                region_pool = base
            full_pool = {c for c in region_pool if fmt.get(c) == format_t}

            # Tightest stratum that clears MIN_POOL (§3.3). Below the relaxed
            # stratum, the store-event is excluded (insufficient_comparable_pool).
            if len(full_pool) >= MIN_POOL:
                controls, relaxed = full_pool, False
            elif len(region_pool) >= MIN_POOL:
                controls, relaxed = region_pool, True
            else:
                continue

            # Per-week baseline = median of the comparable controls that same week.
            control_rows = clean[clean["store_id"].isin(controls)]
            week_median = control_rows.groupby("week_ending")["observed_units"].median()

            test_rows = g[(g["store_id"] == test_store) & (g["promo_id"] == ev.promo_id)]
            for r in test_rows.itertuples(index=False):
                baseline = week_median.get(r.week_ending)
                if baseline is None:
                    continue  # no comparable control sold that week — rare
                out_rows.append(
                    {
                        "promo_id": ev.promo_id,
                        "store_id": test_store,
                        "sku": ev.sku,
                        "observed_units": r.observed_units,
                        "baseline_units": baseline,
                        "complied": r.complied,
                        "relaxed": relaxed,
                    }
                )

    return pd.DataFrame(
        out_rows,
        columns=["promo_id", "store_id", "sku", "observed_units", "baseline_units", "complied", "relaxed"],
    )


def estimate():
    """Run Method 1 over all 131 events. Returns an :class:`EstimatorResult`.

    Blind by construction: only ``pr.load()``, ``pr.economics()`` and
    ``pr.store_card()`` are read.
    """
    events, delta = pr.load()
    economics = pr.economics()
    store_card = pr.store_card()

    rows = _comparable_rows(events, delta, store_card)

    # Per-event relaxed share (observed regime dimension, §3.3): of the event's
    # estimable store-events, the fraction matched at the relaxed stratum (format
    # class dropped). Computed before the margin join, from the store-event grain.
    per_store_event = rows.drop_duplicates(["promo_id", "store_id"])
    relaxed_share = per_store_event.groupby("promo_id")["relaxed"].mean()

    rows = attach_margin_cents(rows, events, economics)
    rows = rows[
        [
            "promo_id",
            "store_id",
            "sku",
            "incremental_margin_cents",
            "baseline_units",
            "observed_units",
            "complied",
        ]
    ]

    result = assemble(events, rows, METHOD_LABEL, EXCLUSION_REASON)
    # Carried into the artifact: null for non-estimable events, else in [0, 1].
    result.events["match_relaxed_share"] = pd.array(
        result.events["promo_id"].map(relaxed_share), dtype="Float64"
    )
    return result
