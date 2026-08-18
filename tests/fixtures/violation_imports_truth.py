"""Deliberate violation: estimation code that imports the truth loader.

Not importable as part of the suite and not collected by pytest — it exists
only as input to `assert_no_truth_access`, which must reject it. If this file
ever stops failing the gate, the gate has stopped working.

Kept permanently rather than committed-then-removed: a gate demonstrated to
fail once, in a commit since reverted, is evidence that has to be taken on
trust from the git log. A gate that fails on every run is evidence now.
"""

from cinderhaven_promo_response import truth  # <- the violation


def estimate_baseline(delta):
    return truth.load_truth()
