"""ROI Scorecard artifact — schema, NA->null correctness, and determinism.

The artifact is the integration seam between the Python pipeline and the front
end (PLAN.md names it the highest-risk seam). These tests pin its shape, assert
it carries only declared estimation fields (no intermediate volumes, no truth),
and that missing values become JSON null rather than NaN, which is not valid JSON.
"""

import json

import cinderhaven_promo_response as pr

from incrementality import build_scorecard

DECLARED_EVENT_KEYS = {
    "promo_id",
    "sku",
    "retailer_id",
    "promo_type",
    "plan_status",
    "story_tag",
    "estimable",
    "n_stores_estimable",
    "net_margin_cents",
    "accrued_cost_cents",
    "roi",
    "lost_money",
    "subsidized_cost_share",
    "baseline_exceeds_promoted",
}


def _build_to(tmp_path, name="scorecard.json"):
    return build_scorecard.build(tmp_path / name)


def _payload(tmp_path):
    return json.loads(_build_to(tmp_path).read_text(encoding="utf-8"))


def test_artifact_has_the_declared_schema_and_top_level_keys(tmp_path):
    payload = _payload(tmp_path)
    assert payload["schema"] == "scorecard/v1"
    assert set(payload) == {"schema", "package_version", "portfolio", "events"}
    assert payload["package_version"] == pr.__version__


def test_portfolio_header_carries_the_cfo_numbers(tmp_path):
    portfolio = _payload(tmp_path)["portfolio"]
    assert set(portfolio) == {
        "method_label",
        "n_events",
        "n_estimable",
        "n_lost_money",
        "total_accrued_spend_cents",
        "net_incremental_margin_cents",
        "portfolio_roi",
    }
    assert portfolio["n_events"] == 131
    assert portfolio["n_estimable"] == 129  # the labelled denominator (spec 2.2)
    assert portfolio["method_label"].startswith("Method 0")


def test_every_event_carries_exactly_the_declared_fields(tmp_path):
    # No intermediate columns (subsidized_baseline_units, observed volumes) and
    # no truth leak out through the artifact — it carries only declared fields.
    events = _payload(tmp_path)["events"]
    assert len(events) == 131
    for record in events:
        assert set(record) == DECLARED_EVENT_KEYS


def test_money_fields_are_integer_cents_or_null(tmp_path):
    events = _payload(tmp_path)["events"]
    for record in events:
        for key in ("net_margin_cents", "accrued_cost_cents", "n_stores_estimable"):
            value = record[key]
            assert value is None or isinstance(value, int), f"{key} = {value!r}"
        # accrued cost and store count are always present; only net can be null.
        assert record["accrued_cost_cents"] is not None
        assert record["n_stores_estimable"] is not None


def test_non_estimable_events_serialize_estimates_as_null(tmp_path):
    events = {r["promo_id"]: r for r in _payload(tmp_path)["events"]}
    for promo_id in ("PRE-0048", "PRE-0054"):  # the two series-start events
        record = events[promo_id]
        assert record["estimable"] is False
        assert record["net_margin_cents"] is None
        assert record["roi"] is None
        assert record["lost_money"] is None
        assert record["subsidized_cost_share"] is None


def test_artifact_contains_no_nan_or_infinity_tokens(tmp_path):
    # NaN / Infinity are not valid JSON. Missing values must be null. Python's
    # json.loads tolerates them by default, so check the raw bytes directly.
    raw = _build_to(tmp_path).read_bytes()
    assert b"NaN" not in raw
    assert b"Infinity" not in raw
    # And it parses under strict rules (no parse_constant fallbacks used).
    json.loads(raw.decode("utf-8"), parse_constant=_reject)


def _reject(token):
    raise AssertionError(f"non-JSON constant in artifact: {token}")


def test_two_builds_are_byte_identical(tmp_path):
    # Determinism (spec 5): no wall-clock, no unseeded value, ratios derived from
    # integer cents. Same code + same pinned package -> identical bytes.
    a = _build_to(tmp_path, "a.json").read_bytes()
    b = _build_to(tmp_path, "b.json").read_bytes()
    assert a == b


def test_artifact_uses_lf_newline_and_canonical_serialization(tmp_path):
    raw = _build_to(tmp_path).read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    payload = json.loads(raw)
    expected = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    assert raw == expected.encode("utf-8")
