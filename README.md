# Cinderhaven Promo Incrementality

Most trade-promotion tools report incremental lift and ask you to trust the
number. There is no way to check: the counterfactual — what would have sold
without the promotion — is unobservable in real scan data. This tool runs on
a dataset where the counterfactual is known and quarantined, so every estimate
it produces is scored against the truth it was blind to.

Five linked views on one promo-event spine — Baseline Builder, Lift Split,
Net Lift, Portfolio, ROI Scorecard — plus an accuracy view that reports how
wrong the estimator actually was.

**Status:** scaffold. No stack chosen, no code written. See PLAN.md.

## Cinderhaven context

Built on the Cinderhaven synthetic dataset — a ~$25M specialty food brand,
50 SKUs across 5 product lines and 6 contracted retailers. Data is synthetic;
methodology and deliverables are real.

The promo signal comes from `cinderhaven-promo-response` v0.1.0, an additive,
seed-locked overlay: a curated promo-event calendar, a promo-responsive scan
series, and a quarantined ground-truth table. It never alters canonical.

## What it does

<!-- Filled in as views ship. Do not write claims here ahead of the code. -->

Nothing yet.

## Stack

Undecided. Two constraints are fixed:

- The estimation engine is **Python** —
  `cinderhaven_promo_response.testing.assert_no_truth_access` parses source
  with `ast` and can only audit `.py` files, so estimation code in another
  language would make the blindness claim unenforceable.
- The data dependency is **`cinderhaven-promo-response>=0.1.0`**, consumed
  through its public API only.

Everything that renders is open. Three candidates are written up in
DECISIONS.md; the choice is made by the planning process.

## Data contract

**Canonical baseline:** 50 SKUs · 5 product lines (AS·PS·SC·DG·SB) · 6 retailers
(Walmart·Costco·Whole Foods·Sprouts·Kroger·Regional Group) · 10 channels
(6 retail + UNFI·KeHE·DPI + DTC)

This tool reads the promo-response overlay and adds no data of its own. It
never regenerates, modifies, or reads the SSOT scan table.

Observed layer, via `pr.load()`:

- `promo_events` — 131 rows
- `promo_scan_delta` — 1,340,462 rows × 8 observed columns

Ground truth reaches one module only — the accuracy view — through
`truth.load_truth()`, guarded by `truth.assert_aligned_with_observed()`.
`assert_no_truth_access` runs in CI over every other estimation module. It is
the package's own gate, imported rather than re-implemented, so the same rule
is enforced on both sides of the boundary.

## Run

```
# Not runnable yet — no stack, no dependency manifest.
```

---

Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics
consulting for specialty food brands scaling into national retail.
