# Estimator specification — cinderhaven-promo-incrementality

**Pre-registration document.** This is committed — and the estimator
implementation is committed and tagged — **before any code in this repo loads
truth.** The git history is the blindness evidence: an estimator whose spec and
code predate the first truth import cannot have been tuned against the answer.
See DECISIONS.md, external-validity entry.

Status: **Method 0 pre-registered. Implementation pending upstream v0.2.0**
(`economics()`), which supplies the margin basis. No estimation code exists yet
at the time this spec is committed.

---

## 1. The blindness contract — the allowed surface

Estimation code consumes **exactly three names** from
`cinderhaven_promo_response`:

| Name | What it provides |
|------|------------------|
| `load()` | The observed layer: `promo_events` (131) and `promo_scan_delta` (1,340,462 rows x 8 observed columns). |
| `economics()` | The **product price card** — per-SKU COGS and per-SKU x retailer wholesale / unit margin. Added upstream in **v0.2.0**, in a module that imports no demand parameters. |
| `testing` | The truth gate (`assert_no_truth_access`), run against this repo's own `src/`. |

Everything else is banned: **`config`, `constants`, `truth`.**

**Demarcation principle — blindness protects the demand response, not the price
card.** Lift, dip, transfer, compliance, seasonality, baseline velocity are what
the estimator must never see. COGS and wholesale price are product economics a
real client hands a vendor on day one; no vendor estimates a client's COGS, and
no accuracy claim rests on not knowing it. `economics()` mirrors the real
engagement.

`constants` is banned because it tangles the legitimate price card with the
baseline-demand generator (`BASE_UNITS`, `SKU_ARCHETYPES`, `SEASONALITY`,
`SEASONAL_PROFILES`) — the true baseline Method 0 is meant to *estimate*. The AST
gate denies only `truth`, so the ban on `config`/`constants` is enforced by this
repo's own supplementary import check over `src/`.

---

## 2. Method 0 — pre-period average baseline

The naive estimator, on the critical path of every downstream number including
ROI. Shipped **labeled as Method 0** on screen: it is the anti-rigging exhibit,
expected to be wrong in measurable ways, not a recommended method.

### 2.1 Literature (predates the generator)

The pre-period baseline is the textbook naive cut in promotion evaluation, and
every source below predates the Cinderhaven generator — so no part of this
method is justified by how the generator works:

- Blattberg & Neslin, *Sales Promotion: Concepts, Methods, and Strategies*
  (Prentice Hall, 1990) — the pre-promotion baseline as the reference against
  which incremental volume is measured.
- van Heerde, Leeflang & Wittink, "The Estimation of Pre- and Postpromotion
  Dips with Store-Level Scanner Data," *Journal of Marketing Research* 37(3),
  2000 — the pre-period baseline and its known dip/borrowing bias.
- The Nielsen/IRI practitioner "baseline & incremental" decomposition, whose
  simplest form is a pre-period expected baseline.

### 2.2 Baseline

For event `E` (`promo_id`) covering SKU `S` at retailer `R` over
`[start_week, end_week]`, and each store `T` of `R` carrying `S`:

    baseline_units(S, T, E) = mean{ observed_units(S, T, w)
                                    : w in the P weeks strictly before E.start_week,
                                      and that row's promo_id is null }

- **Window `P = 8` weeks** (Saturday week-endings). Deliberately short: a longer
  window starts absorbing seasonality, which Method 0 explicitly does **not**
  correct for — a naive baseline that quietly de-seasonalizes would not be
  naive. Judgment call, logged.
- **Promo weeks excluded** from the window: a prior promo in the pre-period
  would inflate the baseline.
- **Insufficiency rule:** if fewer than `M = 4` non-promo weeks are available in
  the window (series start, sparse authorization), the store-event is flagged
  `insufficient_pre_period` and **excluded from the incremental computation** —
  never given a fabricated baseline.
- **Exclusion stays visible (the denominator is never silently shrunk).** An
  event dropped as not estimable does **not** vanish: it appears in the
  Scorecard **unranked**, marked *"not estimable by Method 0,"* and **every
  portfolio figure is labeled "of N estimable events."** A portfolio total that
  quietly shrinks its own denominator is the vendor trick this tool exists to
  mock. (This is also a Method-0-vs-Method-1 contrast later: a better baseline
  rescues some of these.)

### 2.3 Incremental units ("gross lift")

For each promoted store-week row `r = (S, T, w)` with `promo_id == E`:

    incremental_units(r) = observed_units(r) - baseline_units(S, T, E)   # may be < 0

### 2.4 Subsidized baseline (reported, not netted here)

The baseline volume that sold at the discounted price — a **decomposition of
`accrued_cost`**, not a term in the ROI numerator:

    subsidized_units(r) = baseline_units(S, T, E)
    subsidy_giveaway(r) = baseline_units(S, T, E) * (regular_price(r) - promoted_price(r))

> **Framing (PENDING CONFIRMATION — framing A proposed 2026-08-19).** The ROI numerator is
> **manufacturer margin (wholesale − COGS) on incremental units only** — retail
> prices do not enter it. The subsidy giveaway is a **decomposition of
> `accrued_cost` (the denominator)** — trade dollars spent on baseline units
> that would have sold anyway — surfaced in Event Anatomy; it is **never**
> subtracted from the numerator. Nothing double-counts: for `scan_based` events
> the baseline subsidy is already inside `accrued_cost`. Netting it into the
> numerator (framing B) would double-count it against the denominator.

Computed and carried for the Event Anatomy waterfall (a later slice), display
only.

### 2.5 Money — integer cents, round-half-even, row grain

`unit_margin(S, R)` comes from `economics()` and is **manufacturer margin =
wholesale(S, R) - cogs(S)** — never MSRP, which overstates ROI (the package's
own wholesale-vs-msrp warning).

    incremental_margin_cents(r) = round_half_even( incremental_units(r) * unit_margin(S, R) * 100 )

Quantized **once, here at the row grain**, round-half-even. This per-row integer
is the atomic unit everything downstream sums.

### 2.6 ROI and the portfolio header

    event_net_margin_cents(E)   = sum_r incremental_margin_cents(r)      over E's rows
    event_accrued_cost_cents(E) = round_half_even( accrued_cost(E) * 100 )
    event_ROI(E)                = event_net_margin_cents(E) / event_accrued_cost_cents(E)
    event_lost_money(E)         = event_net_margin_cents(E) < event_accrued_cost_cents(E)

Portfolio header (the three CFO numbers + the count), all computed in the
pipeline, never in the front end:

    # sums run over ESTIMABLE events only; excluded events are shown unranked,
    # and every figure is labeled "of N estimable events" (see 2.2).
    total_accrued_spend_cents    = sum_E event_accrued_cost_cents(E)
    net_incremental_margin_cents = sum_E event_net_margin_cents(E)
    portfolio_ROI                = net_incremental_margin_cents / total_accrued_spend_cents
    N_estimable                  = count of events with a Method 0 baseline   # <= 131
    N_lost_money                 = count{ E : event_lost_money(E) }   # of N_estimable

### 2.7 Reconciliation (exact, no tolerance)

The row-level `incremental_margin_cents` is the shared atomic integer, so:

    sum_E event_net_margin_cents(E)  ==  sum_over_all_rows incremental_margin_cents(r)

asserted as **integer equality** — the event-sum and the row-grain sum are the
same integers added in two groupings. A test pins the portfolio total. This is
the package's reconciliation discipline crossing the repo boundary.

---

## 3. Event universe

All **131** events. `executed` (121), `phantom` (7, planned + funded, ran
nowhere), `unplanned` (3, ran without a plan) are all scored; phantom and
unplanned are **marked** in the artifact. Phantom promos accrued cost with no
lift — the leakage story the Scorecard exists to show; dropping them would
flatter the portfolio. See DECISIONS.md.

---

## 4. Known weaknesses of Method 0 (stated, because they are the point)

- **No seasonal adjustment.** An event at a seasonal turn is mis-baselined: a
  grilling-sauce promo as the season ramps has a rising true counterfactual, so
  a flat pre-period average understates baseline and **overstates lift**.
- **Vulnerable to trends/ramps.** A trending SKU's pre-period average lags its
  true counterfactual for the promo weeks.
- **No comparable-store control.** Cannot separate the promo effect from a
  concurrent market-wide move.
- **Residual pre-period contamination.** Excluding promo weeks does not exclude
  the *post-promo dip* weeks that may sit just before the event, which depress
  the baseline and inflate measured lift.

These are why Method 0 is shipped as the anti-rigging exhibit and why the
**two-baseline-method deploy gate** holds public launch until comparable-store
matching lands. Its error is a result to report, by regime, not a defect to
hide.

---

## 5. Determinism

Same package version + seed + estimator code produces identical cents.
Round-half-even is fixed; no wall-clock, no unseeded randomness, no
dict-ordering dependence in the estimation path.

---

## 6. Change control

Any change to this spec or the Method 0 implementation **after first scoring**
is a logged re-run in DECISIONS.md with before/after error — never a silent
edit. Each new baseline method re-scores the Scorecard as its own logged re-run.
