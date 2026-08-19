"""Deliberate violation: estimation code importing the demand generator.

constants holds BASE_UNITS / SEASONALITY / ARCHETYPE_VELOCITY_MULT — the true
baseline by another route. Reaching it makes a "naive" baseline a lookup.
"""

from cinderhaven_promo_response import constants  # <- the violation


def estimate_baseline(delta):
    return constants.SEASONALITY
