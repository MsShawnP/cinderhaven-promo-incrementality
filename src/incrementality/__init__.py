"""Estimation and artifact-building code for the incrementality tool.

Everything in this package is blind: CI runs
`cinderhaven_promo_response.testing.assert_no_truth_access` over `src/` on
every push. The accuracy view will be the single exemption, named
explicitly in `tests/test_truth_gate.py` rather than globbed.

See `src/CLAUDE.md` for the full rule, including the one leak the gate
cannot catch — `cinderhaven_promo_response.config` holds the generator's
coefficients and importing it is prohibited by convention alone.
"""
