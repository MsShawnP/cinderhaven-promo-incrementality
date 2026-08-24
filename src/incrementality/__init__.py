"""Estimation and artifact-building code for the incrementality tool.

Every module in this package is blind except one: CI runs
`cinderhaven_promo_response.testing.assert_no_truth_access` over `src/` on
every push, and `accuracy.py` is the single exemption — named explicitly as a
file in `tests/test_truth_gate.py`, never globbed as a directory. Nothing else
under `src/` may import it either; `tests/test_dependency_direction.py` closes
that hole from the other side.

See `src/CLAUDE.md` for the full rule, including the one leak the gate
cannot catch — `cinderhaven_promo_response.config` holds the generator's
coefficients and importing it is prohibited by convention alone.
"""
