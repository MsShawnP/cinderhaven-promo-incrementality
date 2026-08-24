"""Cross-view consistency: the Scorecard and Event Anatomy must never disagree.

The tool's whole thesis is "two numbers that should agree, don't" — measured
estimate against known truth. A tool making that argument cannot itself show the
*same* event, under the *same* method, with a different ROI or giveaway share on
two of its own pages. That is not a rounding nicety; it is the one class of bug
this project can never ship.

The Scorecard and the anatomy page render the same stats through the same view
formatters, so equal *strings* on screen require equal *values* in the artifacts.
This test compares the emitted artifact values directly — not the estimator
outputs — because both artifacts build from the same estimators; the bug this
guards against lives in the artifact writers' converters, not the estimators. It
was a real defect: build_anatomy quantized roi and subsidized_cost_share to one
decimal, so 0.5500704 rendered as 0.55× on the Scorecard and 0.60× in anatomy.

For every event × method × shared stat: anatomy value ≡ scorecard value, exact.
"""

import json

import pytest

from incrementality import build_anatomy, build_scorecard

# Carried once per event on the Scorecard, per-method in anatomy. It is observed
# spend, method-independent, so every anatomy method block must equal the single
# Scorecard event value.
SHARED_EVENT_FIELD = "accrued_cost_cents"


@pytest.fixture(scope="module")
def scorecard(tmp_path_factory):
    path = build_scorecard.build(tmp_path_factory.mktemp("sc") / "scorecard.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {e["promo_id"]: e for e in payload["events"]}


@pytest.fixture(scope="module")
def anatomy(tmp_path_factory):
    path = build_anatomy.build(tmp_path_factory.mktemp("an") / "anatomy.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {e["promo_id"]: e for e in payload["events"]}


def _shared_method_stats(scorecard, anatomy):
    """Per-method stat keys present in BOTH artifacts — computed live, not hardcoded.

    Deriving the set from the artifacts means a stat added to both writers later
    is checked automatically instead of silently escaping the guard.
    """
    a_event = next(iter(anatomy.values()))
    s_event = next(iter(scorecard.values()))
    return set(s_event["method0"]) & set(a_event["method0"])


def test_shared_stats_include_the_ratios_that_broke(scorecard, anatomy):
    # Guard against a vacuous pass: if roi / giveaway share ever fall out of the
    # intersection (a rename, a moved field), this test would compare nothing and
    # still go green. Pin the two stats the original defect hit.
    shared = _shared_method_stats(scorecard, anatomy)
    assert {"roi", "subsidized_cost_share"} <= shared
    assert shared, "no per-method stats shared between the two artifacts"


def test_anatomy_matches_scorecard_for_every_event_method_stat(scorecard, anatomy):
    assert set(scorecard) == set(anatomy), "the two artifacts cover different events"
    shared = _shared_method_stats(scorecard, anatomy)

    mismatches = []
    for promo_id in scorecard:
        s_event = scorecard[promo_id]
        a_event = anatomy[promo_id]
        for method in ("method0", "method1"):
            for stat in shared:
                s_val = s_event[method][stat]
                a_val = a_event[method][stat]
                if s_val != a_val:
                    mismatches.append(f"{promo_id}.{method}.{stat}: scorecard={s_val!r} anatomy={a_val!r}")

    assert not mismatches, "anatomy stats disagree with the Scorecard:\n" + "\n".join(mismatches)


def test_accrued_cost_matches_across_both_views_and_methods(scorecard, anatomy):
    # Method-independent observed spend: the Scorecard's single per-event value must
    # equal both methods' anatomy value.
    mismatches = []
    for promo_id in scorecard:
        expected = scorecard[promo_id][SHARED_EVENT_FIELD]
        for method in ("method0", "method1"):
            got = anatomy[promo_id][method][SHARED_EVENT_FIELD]
            if got != expected:
                mismatches.append(f"{promo_id}.{method}: scorecard={expected!r} anatomy={got!r}")

    assert not mismatches, "accrued cost disagrees across views:\n" + "\n".join(mismatches)
