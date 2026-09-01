"""Method 1 vectorized path is bit-identical to the loop oracle.

The production comparable-store estimator is vectorized (``_comparable_rows_vectorized``)
so it survives the v0.6.1 event universe (~5,900 events), where the straightforward
per-event/per-store loop (``_comparable_rows_loop``) takes ~9.5 min. Vectorizing an
estimator is a refactor that must move *no* number: the v0.6.1 re-run has to reflect the
data change, not a scoring change. This test is the gate that guarantees that — the loop
is the reference oracle, and the two must agree on matches, medians, tie-breaks and
empty-pool handling.

Two worlds are checked:

- A synthetic edge-case world (deterministic, version-independent) — a sparse regime like
  the pre-density v0.4.0 world, hand-built to exercise the full stratum, the relaxed
  stratum, the below-floor skip, even-count median ties, the volume-band boundary, and a
  week with no comparable control.
- A sampled slice of the live pinned generation (v0.6.1) — the dense regime at real scale.

Kept permanently in the suite: it runs the slow loop only on a small sample, so it stays
fast while pinning the equivalence forever.
"""

import cinderhaven_promo_response as pr
import numpy as np
import pandas as pd
import pytest

from incrementality import method1


def _assert_bit_identical(events, delta, store_card):
    """Loop and vectorized ``_comparable_rows`` produce the same rows, exactly."""
    loop = method1._comparable_rows_loop(events, delta, store_card)
    vec = method1._comparable_rows_vectorized(events, delta, store_card)

    key = ["promo_id", "store_id", "week_ending"]
    loop = loop.sort_values(key).reset_index(drop=True)
    vec = vec.sort_values(key).reset_index(drop=True)

    assert loop.shape == vec.shape, f"row count differs: loop {len(loop)} vs vec {len(vec)}"
    for col in ["promo_id", "store_id", "sku", "week_ending", "observed_units", "complied"]:
        assert (loop[col].to_numpy() == vec[col].to_numpy()).all(), f"{col} differs"
    # Median baseline must be exactly equal — no float tolerance. Same median over the
    # same control set is the same IEEE-754 value.
    assert np.array_equal(
        loop["baseline_units"].astype("float64").to_numpy(),
        vec["baseline_units"].astype("float64").to_numpy(),
    ), "baseline_units differ (median / tie-break mismatch)"
    assert (
        loop["relaxed"].astype(bool).to_numpy() == vec["relaxed"].astype(bool).to_numpy()
    ).all(), "relaxed stratum flag differs"


# --- synthetic edge-case world ----------------------------------------------

_WEEKS = pd.date_range("2024-01-06", periods=20, freq="7D")  # 20 Saturdays

# Region -> list of (retailer, n_stores). Retailers chosen so FORMAT_CLASS never maps to
# None. R0 has enough conventional stores for a FULL pool and few natural stores (so a
# natural test store must RELAX); R1 is too small for any stratum (the SKIP case).
_LAYOUT = {
    "R0": [("RET-KROGER", 7), ("RET-WHOLEFOODS", 3), ("RET-WALMART", 2)],
    "R1": [("RET-REGIONAL", 4)],
}


def _synthetic_world():
    rng = np.random.default_rng(20260827)

    stores = []
    for region, retailers in _LAYOUT.items():
        for retailer, n in retailers:
            for _ in range(n):
                stores.append((f"S{len(stores):03d}", retailer, region))
    store_card = pd.DataFrame(stores, columns=["store_id", "retailer_id", "region"])
    store_ids = store_card["store_id"].tolist()

    sku = "SKU-A"
    # Full non-promo grid: integer velocities in [1, 8] so even-count medians tie often.
    grid = []
    for s in store_ids:
        for wk in _WEEKS:
            grid.append(
                {
                    "sku": sku,
                    "store_id": s,
                    "week_ending": wk,
                    "observed_units": float(rng.integers(1, 9)),
                    "promo_id": None,
                    "complied": bool(rng.integers(0, 2)),
                }
            )
    delta = pd.DataFrame(grid)

    # Events run in weeks 8..11; the pre-period (weeks 0..7) sets velocities/bands.
    event_weeks = list(_WEEKS[8:12])
    r1 = store_card.loc[store_card["region"] == "R1", "store_id"].tolist()
    conventional_r0 = store_card[
        (store_card["region"] == "R0") & (store_card["retailer_id"] == "RET-KROGER")
    ]["store_id"].tolist()
    natural_r0 = store_card[
        (store_card["region"] == "R0") & (store_card["retailer_id"] == "RET-WHOLEFOODS")
    ]["store_id"].tolist()

    events_spec = [
        # full stratum: two conventional R0 test stores, ~5 conventional controls remain.
        ("PRE-A", conventional_r0[:2]),
        # relaxed stratum: a natural R0 test store — <5 natural, but region pool >= 5.
        ("PRE-B", natural_r0[:1]),
        # skip: an R1 test store — region pool is only 3 controls, below MIN_POOL.
        ("PRE-C", r1[:1]),
    ]

    # Mark promoted (store, week) rows with their promo_id and a lifted observed volume.
    pid_of = {}
    for promo_id, promoted in events_spec:
        for s in promoted:
            for wk in event_weeks:
                pid_of[(s, wk)] = promo_id

    mask = [(row.store_id, row.week_ending) in pid_of for row in delta.itertuples(index=False)]
    delta.loc[mask, "promo_id"] = [
        pid_of[(row.store_id, row.week_ending)]
        for row in delta[mask].itertuples(index=False)
    ]
    # A promoted week sells a bit more than baseline, so incremental is generally positive.
    delta.loc[mask, "observed_units"] = delta.loc[mask, "observed_units"] + 3.0

    # Drop one control's row in one event week to exercise the "no comparable that week"
    # path (a store-event whose baseline is missing for a single week).
    a_control = conventional_r0[3]
    drop = (delta["store_id"] == a_control) & (delta["week_ending"] == event_weeks[1])
    delta = delta[~drop].reset_index(drop=True)

    events = pd.DataFrame(
        {
            "promo_id": [e[0] for e in events_spec],
            "sku": sku,
            "start_week": [event_weeks[0]] * len(events_spec),
            "end_week": [event_weeks[-1]] * len(events_spec),
        }
    )
    return events, delta, store_card


def test_vectorized_matches_loop_on_a_synthetic_edge_case_world():
    events, delta, store_card = _synthetic_world()
    # Guard: the fixture must actually exercise both strata and the skip, or it would
    # prove equivalence only on the easy path.
    vec = method1._comparable_rows_vectorized(events, delta, store_card)
    covered = set(vec["promo_id"])
    assert "PRE-A" in covered, "full-stratum event produced no rows — fixture degenerate"
    assert "PRE-B" in covered, "relaxed-stratum event produced no rows — fixture degenerate"
    assert "PRE-C" not in covered, "skip event should have been excluded (region pool < MIN_POOL)"
    assert bool(vec.loc[vec["promo_id"] == "PRE-B", "relaxed"].iloc[0]) is True
    assert bool(vec.loc[vec["promo_id"] == "PRE-A", "relaxed"].iloc[0]) is False

    _assert_bit_identical(events, delta, store_card)


# --- live sampled slice (the pinned generation) -----------------------------


@pytest.fixture(scope="module")
def live():
    events, delta = pr.load()
    return events, delta, pr.store_card()


def test_vectorized_matches_loop_on_a_live_sample(live):
    events, delta, store_card = live
    # A deterministic spread across the universe, plus every seeded story event. Small
    # enough that the slow loop stays quick; varied enough to hit full and relaxed strata.
    sample = pd.concat(
        [events.iloc[::71].head(80), events[events["story_tag"].notna()]]
    ).drop_duplicates("promo_id")
    _assert_bit_identical(sample, delta, store_card)
