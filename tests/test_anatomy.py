"""Event Anatomy artifact (anatomy/v1) — observed + estimated, never truth.

Anatomy explains the estimate; accuracy judges it. So this artifact must carry only
observed metadata and the estimators' own outputs — the three-bar volume waterfall,
margin, cost — and never a truth decomposition component (lift / dip / transfer /
noise / causal attribution). Those live in the accuracy path only.
"""

import json

import pytest

from incrementality import build_anatomy

# Truth-only decomposition columns — never in this artifact. (subsidized_baseline is
# the *estimated* baseline, an estimator output, and is allowed; only truth's own
# lift/dip/transfer/noise/attribution are forbidden.)
FORBIDDEN_TRUTH_TOKENS = ("lift_units", "dip_units", "transfer_units", "noise_units", "caused_by")

META_KEYS = {
    "promo_id",
    "sku",
    "retailer_id",
    "promo_type",
    "funding_mechanism",
    "plan_status",
    "story_tag",
    "start_week",
    "end_week",
    "n_weeks",
    "discount_depth_pct",
    "method0",
    "method1",
}

METHOD_KEYS = {
    "estimable",
    "exclusion_reason",
    "gross_promoted_units",
    "subsidized_baseline_units",
    "net_incremental_units",
    "net_margin_cents",
    "accrued_cost_cents",
    "roi",
    "lost_money",
    "subsidized_cost_share",
    "baseline_exceeds_promoted",
    "n_stores_estimable",
}


@pytest.fixture(scope="module")
def artifact_path(tmp_path_factory):
    return build_anatomy.build(tmp_path_factory.mktemp("anatomy") / "anatomy.json")


@pytest.fixture(scope="module")
def payload(artifact_path):
    return json.loads(artifact_path.read_text(encoding="utf-8"))


def test_schema_and_all_131_events(payload):
    assert payload["schema"] == "anatomy/v1"
    assert set(payload) == {"schema", "package_version", "events"}
    assert len(payload["events"]) == 131


def test_artifact_carries_no_truth_decomposition_token(artifact_path):
    raw = artifact_path.read_text(encoding="utf-8")
    for token in FORBIDDEN_TRUTH_TOKENS:
        assert token not in raw, f"anatomy artifact leaks a truth token: {token!r}"


def test_every_event_has_both_methods_and_meta(payload):
    for event in payload["events"]:
        assert set(event) == META_KEYS
        assert set(event["method0"]) == METHOD_KEYS
        assert set(event["method1"]) == METHOD_KEYS


def test_waterfall_reconciles_gross_minus_baseline_equals_net(payload):
    # The three bars must add up on screen: gross − baseline = net, to the displayed
    # decimal, for every estimable event under every method.
    for event in payload["events"]:
        for method in ("method0", "method1"):
            m = event[method]
            if m["estimable"]:
                assert m["gross_promoted_units"] is not None
                assert round(m["gross_promoted_units"] - m["subsidized_baseline_units"], 1) == m[
                    "net_incremental_units"
                ]


def test_non_estimable_events_have_null_volumes_and_a_reason(payload):
    by_id = {e["promo_id"]: e for e in payload["events"]}
    for promo_id in ("PRE-0048", "PRE-0054"):  # the two series-start events (Method 0)
        m0 = by_id[promo_id]["method0"]
        assert m0["estimable"] is False
        assert m0["exclusion_reason"] == "insufficient_pre_period"
        assert m0["gross_promoted_units"] is None
        assert m0["net_incremental_units"] is None


def test_two_builds_are_byte_identical(artifact_path, tmp_path):
    again = build_anatomy.build(tmp_path / "again.json")
    assert artifact_path.read_bytes() == again.read_bytes()


def test_lf_newline_and_no_nan(artifact_path):
    raw = artifact_path.read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    assert b"NaN" not in raw
    assert b"Infinity" not in raw
