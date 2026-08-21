# Estimator specification — cinderhaven-promo-incrementality

**Pre-registration document.** This is committed — and the estimator
implementation is committed and tagged — **before any code in this repo loads
truth.** The git history is the blindness evidence: an estimator whose spec and
code predate the first truth import cannot have been tuned against the answer.
See DECISIONS.md, external-validity entry.

Status:
- **Method 0 (§2) — pre-registered and frozen 2026-08-19, implemented.** The ROI
  framing is confirmed (§2.4, framing A); `economics()` shipped in upstream v0.2.1
  and the consumer is pinned to it. Changes after first scoring are logged re-runs
  (§7).
- **Method 1 (§3) — pre-registered 2026-08-21, implementation blocked on upstream
  `store_card()` (v0.3.0).** The comparable-store baseline needs cross-banner
  controls matched on store identity (region, format) that the observed layer does
  not carry — same-banner control pools are empty for ~80% of events because
  promotions here are banner-wide (measured; see §3.7). `store_card()` supplies that
  identity, mirroring `economics()`'s demarcation. This section is committed and
  tagged **before** any Method 1 code loads truth. See DECISIONS.md.

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
- **Event-level estimability (clarified 2026-08-19, pre-freeze).** Store-events
  are dropped **individually** when insufficient. An **event** is estimable iff
  **at least one** of its store-events has a sufficient pre-period; its net then
  sums over the sufficient store-events only. An event is *"not estimable by
  Method 0"* only when it has **zero** sufficient store-events. In this
  generation that is exactly **2 of 131** — `PRE-0048` and `PRE-0054`, both
  starting 2023-01-28, three weeks after the series begins, so no store has four
  pre-period weeks. `N_estimable = 129`.
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

The baseline volume that sold during the promo — a **decomposition of
`accrued_cost`**, not a term in the ROI numerator:

    subsidized_units(r) = baseline_units(S, T, E)
    subsidy_giveaway(r) = baseline_units(S, T, E) * (regular_price(r) - promoted_price(r))

> **Framing A — confirmed 2026-08-19.** The manufacturer's realized economics
> are **wholesale − COGS per unit**, and **all** promo funding flows through
> `accrued_cost`. The shelf discount (`promoted_price`) is the *retailer's*
> price move: it drives demand but never touches the manufacturer's wholesale
> margin per unit. So:
>
> - **numerator** = manufacturer margin on *incremental* units,
> - **denominator** = accrued trade cost,
> - **giveaway** = the slice of that cost which bought volume that would have
>   sold anyway.
>
> Nothing is netted twice — the giveaway lives inside the denominator, never
> the numerator. This is the same lesson the upstream calibration bug taught
> (**retail margin ≠ manufacturer margin**, ~2.8×), now institutionalized here:
> retail prices decompose the *cost*, they never enter the *margin*.

**Display requirement — the giveaway share.** Every event surfaces the share of
its promoted volume that would have sold anyway: *"X% of the volume sold on
discount would have sold anyway."* It is the `pure_subsidy` story's headline stat
and the most CEO-legible number the decomposition produces — a promo can post
real incremental units and still be a bad buy because most of the discounted
volume needed no subsidy.

    subsidized_cost_share(E) = (sum over complied rows of baseline_units)
                             / (sum over complied rows of observed_units)

Over **complied rows only** — volume that actually sold on discount. A volume
ratio, in `[0, 1]` except on net-dip events (see the annotation below).

> **Corrected 2026-08-19 (pre-freeze, before any scoring).** The original §2.4
> formula divided the *retail* giveaway (`baseline_units × (regular − promoted)`)
> by the *manufacturer* `accrued_cost` — two different dimensions — producing
> "shares" up to **936%** (`clean_winner`, whose ~12%-of-volume coupon gives it
> the smallest subsidy base and so the largest blow-up: the mixed-dimension bug's
> most absurd number landed on the story with the smallest base, confirming the
> dimension check caught a real defect). The volume ratio above is the
> dimensionally honest version of the same intent — *a share of what the spend
> bought.* Logged as a spec correction in DECISIONS.md. This is a pre-freeze fix,
> not a post-scoring re-run: no truth has been loaded.
>
> **Scan-funded equivalence — where the "trade dollars" copy stays honest.**
> Discount depth is constant within an event, so the volume ratio equals the
> discount-weighted *dollar* share identically. For **scan-funded** events,
> `accrued_cost = rate × promoted units`, so `baseline_units ÷ promoted_units`
> equals `baseline_dollars ÷ accrued_dollars` exactly — there the CEO line *"X%
> of this deal's trade dollars subsidized volume you'd have sold anyway"* is
> dimensionally true and may be used. For **fixed-funded** events (billback,
> off_invoice, MCB) the fund is not per-unit, so only the volume phrasing is
> honest; the universal stat is therefore worded in volume.
>
> **Net-dip annotation.** A share `> 1` means the pre-period baseline sat *above*
> the volume that sold during the promo — a dip / pull-forward artifact of the
> naive baseline, not a >100% subsidy. Carried as a flag
> (`baseline_exceeds_promoted`) so the view annotates it rather than showing a
> nonsensical percentage.

The **per-row retail giveaway** `subsidy_giveaway(r) = baseline_units × (regular
− promoted)` remains defined above as a decomposition of the retail discount; it
is an **Event Anatomy** waterfall quantity (next arc), not computed in the
Scorecard pipeline. The Scorecard carries only the volume share.

Computed in the pipeline, never in the front end.

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

**Zero accrued cost (clarified 2026-08-19, pre-freeze).** Three events accrued
`$0.00` (two phantoms and one executed that accrued nothing). `event_ROI` divides
by `accrued_cost`, which is undefined at zero — so ROI is **null** there, not a
sentinel or a clamp. `event_lost_money` uses the `net < cost` comparison, which
is still defined (`net < 0` at zero cost), so those events are still classified.
The **portfolio** denominator is the *sum* of estimable accrued costs, which is
positive, so `portfolio_ROI` is always defined.

### 2.7 Reconciliation (exact, no tolerance)

The row-level `incremental_margin_cents` is the shared atomic integer, so:

    sum_E event_net_margin_cents(E)  ==  sum_over_all_rows incremental_margin_cents(r)

asserted as **integer equality** — the event-sum and the row-grain sum are the
same integers added in two groupings. A test pins the portfolio total. This is
the package's reconciliation discipline crossing the repo boundary.

---

## 3. Method 1 — comparable-store baseline

The second baseline, and the one that clears the two-method public-deploy gate
with Method 0. Where Method 0 asks *"what did this store sell before the promo?"*,
Method 1 asks *"what did comparable stores sell **during** the promo weeks, while
not running it?"* — a concurrent counterfactual. That is exactly what Method 0
lacks: a read on the seasonal and market movement happening in the promo weeks
themselves. Shipped **labeled as Method 1**, alongside Method 0, with the delta
between them visible.

### 3.1 Literature (predates the generator)

The test-vs-control / matched-store baseline is the standard practitioner
alternative to a pre-period average, and every source below predates the
Cinderhaven generator:

- Abraham & Lodish, "PROMOTER: An Automated Promotion Evaluation System,"
  *Marketing Science* 6(2), 1987 — the baseline as expected sales absent the
  promotion, read from comparable non-promoted stores and periods.
- Abraham & Lodish, "Getting the Most Out of Advertising and Promotion,"
  *Harvard Business Review*, May–June 1990 — the control-store logic in
  practitioner form.
- Blattberg & Neslin, *Sales Promotion: Concepts, Methods, and Strategies*
  (Prentice Hall, 1990) — the control-store method for incremental-volume
  measurement.
- The Nielsen/IRI "matched control store" test-vs-control standard, whose whole
  premise is that the control group carries the counterfactual the test store
  cannot show about itself.

No part of this method is justified by how the generator works.

### 3.2 The allowed surface adds `store_card()`

Method 1 consumes one name beyond Method 0's surface: **`store_card()`** (upstream
**v0.3.0**, shipped), one row per `store_id` carrying **store-master identity** —
`store_id`, `retailer_id`, `region` (five regions). It is the day-one data a client
hands a vendor, exactly `economics()`'s demarcation: identity, not demand response.

> **Demarcation, verbatim (governed the v0.3.0 release):** the card carries
> geography and banner identity; **volume tier is derived by the estimator from
> observed pre-period velocity, never shipped on the card** — anything
> velocity-shaped stays off it, because baseline velocity is on the protected side
> of the blindness line (DECISIONS.md, the `economics()` demarcation). This keeps
> `store_card()` unambiguously on the identity side, same as `economics()`.

**`region` is package-assigned, not a real store-master draw** — it is a value the
synthetic data package assigns to each store and must never be joined to platform
store data (DECISIONS.md). It is legitimate comparability identity all the same.

**Format class is a consumer-side JUDGMENT mapping.** `store_card()` ships no
`store_format`, so Method 1 assigns a coarse format class from the retailer by the
estimator author's retail knowledge — **tagged `JUDGMENT`, not read from the
generator:**

    RET-COSTCO      -> club            # JUDGMENT: warehouse club
    RET-WALMART     -> supercenter     # JUDGMENT: mass supercenter
    RET-WHOLEFOODS  -> natural         # JUDGMENT: natural/organic
    RET-SPROUTS     -> natural         # JUDGMENT: natural/organic
    RET-KROGER      -> conventional    # JUDGMENT: conventional grocery
    RET-REGIONAL    -> conventional    # JUDGMENT: conventional grocery

Format class is coarser than banner on purpose — two natural banners share a class —
which is exactly what turns the empty same-banner pool (§3.7) into a usable
cross-banner one. The mapping predates any truth access and is not tuned against
error; changing it after first scoring is a logged re-run.

The allowed surface becomes exactly `load()`, `economics()`, `store_card()`,
`testing`. `config`, `constants`, `truth` remain banned; the AST gate and the
supplementary import check both cover Method 1 code.

### 3.3 Comparable pool

For a promoted store-event — store `T`, event `E` (SKU `S`, retailer `R`, weeks
`W = [start_week, end_week]`) — the comparable pool `C(T, E)` is the set of stores
that:

- **carry SKU `S`** (have observed rows for it),
- are **not running any promotion during `W`** — every `(store, S, w in W)` row has
  `promo_id` null (a clean control, not merely not-running-*this*-event),
- are **not** `T` and **not** among `E`'s promoted stores,
- **match `T` on store identity:** same `region` (`store_card()`) + same **format
  class** (the §3.2 JUDGMENT mapping) + observed volume within a band of `T`'s (§3.6).

**Cross-banner is allowed and expected.** Same-banner control pools are empty for
~80% of events (§3.7), so `C` is drawn across retailers; the identity match is what
makes a cross-banner store a valid control.

### 3.4 Baseline — the comparable median, per week

For each promoted week `w` in `W`, the baseline is the median velocity of the
comparable pool in that same week:

    baseline_units(T, E, w) = median{ observed_units(c, S, w) : c in C(T, E) }

Per **week**, not per event: the point of a comparable-store method is to track the
concurrent movement Method 0 is blind to, and that movement is weekly. The volume
match (§3.6) makes the comparables' absolute median a valid level for `T`.

    incremental_units(r = (S, T, w)) = observed_units(r) - baseline_units(T, E, w)

Everything downstream — subsidized baseline and giveaway share (§2.4), integer-cent
margin at the row grain (§2.5), ROI and the portfolio header (§2.6), reconciliation
(§2.7) — is computed **exactly as in Method 0**, on this baseline instead. The money
grain, round-half-even, and exact reconciliation are unchanged.

### 3.5 Minimum-pool rule and its exclusion reason (the visible-exclusion rider)

A median over a thin pool is noise. Require at least `MIN_POOL` comparable stores:

- If `|C(T, E)| < MIN_POOL`, the store-event is flagged **`insufficient_comparable_pool`**
  and excluded from the incremental computation — never given a baseline read off
  one or two stores.
- **Exclusion stays visible**, exactly as Method 0's `insufficient_pre_period`
  rider (§2.2): an event with no estimable store-event appears in the Scorecard
  **unranked**, marked *"not estimable by Method 1,"* and every Method 1 portfolio
  figure is labeled *"of N estimable events."* The reason code distinguishes it from
  Method 0's exclusion, so the two methods' coverage can be compared honestly.

`MIN_POOL` and the volume band (§3.6) are **provisional pending the matched-pool
distribution**, which cannot be measured until `store_card()` ships `region` and
`store_format`. They will be set from that distribution and **tuned against pool
size (observed), never against error (truth)** — tuning a blind estimator's knobs
against the answer key is the one thing pre-registration exists to forbid. The
chosen values are logged in DECISIONS.md before first scoring.

### 3.6 Volume tier, and coverage versus Method 0

The volume match uses `T`'s **observed** pre-period velocity — the mean of its
`observed_units` for `S` over the same 8-week pre-period window Method 0 uses (§2.2)
— and keeps comparables whose own pre-period velocity falls in the same band.
Volume is computed by the estimator from observed units; it is never read from
`store_card()`.

Because Method 1's baseline comes from the comparables' *during-week* velocity, it
does **not** require `T`'s own pre-period for the baseline value — only for the
volume match. Where `T` has too little pre-period history for a volume estimate
(the series-start events Method 0 cannot estimate at all), Method 1 falls back to
matching on `region` + `store_format` alone. So **Method 1 can estimate some events
Method 0 excludes** — the concrete "a better baseline rescues some of these" contrast
promised in §2.2. The fallback is labeled in the artifact so the coverage gain is
attributable to it, not hidden.

### 3.7 Known weaknesses (stated, because they are the point)

- **Banner-wide promotion is the norm here, so there are no same-banner controls.**
  Measured on this generation: 40 of 131 events have **zero** same-banner clean
  controls and 106 of 131 have fewer than five, because a promotion covers
  essentially every store of its retailer that carries the SKU. This is realistic —
  real trade events are banner-wide — and it is *why* Method 1 matches cross-banner
  on identity rather than within banner. Cross-banner controls carry residual
  shopper-base differences that `region` + `store_format` + volume matching reduces
  but does not eliminate.
- **Sensitive to comparable-pool size.** A thin matched pool gives a noisy median;
  `MIN_POOL` trades coverage for stability, and the trade is made visible through the
  `insufficient_comparable_pool` exclusion rather than absorbed silently.
- **Fails when the controls are themselves affected.** A category-wide or
  market-wide movement (a holiday, a competitor's national event) moves the control
  stores too, so the concurrent counterfactual absorbs it and Method 1 under- or
  over-states lift. A pre-period method is blind to this differently; neither is
  immune.
- **Matching is on observed identity, not the generator's true store structure.**
  Region and format are the client's store master, not the latent variables that set
  each store's demand — residual confounding remains. The accuracy view measures how
  much, by regime; it is a result to report, not a defect to hide.

### 3.8 Determinism and change control

Same determinism contract as §6: same package version + seed + code → identical
cents; the median is order-independent, and any tie-break is fixed. Adding Method 1
re-scores the Scorecard as a **logged re-run** (§7): the scorecard artifact carries
both methods, and the view toggles between them with the delta visible. That toggle
is the moment the "compare the methods" demonstration exists, and the two-method
public-deploy gate clears when both ship behind it.

## 4. Event universe

All **131** events. `executed` (121), `phantom` (7, planned + funded, ran
nowhere), `unplanned` (3, ran without a plan) are all scored; phantom and
unplanned are **marked** in the artifact. Phantom promos accrued cost with no
lift — the leakage story the Scorecard exists to show; dropping them would
flatter the portfolio. See DECISIONS.md.

---

## 5. Known weaknesses of Method 0 (stated, because they are the point)

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

## 6. Determinism

Same package version + seed + estimator code produces identical cents.
Round-half-even is fixed; no wall-clock, no unseeded randomness, no
dict-ordering dependence in the estimation path.

---

## 7. Change control

Any change to this spec or the Method 0 implementation **after first scoring**
is a logged re-run in DECISIONS.md with before/after error — never a silent
edit. Each new baseline method re-scores the Scorecard as its own logged re-run.
