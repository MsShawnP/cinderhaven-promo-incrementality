"""Deliberate violation: an estimator that reaches truth transitively via the
accuracy module.

Not collected by pytest and not executed — it exists only as input to the
dependency-direction guard, which must reject it. The accuracy module is the
one file allowed to import truth; anything that imports IT reaches truth at
runtime while its own AST stays clean and the per-file truth gate passes. Kept
permanently so the guard is demonstrated-to-fail on every run, not once in a
reverted commit.
"""

from incrementality import accuracy  # <- the violation


def estimate_baseline(delta):
    return accuracy.score(delta)
