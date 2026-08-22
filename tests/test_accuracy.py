"""Accuracy artifact (accuracy/v1) — error metrics only, never truth.

This repo is public and `.gitignore` does not protect an artifact written into the
site's data directory by design (DECISIONS.md). So the one thing these tests must
guarantee is that the accuracy artifact carries **error statistics derived from
truth and nothing else** — no truth value, no per-row truth, nothing a reader could
invert back to a truth quantity. Plus the pre-registered shape: both methods side by
side, ≥5 events per bucket, observed-only regime labels, stories separated.

This test imports `accuracy` (which imports truth); it lives in `tests/`, which the
truth gate does not scan — the gate scans `src/`, where only `accuracy.py` is exempt.
"""

import json

import pytest

from incrementality import accuracy

# Truth column names that must never appear anywhere in the artifact — as a key or in
# a way that exposes a value. The artifact holds percentages, counts and observed
# labels only.
FORBIDDEN_SUBSTRINGS = (
    "baseline_units",
    "lift_units",
    "dip_units",
    "transfer_units",
    "noise_units",
    "caused_by",
    "true_incremental",
    "est_incremental",
    "truth",
)

HEADLINE_ALLOWED = {
    "median_abs_pct_error",
    "median_signed_pct_error",
    "n_scored",
    "n_below_floor",
    "median_abs_unit_error_below_floor",  # only when the below-floor bucket is ≥5
}

OBSERVED_REGIMES = {
    "promo_type",
    "retailer",
    "product_line",
    "depth_band",
    "duration_band",
    "season",
    "match_relaxed_share",  # observed attribute of the match (Method 1)
}


@pytest.fixture(scope="module")
def artifact_path(tmp_path_factory):
    # Loads truth + both estimators (~20s); build once for the module.
    return accuracy.build(tmp_path_factory.mktemp("accuracy") / "accuracy.json")


@pytest.fixture(scope="module")
def payload(artifact_path):
    return json.loads(artifact_path.read_text(encoding="utf-8"))


def test_schema_and_top_level_shape(payload):
    assert payload["schema"] == "accuracy/v1"
    assert set(payload) == {"schema", "package_version", "floor_units", "methods", "stories"}
    assert set(payload["methods"]) == {"method0", "method1"}


def test_artifact_contains_no_truth_key_anywhere(artifact_path):
    # The raw bytes must not mention any truth column or a truth-value field. This is
    # the public-safety guarantee; it is checked on the serialized text, not the tree.
    raw = artifact_path.read_text(encoding="utf-8")
    for needle in FORBIDDEN_SUBSTRINGS:
        assert needle not in raw, f"artifact leaks a truth-adjacent token: {needle!r}"


def test_headline_carries_only_error_and_counts(payload):
    for method in ("method0", "method1"):
        headline = payload["methods"][method]["headline"]
        assert set(headline) <= HEADLINE_ALLOWED, method
        # The percentage headline exists and is a number.
        assert isinstance(headline["median_abs_pct_error"], (int, float))
        assert isinstance(headline["n_scored"], int)


def test_both_methods_are_scored_side_by_side(payload):
    # The anti-rigging exhibit: Method 0 is never shown alone. Both have a headline.
    assert payload["methods"]["method0"]["headline"]["n_scored"] > 0
    assert payload["methods"]["method1"]["headline"]["n_scored"] > 0


def test_every_regime_bucket_has_at_least_five_events(payload):
    for method in ("method0", "method1"):
        for feature, buckets in payload["methods"][method]["regimes"].items():
            assert feature in OBSERVED_REGIMES, f"non-observed regime label: {feature}"
            for bucket in buckets:
                assert bucket["n_events"] >= 5, f"{method}/{feature}/{bucket['label']} < 5 events"
                assert set(bucket) == {
                    "label",
                    "n_events",
                    "median_abs_pct_error",
                    "median_signed_pct_error",
                }


def test_match_relaxed_share_regime_is_method1_only(payload):
    # It is an attribute of Method 1's match; Method 0 has no such regime.
    assert "match_relaxed_share" in payload["methods"]["method1"]["regimes"]
    assert "match_relaxed_share" not in payload["methods"]["method0"]["regimes"]


def test_stories_are_separated_and_carry_only_percentages(payload):
    stories = payload["stories"]
    assert {s["story_tag"] for s in stories} == {
        "pantry_trap",
        "hero_cannibal",
        "pure_subsidy",
        "clean_winner",
    }
    for story in stories:
        assert set(story) == {"story_tag", "promo_id", "method0", "method1"}
        for method in ("method0", "method1"):
            block = story[method]
            assert set(block) == {"estimable", "signed_pct_error"}
            # A percentage or null — never a unit count (which could expose truth).
            assert block["signed_pct_error"] is None or isinstance(block["signed_pct_error"], (int, float))


def test_two_builds_are_byte_identical(artifact_path, tmp_path):
    again = accuracy.build(tmp_path / "again.json")
    assert artifact_path.read_bytes() == again.read_bytes()


def test_artifact_uses_lf_newline_and_no_nan(artifact_path):
    raw = artifact_path.read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    assert b"NaN" not in raw
    assert b"Infinity" not in raw
