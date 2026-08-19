"""Method 0 — the pre-period-average baseline estimator.

The naive estimator, pre-registered and frozen in ``docs/estimators.md`` before
any code in this repo loads truth. It is shipped **labeled as Method 0** on
screen: the anti-rigging exhibit, expected to be wrong in measurable ways, not a
recommended method. Its known weaknesses (no seasonal adjustment, trend
vulnerability, no comparable-store control, residual pre-period dip
contamination) are the point — see the spec, section 4.

Blindness: this module is estimation code and stays blind. It consumes exactly
``pr.load()`` (observed layer) and ``pr.economics()`` (the product price card).
No ``truth``, no ``config``, no ``constants`` — the CI truth gate and this repo's
own import-ban check both audit it. The only demand-side quantity it ever sees is
``observed_units``; the baseline it compares against is *estimated* from the
pre-period, never read from the generator.

Money is integer cents, quantized once at the row grain with round-half-even
(numpy ``rint`` is round-half-to-even). That per-row integer is the atomic unit
everything downstream sums, so the portfolio reconciliation ties exactly with no
float tolerance (spec section 2.7). Ratios (ROI, giveaway share) are derived from
those integer cents and are therefore deterministic too.
"""

from dataclasses import dataclass

import cinderhaven_promo_response as pr
import numpy as np
import pandas as pd

# On-screen label. Every figure this estimator produces is the naive pre-period
# average and must say so — no unlabeled naive numbers (DECISIONS.md).
METHOD_LABEL = "Method 0 — pre-period average"

# Baseline window. P = 8 Saturday weeks strictly before the event start.
# Deliberately short: a longer window starts absorbing seasonality, which
# Method 0 explicitly does NOT correct for — a naive baseline that quietly
# de-seasonalizes would not be naive (spec section 2.2, a logged judgment call).
PRE_PERIOD_WEEKS = 8
# Insufficiency floor: fewer than M non-promo weeks in the window and the
# store-event gets no fabricated baseline — it is excluded from the incremental
# computation (spec section 2.2).
MIN_PRE_PERIOD_WEEKS = 4


@dataclass(frozen=True)
class Method0Result:
    """The estimator's output, at three grains.

    - ``events``: one row per promo_id (all 131), with the per-event
      decomposition. Non-estimable events are present with null estimates and
      ``estimable=False`` — the denominator is never silently shrunk.
    - ``portfolio``: the CFO header, summed over estimable events only.
    - ``rows``: the sufficient promoted rows with their row-grain integer cents.
      Kept so the reconciliation test can re-sum the row grain independently of
      the event grouping (spec section 2.7).
    """

    events: pd.DataFrame
    portfolio: dict
    rows: pd.DataFrame


def _round_half_even_cents(dollar_values):
    """Dollars (float) -> integer cents, round-half-even at this grain.

    numpy ``rint`` rounds half to the nearest even integer — not half-up, which
    across 1.34M-scale row counts biases totals upward (DECISIONS.md). The result
    is int64; it is the atomic unit the roll-ups sum, so it must be exact.
    """
    return np.rint(np.asarray(dollar_values, dtype="float64") * 100.0).astype("int64")


def _store_event_baselines(events, delta):
    """Per (promo_id, store_id) pre-period baseline and its sufficiency flag.

    For each promoted store-event, the baseline is the mean of ``observed_units``
    over that store's own non-promo weeks in ``[start - P, start)``. A store-event
    with fewer than M such weeks is marked insufficient and carries no baseline.
    """
    promoted_cells = (
        delta[delta["promo_id"].notna()][["promo_id", "sku", "store_id"]]
        .drop_duplicates()
        .merge(events[["promo_id", "start_week"]], on="promo_id", how="left")
    )

    # Non-promo history only: a prior promo sitting in the pre-period would
    # inflate the baseline, so promo weeks are excluded from the window (any
    # promo, not just this event's).
    history = delta[delta["promo_id"].isna()][["sku", "store_id", "week_ending", "observed_units"]]

    # Attach every candidate history row to the store-events that share its
    # (sku, store_id), then keep only rows inside that event's pre-period window.
    # start_week and week_ending are Saturday-aligned, so [start - 8wk, start)
    # is exactly the 8 Saturdays before the event.
    window = PRE_PERIOD_WEEKS * pd.Timedelta(weeks=1)
    candidates = promoted_cells.merge(history, on=["sku", "store_id"], how="left")
    in_window = (
        (candidates["week_ending"] < candidates["start_week"])
        & (candidates["week_ending"] >= candidates["start_week"] - window)
    )
    windowed = candidates[in_window]

    agg = (
        windowed.groupby(["promo_id", "store_id"], sort=True)["observed_units"]
        .agg(baseline_units="mean", pre_period_weeks="size")
        .reset_index()
    )

    # Left-join back so store-events with zero in-window history (authorization
    # started at the promo) survive as insufficient rather than vanishing.
    cells = promoted_cells.merge(agg, on=["promo_id", "store_id"], how="left")
    cells["pre_period_weeks"] = cells["pre_period_weeks"].fillna(0).astype("int64")
    cells["is_sufficient"] = cells["pre_period_weeks"] >= MIN_PRE_PERIOD_WEEKS
    return cells[["promo_id", "store_id", "sku", "baseline_units", "pre_period_weeks", "is_sufficient"]]


def _row_estimates(events, delta, economics):
    """Per sufficient promoted row: incremental margin cents and giveaway cents.

    Rows whose store-event is insufficient are dropped entirely — no baseline,
    no incremental, no giveaway (spec section 2.2).
    """
    cells = _store_event_baselines(events, delta)
    sufficient = cells[cells["is_sufficient"]]

    promoted = delta[delta["promo_id"].notna()][
        ["promo_id", "store_id", "sku", "observed_units", "complied"]
    ]
    rows = promoted.merge(
        sufficient[["promo_id", "store_id", "baseline_units"]],
        on=["promo_id", "store_id"],
        how="inner",  # inner: drops rows from insufficient store-events
    )

    # unit_margin = manufacturer margin = wholesale - COGS, per (sku, retailer),
    # from economics(). Never MSRP (overstates ROI — the package's own warning).
    # Retailer comes from the event, which is authoritative for the promo.
    rows = rows.merge(events[["promo_id", "retailer_id"]], on="promo_id", how="left")
    rows = rows.merge(
        economics[["sku", "retailer_id", "unit_margin"]],
        on=["sku", "retailer_id"],
        how="left",
    )

    # Incremental units may be negative — a promoted week can sell below its
    # pre-period average (dip, cannibalization). The sign is carried, not clamped.
    incremental_units = rows["observed_units"] - rows["baseline_units"]
    rows["incremental_margin_cents"] = _round_half_even_cents(incremental_units * rows["unit_margin"])

    # baseline_units, observed_units and complied are carried through for the
    # giveaway share (spec section 2.4). The share is a volume ratio computed at
    # the event grain over complied rows — see estimate() — so no per-row money
    # quantization happens here.
    return rows[
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


def estimate():
    """Run Method 0 over all 131 events. Returns a :class:`Method0Result`.

    Blind by construction: only ``pr.load()`` and ``pr.economics()`` are read.
    """
    events, delta = pr.load()
    economics = pr.economics()

    rows = _row_estimates(events, delta, economics)

    # Giveaway share operates on complied rows only — volume that actually sold on
    # discount (spec section 2.4). Non-complied promoted rows sold at the regular
    # price, so they are not part of "the volume sold on discount."
    rows["baseline_units_complied"] = np.where(rows["complied"], rows["baseline_units"], 0.0)
    rows["observed_units_complied"] = np.where(rows["complied"], rows["observed_units"], 0.0)

    # Event grain. Sum the row-grain integer cents per event; this is the same
    # set of integers the portfolio total sums, so reconciliation is exact.
    per_event = (
        rows.groupby("promo_id", sort=True)
        .agg(
            net_margin_cents=("incremental_margin_cents", "sum"),
            subsidized_baseline_units=("baseline_units_complied", "sum"),
            promoted_volume_units=("observed_units_complied", "sum"),
            n_stores_estimable=("store_id", "nunique"),
        )
        .reset_index()
    )

    # Start from all 131 events so non-estimable ones are present, not dropped.
    out = events[["promo_id", "sku", "retailer_id", "promo_type", "plan_status", "story_tag"]].copy()
    out = out.merge(per_event, on="promo_id", how="left")

    # An event is estimable iff it has at least one sufficient store-event.
    # The two 2023-01-28 events have <4 pre-period weeks at every store (series
    # start) and fall out here — shown unranked, never given a fabricated number.
    out["estimable"] = out["net_margin_cents"].notna()
    out["net_margin_cents"] = out["net_margin_cents"].astype("Int64")
    out["n_stores_estimable"] = out["n_stores_estimable"].fillna(0).astype("int64")

    out["accrued_cost_cents"] = _round_half_even_cents(events["accrued_cost"].to_numpy())

    # ROI and giveaway share are ratios of integer cents. Undefined when accrued
    # cost is zero (3 events: two phantoms and one executed that accrued nothing)
    # — division by zero has no honest numeric answer, so ROI is null there. The
    # lost-money test below does not need ROI and stays defined. Flagged for a
    # DECISIONS re-run note: the frozen spec's section 2.6 formula divides by
    # accrued_cost without addressing the zero case.
    cost = out["accrued_cost_cents"]
    net = out["net_margin_cents"]
    has_cost = out["estimable"] & (cost != 0)
    out["roi"] = np.where(has_cost, net.astype("float64") / cost.astype("float64"), np.nan)

    # Giveaway share (spec section 2.4, corrected 2026-08-19 to a volume ratio —
    # see DECISIONS.md). Of the volume sold on discount, the fraction that would
    # have sold anyway at baseline. Discount depth is constant within an event, so
    # this volume ratio equals the discount-weighted dollar share; for scan-funded
    # events (accrued cost = rate x promoted units) it also equals baseline's share
    # of accrued trade dollars, which is where the "% of trade dollars" copy is
    # dimensionally honest. Undefined when no complied volume sold (phantoms).
    volume = out["promoted_volume_units"]
    has_volume = out["estimable"] & (volume > 0)
    out["subsidized_cost_share"] = np.where(
        has_volume, out["subsidized_baseline_units"] / volume, np.nan
    )
    # Net-dip annotation: share > 1 means baseline exceeded the promoted volume —
    # the naive baseline sits above what sold during the promo (a dip / pull-forward
    # artifact). Flagged so the view can annotate rather than the number reading as
    # a nonsensical ">100% subsidy."
    out["baseline_exceeds_promoted"] = pd.array(
        np.where(has_volume, out["subsidized_cost_share"] > 1.0, None), dtype="boolean"
    )

    # Lost money: net incremental margin below accrued cost. Defined for every
    # estimable event including the zero-cost ones (net < 0 there). Null for
    # non-estimable events, which have no net.
    out["lost_money"] = pd.array(
        np.where(out["estimable"], net < cost, None), dtype="boolean"
    )

    portfolio = _portfolio(out)
    return Method0Result(events=out, portfolio=portfolio, rows=rows)


def _portfolio(events_out):
    """The CFO header, summed over estimable events only (spec section 2.6).

    Every figure is labeled "of N estimable events": a portfolio total that
    quietly shrinks its own denominator is the vendor trick this tool mocks.
    """
    estimable = events_out[events_out["estimable"]]
    total_accrued_spend_cents = int(estimable["accrued_cost_cents"].sum())
    net_incremental_margin_cents = int(estimable["net_margin_cents"].sum())
    return {
        "method_label": METHOD_LABEL,
        "n_events": len(events_out),
        "n_estimable": len(estimable),
        # every estimable event has a defined lost_money (no NA in this subset),
        # so summing the boolean column counts the True values.
        "n_lost_money": int(estimable["lost_money"].sum()),
        "total_accrued_spend_cents": total_accrued_spend_cents,
        "net_incremental_margin_cents": net_incremental_margin_cents,
        # Portfolio ROI: denominator is the sum of estimable accrued costs, which
        # is positive (many events cost more than zero), so this ratio is defined.
        "portfolio_roi": (
            net_incremental_margin_cents / total_accrued_spend_cents
            if total_accrued_spend_cents
            else None
        ),
    }
