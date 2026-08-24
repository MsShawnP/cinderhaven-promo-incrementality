"""The test that is not optional. See tests/CLAUDE.md.

Two claims, deliberately separate:

1. Estimation code under `src/` cannot reach quarantined ground truth.
2. The gate that asserts (1) actually rejects violations.

Claim 2 is what makes claim 1 mean anything. A gate that passes over code it
would never fail is indistinguishable from no gate at all, and the failure
mode is silent — it reports green forever.
"""

import pytest
from cinderhaven_promo_response.testing import (
    TruthAccessViolation,
    assert_no_truth_access,
)

# The exemption list. Every entry is an explicit **file** path, never a
# directory. A directory exemption is a growth path: anything later dropped
# into it inherits the blindness exemption silently, and a "list is still
# singular" check would not fire because the entry count never changes. When
# the accuracy view grows past one module, each file is named on its own line.
# The friction is the point — an exemption should cost a visible line.
#
# The file below is the shipped Accuracy view — the one module allowed to read
# truth. It was listed here before it existed, and the entry did not change when
# it landed; that is the point of naming a file rather than globbing a directory.
ACCURACY_VIEW = ("src/incrementality/accuracy.py",)

FIXTURES = "tests/fixtures"


def test_estimation_path_is_blind():
    """No module under src/ imports truth or names the truth artifact."""
    assert_no_truth_access("src", exclude=ACCURACY_VIEW)


def test_gate_rejects_a_module_that_imports_truth():
    """Layer 1: the import channel."""
    with pytest.raises(TruthAccessViolation):
        assert_no_truth_access(f"{FIXTURES}/violation_imports_truth.py")


def test_gate_rejects_a_module_that_names_the_truth_artifact():
    """Layer 2: the path channel, which imports nothing and would otherwise pass."""
    with pytest.raises(TruthAccessViolation):
        assert_no_truth_access(f"{FIXTURES}/violation_names_truth_artifact.py")


def test_gate_refuses_to_run_over_an_empty_tree(tmp_path):
    """A gate that audits zero files must not report success.

    Upstream raises ValueError rather than passing vacuously. Asserted here
    because it is the property that makes a green gate meaningful: without
    it, deleting src/ would turn this suite green.
    """
    (tmp_path / "no_python_here.txt").write_text("not code")
    with pytest.raises(ValueError):
        assert_no_truth_access(str(tmp_path))


def test_every_exemption_is_a_named_file_not_a_directory():
    """The invariant that must survive the list growing.

    `exclude` matches on substring, so a trailing-slash entry exempts every
    file placed under it, forever, with no further edit and no failing test.
    Naming files individually means each exemption costs one visible line.
    """
    for entry in ACCURACY_VIEW:
        assert entry.endswith(".py"), (
            f"exemption {entry!r} is not a file path. A directory exemption "
            "silently covers every file added under it later — name the module."
        )
        assert not entry.endswith("/"), f"exemption {entry!r} is a directory"


def test_exemption_list_matches_the_logged_decision():
    """A second exemption is a decision to log, not a line to add quietly.

    See DECISIONS.md: truth flows one way. Widening this list is how the
    gate gets turned off one plausible entry at a time.
    """
    assert ACCURACY_VIEW == ("src/incrementality/accuracy.py",), (
        "the truth-gate exemption list changed; this requires a DECISIONS.md "
        f"entry explaining why, not a test edit. Found: {ACCURACY_VIEW!r}"
    )
