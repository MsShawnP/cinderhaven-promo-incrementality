"""Method 0 — the pre-period-average baseline estimator.

The naive estimator, pre-registered and frozen in ``docs/estimators.md`` before
any code in this repo loads truth. Shipped **labeled as Method 0** on screen: the
anti-rigging exhibit, expected to be wrong in measurable ways, not a recommended
method. Its known weaknesses (no seasonal adjustment, trend vulnerability, no
comparable-store control, residual pre-period dip contamination) are the point —
see the spec, §5.

Method 0's whole content is its baseline: for each promoted store-week, the
counterfactual is that store's own mean velocity over the 8-week pre-period. Once
that baseline is set, everything downstream — margin, roll-up, ROI, giveaway share,
reconciliation — is the shared machinery in ``common`` (identical for every method).

Blind: consumes only ``pr.load()`` and ``pr.economics()``. No ``truth``, ``config``
or ``constants``; the CI truth gate and the import-ban check both audit it.
"""

import cinderhaven_promo_response as pr

from incrementality.common import (
    assemble,
    attach_margin_cents,
    store_event_pre_period_velocity,
)

# On-screen label. Every figure this estimator produces is the naive pre-period
# average and must say so — no unlabeled naive numbers (DECISIONS.md).
METHOD_LABEL = "Method 0 — pre-period average"

# The one way a Method 0 store-event drops out: too little pre-period history for
# a naive baseline. Stamped on the events it cannot estimate (spec §2.2, §3.5).
EXCLUSION_REASON = "insufficient_pre_period"


def _row_estimates(events, delta, economics):
    """Per estimable promoted row: the pre-period baseline and its margin cents.

    A store-event whose pre-period is insufficient is dropped entirely — no
    baseline, no incremental, no giveaway (spec §2.2). The two 2023-01-28 events
    have <4 pre-period weeks at every store (series start) and fall out here, so
    Method 0 cannot estimate them.
    """
    velocity = store_event_pre_period_velocity(events, delta)
    sufficient = velocity[velocity["is_sufficient"]].copy()
    # Method 0's baseline *is* the pre-period velocity.
    sufficient["baseline_units"] = sufficient["pre_period_velocity"]

    promoted = delta[delta["promo_id"].notna()][
        ["promo_id", "store_id", "sku", "observed_units", "complied"]
    ]
    rows = promoted.merge(
        sufficient[["promo_id", "store_id", "baseline_units"]],
        on=["promo_id", "store_id"],
        how="inner",  # inner: drops rows from insufficient store-events
    )
    rows = attach_margin_cents(rows, events, economics)
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
    """Run Method 0 over all 131 events. Returns an :class:`EstimatorResult`.

    Blind by construction: only ``pr.load()`` and ``pr.economics()`` are read.
    """
    events, delta = pr.load()
    economics = pr.economics()
    rows = _row_estimates(events, delta, economics)
    return assemble(events, rows, METHOD_LABEL, EXCLUSION_REASON)
