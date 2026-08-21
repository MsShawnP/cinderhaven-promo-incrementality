"""Shared estimator machinery — the parts every baseline method holds in common.

A baseline method differs from another **only** in how it computes the per-row
counterfactual ``baseline_units``. Everything downstream of that — the manufacturer
margin at the row grain, the integer-cent quantization, the event roll-up, the
portfolio header, ROI, the giveaway share, and the exact reconciliation — is
identical, and lives here so the two methods cannot drift apart. When the Scorecard
toggles Method 0 against Method 1, the delta must reflect the baseline change and
nothing else; sharing this spine is what guarantees that.

Blind, like everything under ``src/``: no ``truth``/``config``/``constants``. This
module never even loads data — it transforms frames its callers built from the
allowed surface.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

# Baseline pre-period window. P = 8 Saturday weeks strictly before the event start.
# Method 0 uses this as its baseline; Method 1 uses the same window to estimate the
# store volume it matches comparables on (spec §2.2, §3.6). One definition, shared.
PRE_PERIOD_WEEKS = 8
# Insufficiency floor: fewer than M non-promo weeks in the window and the
# store-event's pre-period velocity is not trusted (spec §2.2).
MIN_PRE_PERIOD_WEEKS = 4


@dataclass(frozen=True)
class EstimatorResult:
    """A baseline method's output, at three grains.

    - ``events``: one row per promo_id (all 131), with the per-event decomposition.
      Non-estimable events are present with null estimates, ``estimable=False`` and
      an ``exclusion_reason`` — the denominator is never silently shrunk.
    - ``portfolio``: the CFO header, summed over estimable events only.
    - ``rows``: the estimable promoted rows with their row-grain integer cents, so
      the reconciliation test can re-sum the row grain independently of the event
      grouping (spec §2.7).
    """

    events: pd.DataFrame
    portfolio: dict
    rows: pd.DataFrame


def round_half_even_cents(dollar_values):
    """Dollars (float) -> integer cents, round-half-even at this grain.

    numpy ``rint`` rounds half to the nearest even integer — not half-up, which
    across 1.34M-scale row counts biases totals upward (DECISIONS.md). The result
    is int64; it is the atomic unit the roll-ups sum, so it must be exact.
    """
    return np.rint(np.asarray(dollar_values, dtype="float64") * 100.0).astype("int64")


def store_event_pre_period_velocity(events, delta):
    """Per (promo_id, store_id): mean non-promo velocity in the 8-week pre-period.

    For each promoted store-event, the mean of ``observed_units`` over that store's
    own non-promo weeks in ``[start - P, start)``, plus how many such weeks existed
    and whether that clears ``MIN_PRE_PERIOD_WEEKS``. Method 0 reads this as its
    baseline; Method 1 reads it as the store's volume for comparable matching.
    """
    promoted_cells = (
        delta[delta["promo_id"].notna()][["promo_id", "sku", "store_id"]]
        .drop_duplicates()
        .merge(events[["promo_id", "start_week"]], on="promo_id", how="left")
    )

    # Non-promo history only: a prior promo in the pre-period would inflate the
    # velocity, so promo weeks are excluded (any promo, not just this event's).
    history = delta[delta["promo_id"].isna()][["sku", "store_id", "week_ending", "observed_units"]]

    # start_week and week_ending are Saturday-aligned, so [start - 8wk, start) is
    # exactly the 8 Saturdays before the event.
    window = PRE_PERIOD_WEEKS * pd.Timedelta(weeks=1)
    candidates = promoted_cells.merge(history, on=["sku", "store_id"], how="left")
    in_window = (candidates["week_ending"] < candidates["start_week"]) & (
        candidates["week_ending"] >= candidates["start_week"] - window
    )
    windowed = candidates[in_window]

    agg = (
        windowed.groupby(["promo_id", "store_id"], sort=True)["observed_units"]
        .agg(pre_period_velocity="mean", pre_period_weeks="size")
        .reset_index()
    )

    # Left-join back so store-events with zero in-window history (authorization
    # started at the promo) survive as insufficient rather than vanishing.
    cells = promoted_cells.merge(agg, on=["promo_id", "store_id"], how="left")
    cells["pre_period_weeks"] = cells["pre_period_weeks"].fillna(0).astype("int64")
    cells["is_sufficient"] = cells["pre_period_weeks"] >= MIN_PRE_PERIOD_WEEKS
    return cells[
        ["promo_id", "store_id", "sku", "pre_period_velocity", "pre_period_weeks", "is_sufficient"]
    ]


def attach_margin_cents(rows, events, economics):
    """Add ``incremental_margin_cents`` to rows that already carry ``baseline_units``.

    unit_margin = manufacturer margin = wholesale - COGS per (sku, retailer), from
    economics(); never MSRP (overstates ROI). Incremental units may be negative — a
    promoted week can sell below its counterfactual; the sign is carried, not clamped.
    Quantized once here at the row grain, round-half-even (spec §2.5).
    """
    rows = rows.merge(events[["promo_id", "retailer_id"]], on="promo_id", how="left")
    rows = rows.merge(
        economics[["sku", "retailer_id", "unit_margin"]],
        on=["sku", "retailer_id"],
        how="left",
    )
    incremental_units = rows["observed_units"] - rows["baseline_units"]
    rows["incremental_margin_cents"] = round_half_even_cents(incremental_units * rows["unit_margin"])
    return rows


def assemble(events, rows, method_label, exclusion_reason):
    """Roll estimable rows up to the event grain and the portfolio header.

    ``rows`` are the estimable promoted rows for one method, each carrying
    ``incremental_margin_cents`` (the atomic integer), ``baseline_units``,
    ``observed_units`` and ``complied``. ``exclusion_reason`` is stamped on events
    this method could not estimate (distinct per method — spec §3.5).
    """
    rows = rows.copy()
    # Giveaway share operates on complied rows only — volume that actually sold on
    # discount (spec §2.4). Non-complied rows sold at the regular price.
    rows["baseline_units_complied"] = np.where(rows["complied"], rows["baseline_units"], 0.0)
    rows["observed_units_complied"] = np.where(rows["complied"], rows["observed_units"], 0.0)

    # Event grain. Sum the row-grain integer cents per event; this is the same set
    # of integers the portfolio total sums, so reconciliation is exact (spec §2.7).
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

    # An event is estimable iff at least one of its store-events survived this
    # method's sufficiency rule (Method 0: a usable pre-period; Method 1: a large
    # enough comparable pool). Non-estimable events are shown unranked and carry
    # the reason, never a fabricated number.
    out["estimable"] = out["net_margin_cents"].notna()
    out["exclusion_reason"] = np.where(out["estimable"], None, exclusion_reason)
    out["net_margin_cents"] = out["net_margin_cents"].astype("Int64")
    out["n_stores_estimable"] = out["n_stores_estimable"].fillna(0).astype("int64")

    out["accrued_cost_cents"] = round_half_even_cents(events["accrued_cost"].to_numpy())

    # ROI is a ratio of integer cents, undefined when accrued cost is zero (division
    # by zero has no honest numeric answer, so null — not a sentinel). lost_money
    # uses net < cost and stays defined there (spec §2.6).
    cost = out["accrued_cost_cents"]
    net = out["net_margin_cents"]
    has_cost = out["estimable"] & (cost != 0)
    out["roi"] = np.where(has_cost, net.astype("float64") / cost.astype("float64"), np.nan)

    # Giveaway share (spec §2.4): of the volume sold on discount, the fraction that
    # would have sold anyway at baseline. Undefined when no complied volume sold.
    volume = out["promoted_volume_units"]
    has_volume = out["estimable"] & (volume > 0)
    out["subsidized_cost_share"] = np.where(
        has_volume, out["subsidized_baseline_units"] / volume, np.nan
    )
    # Net-dip flag: share > 1 means the baseline sat above the promoted volume (a
    # dip / pull-forward), so the view annotates rather than showing >100% subsidy.
    out["baseline_exceeds_promoted"] = pd.array(
        np.where(has_volume, out["subsidized_cost_share"] > 1.0, None), dtype="boolean"
    )

    # Lost money: net incremental margin below accrued cost. Defined for every
    # estimable event including zero-cost ones; null for non-estimable events.
    out["lost_money"] = pd.array(np.where(out["estimable"], net < cost, None), dtype="boolean")

    portfolio = _portfolio(out, method_label)
    return EstimatorResult(events=out, portfolio=portfolio, rows=rows)


def _portfolio(events_out, method_label):
    """The CFO header, summed over estimable events only (spec §2.6).

    Every figure is labeled "of N estimable events": a portfolio total that quietly
    shrinks its own denominator is the vendor trick this tool mocks.
    """
    estimable = events_out[events_out["estimable"]]
    total_accrued_spend_cents = int(estimable["accrued_cost_cents"].sum())
    net_incremental_margin_cents = int(estimable["net_margin_cents"].sum())
    return {
        "method_label": method_label,
        "n_events": len(events_out),
        "n_estimable": len(estimable),
        # every estimable event has a defined lost_money (no NA in this subset).
        "n_lost_money": int(estimable["lost_money"].sum()),
        "total_accrued_spend_cents": total_accrued_spend_cents,
        "net_incremental_margin_cents": net_incremental_margin_cents,
        # Denominator is the sum of estimable accrued costs (positive), so defined.
        "portfolio_roi": (
            net_incremental_margin_cents / total_accrued_spend_cents
            if total_accrued_spend_cents
            else None
        ),
    }
