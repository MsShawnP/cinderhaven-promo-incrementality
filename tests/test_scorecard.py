"""ROI Scorecard artifact (scorecard/v2) — schema, NA->null, determinism.

The artifact is the seam between the Python pipeline and the front end (PLAN.md
names it the highest-risk seam). v2 carries both methods: a portfolio header per
method and one record per event co-locating both methods' estimates, so the
Scorecard's toggle and the Method 0 -> Method 1 delta are a lookup. These tests pin
its shape, assert it carries only declared estimation fields (no intermediate
volumes, no truth), and that missing values become JSON null, not NaN.
"""

import json

import cinderhaven_promo_response as pr
import pytest

from incrementality import build_scorecard

PORTFOLIO_KEYS = {
    "method_label",
    "n_events",
    "n_estimable",
    "n_lost_money",
    "total_accrued_spend_cents",
    "net_incremental_margin_cents",
    "portfolio_roi",
}

SHARED_EVENT_KEYS = {
    "promo_id",
    "sku",
    "retailer_id",
    "promo_type",
    "plan_status",
    "story_tag",
    "accrued_cost_cents",
    "method0",
    "method1",
}

METHOD0_KEYS = {
    "estimable",
    "exclusion_reason",
    "n_stores_estimable",
    "net_margin_cents",
    "roi",
    "lost_money",
    "subsidized_cost_share",
    "baseline_exceeds_promoted",
}
METHOD1_KEYS = METHOD0_KEYS | {"match_relaxed_share"}


# Building runs both estimators (~14s), so build once for the module and reuse.
@pytest.fixture(scope="module")
def artifact_path(tmp_path_factory):
    return build_scorecard.build(tmp_path_factory.mktemp("scorecard") / "scorecard.json")


@pytest.fixture(scope="module")
def payload(artifact_path):
    return json.loads(artifact_path.read_text(encoding="utf-8"))


def test_artifact_has_the_declared_schema_and_top_level_keys(payload):
    assert payload["schema"] == "scorecard/v2"
    assert set(payload) == {"schema", "package_version", "portfolios", "events"}
    assert payload["package_version"] == pr.__version__


def test_both_method_portfolios_carry_the_cfo_numbers(payload):
    portfolios = payload["portfolios"]
    assert set(portfolios) == {"method0", "method1"}
    for key, portfolio in portfolios.items():
        assert set(portfolio) == PORTFOLIO_KEYS, key
        assert portfolio["n_events"] == 131
        assert portfolio["n_estimable"] == 129  # both methods, this generation
    assert portfolios["method0"]["method_label"].startswith("Method 0")
    assert portfolios["method1"]["method_label"].startswith("Method 1")


def test_every_event_co_locates_both_methods_with_declared_fields(payload):
    # No intermediate columns and no truth leak out — only declared fields, and
    # method1 alone carries the relaxation regime dimension.
    events = payload["events"]
    assert len(events) == 131
    for record in events:
        assert set(record) == SHARED_EVENT_KEYS
        assert set(record["method0"]) == METHOD0_KEYS
        assert set(record["method1"]) == METHOD1_KEYS


def test_money_fields_are_integer_cents_or_null(payload):
    for record in payload["events"]:
        assert isinstance(record["accrued_cost_cents"], int)
        for method in ("method0", "method1"):
            net = record[method]["net_margin_cents"]
            assert net is None or isinstance(net, int)
            assert isinstance(record[method]["n_stores_estimable"], int)


def test_a_method_that_cannot_estimate_an_event_serializes_nulls(payload):
    events = {r["promo_id"]: r for r in payload["events"]}
    # PRE-0097: estimable under Method 0, not under Method 1 (insufficient pool).
    m1 = events["PRE-0097"]["method1"]
    assert m1["estimable"] is False
    assert m1["exclusion_reason"] == "insufficient_comparable_pool"
    assert m1["net_margin_cents"] is None
    assert m1["roi"] is None
    assert m1["match_relaxed_share"] is None
    assert events["PRE-0097"]["method0"]["estimable"] is True


def test_relaxed_share_is_present_and_bounded_where_method1_estimates(payload):
    for record in payload["events"]:
        share = record["method1"]["match_relaxed_share"]
        if record["method1"]["estimable"]:
            assert share is not None and 0.0 <= share <= 1.0
        else:
            assert share is None


def test_artifact_contains_no_nan_or_infinity_tokens(artifact_path):
    raw = artifact_path.read_bytes()
    assert b"NaN" not in raw
    assert b"Infinity" not in raw
    json.loads(raw.decode("utf-8"), parse_constant=_reject)


def _reject(token):
    raise AssertionError(f"non-JSON constant in artifact: {token}")


def test_two_builds_are_byte_identical(artifact_path, tmp_path):
    again = build_scorecard.build(tmp_path / "again.json")
    assert artifact_path.read_bytes() == again.read_bytes()


def test_artifact_uses_lf_newline_and_canonical_serialization(artifact_path):
    raw = artifact_path.read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    payload = json.loads(raw)
    expected = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    assert raw == expected.encode("utf-8")
