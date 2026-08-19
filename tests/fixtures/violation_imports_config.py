"""Deliberate violation: estimation code importing the response coefficients.

Not collected by pytest; input to assert_no_generator_access, which must reject
it. config holds LIFT_CENTERS / DIP_FRACTION — the promo-response answer key.
"""

from cinderhaven_promo_response import config  # <- the violation


def estimate_baseline(delta):
    return config.LIFT_CENTERS
