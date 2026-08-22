# cinderhaven-promo-incrementality — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

### 2026-08-17 — The estimation engine is Python. Not a preference — a constraint.

- **Why:** The project's central claim is that estimates are blind and
  provably so, enforced by `cinderhaven_promo_response.testing.assert_no_truth_access`
  running in CI. That function parses source with `ast` and walks it for
  forbidden imports and string literals. It can audit `.py` files and
  nothing else. Estimation code written in TypeScript, SQL, or R would make
  the gate silently vacuous — it would pass by never being applied.
- **Scope:** global; all estimation code.
- **Do not:** re-implement the gate in another language to work around this.
  A consumer re-implementing the check is asserting its own good intentions;
  importing and running the package's own gate is the claim worth making.

### 2026-08-17 — Consume the data package through its public API only.

- **Why:** `pr.load()`, `truth.load_truth()`, `truth.assert_aligned_with_observed()`
  and `testing.assert_no_truth_access()` are the contract the package
  documents and tests. Reading its `.cache/` parquet directly, or importing
  its internals, bypasses the loader schema gates — including the one that
  hard-fails when a truth column rides along on the observed artifact.
- **Scope:** global.
- **Do not:** call `pd.read_parquet` on anything under the package's
  `.cache/`. Do not import `cinderhaven_promo_response.config` from
  estimation code — the generator's coefficients are the answer key, and
  the AST gate will not catch it because it only denies `truth`.

### ~~2026-08-17 — PENDING: front-end stack. Deferred to the planning process.~~

> **CLOSED 2026-08-17 by `/plan-eng-review`.** Superseded by "Front-end stack:
> SvelteKit" below. Body kept intact as history — the candidate analysis here
> was written against six views, scrollytelling and a 1.34M-row browser
> payload, all three of which turned out to be false. Read it for what was
> considered, not for what is true.

~~**Status: open. This is the first task in PLAN.md.**~~ Recorded here so the
planning process starts from the constraints rather than re-deriving them.

**What is already settled** (see the two decisions above): the engine is
Python, and the data arrives through `pr.load()`. The open question is only
what renders the five views, and whether anything needs a live server.

**The prior question, which should be answered first:** does this tool
compute at request time? Everything upstream is deterministic and seed-locked,
and the estimators are too — 131 events, and no user input changes a result,
only what is displayed. Baseline-method selection is the apparent exception,
but the method space is small (~3), so all methods can be precomputed and
toggled client-side. If that holds, the tool is a **build-time computation
with an interactive front end**, not a query service, and a Python web server
buys nothing while costing hosting, latency, and a cold-start story.

**Candidates evaluated on 2026-08-17, none chosen:**

1. **Python engine + Dash/Plotly on Fly.io** — the fleet default, included
   because it must be beaten on merit rather than skipped. One language end
   to end, a shape already shipped elsewhere, fastest to a working tool.
   Against: the callback model fights scrollytelling and a story-driven
   waterfall, five linked views make the callback graph brittle, and a Dash
   app looks like a Dash app — the flagship bar is exactly what it gives up.
   Always-on server for data that never changes.
2. **Python engine + Observable Framework, static, on Cloudflare Pages** —
   Framework's native model is Python data loaders at build time with
   markdown/D3 pages rendering the outputs, which is the architecture rather
   than a workaround; the Python/JS boundary lands exactly where the CI gate
   needs it. Full control over the waterfall, the cannibalization matrix and
   the type/color system, so the Lailara design system genuinely applies.
   1.34M rows ship as parquet and query client-side via DuckDB-WASM.
   Against: JS/markdown is new ground, Framework is a young project, and
   styling is real CSS work rather than component defaults.
3. **Python engine + SvelteKit + D3, static, on Cloudflare Pages** — highest
   ceiling on the visual result, scrollytelling native, nothing opinionated.
   Against: routing, loading, layout and chart primitives are all bespoke;
   roughly a week added to the estimate and the steepest learning curve.

**Deliberately excluded:** Evidence.dev. Strong at SQL scorecards and weakest
at custom composite charts, which is precisely the waterfall and the
cannibalization matrix.

**What makes this decision low-stakes to get wrong:** the engine is a plain
Python package under every option. If the front end disappoints, it is
replaced and 100% of the estimation code survives. Weigh the front-end
choice accordingly — it is reversible; the engine language is not.

**Do not** close this entry by picking an option in passing. Strike it
through and write a dated replacement naming the rejected alternatives.

**Requirements changed after this entry was written (2026-08-17, `/clarify`
and `/office-hours`).** The candidate analysis above assumed six views,
scrollytelling, and 1.34M rows in the browser. All three are now false. The
comparison must be re-run against the current requirements — three views,
precomputed artifacts, persistent cross-view filters and deep-linkable
events. Candidate 1 (Dash) is eliminated: an always-on server for data that
never changes. Candidates 2 and 3 are both still live, and the margin
between them narrowed when the scope dropped to three views. `/plan-eng-review`
tests them fresh and inherits nothing from the six-view framing.

### 2026-08-17 — Front-end stack: SvelteKit + D3, static, on Cloudflare Pages.

Closes the PENDING entry above. Decided at `/plan-eng-review`.

- **Decision:** Python engine writes precomputed artifacts at build time.
  **SvelteKit** with `adapter-static` renders three views, deployed static to
  Cloudflare Pages. D3 for the composite charts.
- **Why — one reason, narrowly:** the requirements are router-shaped.
  Persistent cross-view filters, deep-linkable events and comparison mode are
  shared client state across routes. SvelteKit provides a client router,
  stores and `searchParams` natively. Nothing else about this project argues
  for it.

**Rejected — Observable Framework, static, on Cloudflare Pages.** The closest
call, and rejected on evidence rather than taste. Framework is a **multi-page
app**: file-based routing, build-time page loaders, parameterized routes, and
— across its routing, page-loaders and params documentation — **no client-side
router and no built-in cross-route state**. The requirements are reachable via
URL search params plus a shared module, but hand-rolled, and a document load
lands on the **primary interaction path**: clicking an event row in the
Scorecard to open Event Anatomy is the most-used transition in the tool and it
would flash. Comparison mode across a page load is worse. *Caveat recorded
honestly: this rests on Framework having no undocumented client router. Three
documentation queries found none. If that is wrong, this decision is worth
revisiting — the rest of Framework's model, especially Python data loaders at
build time, fit this project well.*

**Rejected — Dash/Plotly on Fly.io.** An always-on server for data that never
changes: hosting cost, cold-start story and latency bought nothing. Plotly
defaults fight the Lailara design system, and the flagship bar is exactly what
that gives up.

**Rejected earlier — Evidence.dev.** Strong at SQL scorecards, weakest at
custom composite charts, which is precisely the waterfall.

- **What makes this safe to have gotten wrong:** the engine is a plain Python
  package under every option. A front-end swap costs zero estimation code. The
  decision was made decisively rather than deliberated further, because the
  project's named primary risk is the stall, not a wrong front end.
- **Scope:** everything that renders.
- **Do not:** add a server. Do not introduce a client-side data query layer —
  artifacts are precomputed and small by decision.

### 2026-08-17 — Three views, not six. Scope halved.

- **Decision:** Build **ROI Scorecard**, **Event Anatomy**, **Accuracy**.
  Nothing else.
- **Why:** Baseline Builder, Lift Split, Net Lift and Portfolio were five
  separate tools in the original brainstorm that got inherited as views
  without re-justification. They are the same decomposition at four zoom
  levels. Collapsed into Event Anatomy as segments of one waterfall rather
  than four navigations. Every persuasive job stays assigned: the Scorecard
  is the verdict, Event Anatomy is the explanation, Accuracy is the proof.
- **What Event Anatomy has to answer, and why Accuracy cannot:** the
  objection that actually happens in the room is per-event — *"that August
  BOGO was my call, I know it worked, your tool says it lost money."* The
  trade lead is defending a promo, not auditing an estimator.
  Accuracy-in-general does not defuse that; anatomy-of-this-number does.
  The full chain, for that event: gross → subsidized baseline → dip →
  transfer → net, with the baseline-method toggle and the transfer panel
  inside the view.
- **Scope:** global; supersedes the five-view framing in CLAUDE.md.
- **Do not:** solve "the tool looks thin" by adding views. Depth per view
  beats view count — one anatomy view with a working method toggle is
  deeper than four shallow pages.

### 2026-08-19 — Blindness protects the demand response, not the price card. Economics via a blessed accessor.

- **Decision:** Estimation code's **allowed surface is exactly** `pr.load()`,
  `pr.economics()`, and `pr.testing`. `economics()` — per-SKU COGS and
  per-SKU×retailer wholesale/unit margin — is added upstream in **v0.2.0** in its
  own module that imports **no demand parameters**. `config`, `constants`, and
  `truth` are all banned.
- **The demarcation principle:** blindness protects the **demand response** —
  lift, dip, transfer, compliance, seasonality, baseline velocity — the things an
  estimator must not see. **COGS and wholesale price are not demand response.**
  They are product economics a real client hands a vendor on day one; no vendor
  estimates a client's COGS, and no accuracy claim rests on not knowing it.
  `economics()` mirrors the real engagement; withholding it would model a world
  no analyst works in.
- **Why a new accessor rather than reading `constants`:** `constants` tangles the
  price card (COGS, wholesale, MSRP — legitimate) with the **baseline-demand
  generator** (`BASE_UNITS`, `SKU_ARCHETYPES`, `ARCHETYPE_VELOCITY_MULT`,
  `SEASONALITY`, `SEASONAL_PROFILES`). Importing it for COGS also hands over the
  true seasonal and velocity structure — the baseline Method 0 is supposed to
  *estimate*. That is a blindness breach the AST gate does **not** catch (it
  denies `truth`, not `constants`) — the same "structure walks out past the gate"
  hole as the `config` ban. The fix is upstream separation, not a consumer
  workaround.
- **Enforcement:** the allowed surface is asserted by this repo's own
  supplementary import check over `src/` (bans `config`/`constants`), on top of
  the upstream `assert_no_truth_access` truth gate. Lands with the pipeline
  commits.
- **Rejected — external cited margin %:** would ship slice 1 without waiting on
  v0.2.0, but folds a margin-assumption error into what the accuracy view later
  presents as *estimation* error — muddying the one attribution the tool exists
  to keep clean. Not worth blurring the thesis exhibit for ship-now.
- **Rejected — revenue-basis ROI (no COGS):** systematically overstates ROI
  (SPEC.md's own msrp-vs-wholesale warning); an ROI that flatters promos is the
  competitor's product, not this one.
- **Scope:** all estimation code; the CI gate; the upstream v0.2.0 release.
- **Do not:** import `constants` or `config` from estimation code. Do not compute
  margin from MSRP — manufacturer margin is wholesale − COGS.

### 2026-08-21 — Method 1 is a cross-banner, identity-matched comparable-store baseline. It needs `store_card()` (v0.3.0).

- **Decision:** Method 1 (spec §3, pre-registered 2026-08-21) is a comparable-store
  baseline: for each promoted store-week, the counterfactual is the **median
  velocity of comparable control stores in that same week**, where comparability is
  defined on **observed store identity** — `region` and `store_format` from a new
  upstream accessor `store_card()`, plus an observed volume band. Controls are drawn
  **cross-banner**. The pipeline is **blocked on upstream v0.3.0** shipping
  `store_card()`, same pattern as Method 0 blocked on `economics()` (v0.2.0).
- **Why cross-banner, and why the store-card is needed — measured, not asserted:**
  same-banner clean control pools are **empty for 40 of 131 events and < 5 for 106
  of 131** (median 2), because promotions in this universe are **banner-wide** — a
  promo covers essentially every store of its retailer carrying the SKU. A
  same-banner comparable method would exclude ~80% of events. Valid cross-banner
  matching requires store identity (region, format) that the observed layer does not
  carry (`store_id` gives only the banner prefix; `economics()` is per SKU×retailer).
  This is the STOP-AND-ASK trigger firing exactly as pre-authorized — improvising an
  observed-only proxy or reaching into `constants` was declined in favor of the
  proper upstream accessor.
- **`store_card()` demarcation, verbatim (governs the v0.3.0 release):** the card
  carries what a client's store master actually contains — geography and format
  identity. **Volume tier is derived by the estimator from observed pre-period
  velocity, never shipped on the card**; anything velocity-shaped stays off it,
  because baseline velocity is on the protected side of the blindness line. That
  keeps `store_card()` unambiguously on the identity side, same as `economics()`.
  Own module, imports no demand parameters, AST-clean, demand-free import test.
  Allowed surface becomes `load()`, `economics()`, `store_card()`, `testing`.
- **Provisional constants, tuned on pool size not error:** `MIN_POOL` (the
  minimum-comparable-pool floor, with exclusion reason `insufficient_comparable_pool`)
  and the volume band cannot be set until `store_card()` ships the identity columns
  to measure the matched-pool distribution. They will be tuned **against observed pool
  size, never against truth/error**, and logged before first scoring — tuning a blind
  estimator against the answer key is the one thing pre-registration forbids.
- **Rejected as Method 1 — the indexed diff-in-diff (a Method 2 candidate, not a
  fallback):** baseline = test store's own pre-period × the control pool's during/pre
  velocity ratio. Fully observed (banner + velocity), no release needed. It is a
  **legitimately different standard method**, and as its own pre-registered method
  later it would strengthen the multi-method accuracy story. Its only sin here is
  that it is not the attribute-matched comparable-store method §3 set out to register.
  **Logged as a future Method 2 candidate**, not a rejected approach.
- **Scope:** `docs/estimators.md` §3; Method 1 estimation code; the CI gate; the
  upstream v0.3.0 release.
- **Do not:** define comparability on same-banner controls only (the pools are
  empty). Do not ship a volume/velocity tier on `store_card()`. Do not tune
  `MIN_POOL` or the band against measured error. Do not implement Method 1 before
  the consumer is pinned to a `store_card()`-bearing release.

### 2026-08-21 — Re-pin to v0.3.0 (store_card()). Logged re-run per the pin decision.

- **Decision:** The consumer is re-pinned from v0.2.1 (`11caa13`) to **v0.3.0**
  (`6556460000d56fd2df1c89c59f592f363b93245c`), which adds `store_card()`. Logged
  as a **re-run** per the pin decision — an accuracy number is meaningless without
  recording which generation it scored against, and the pin is the record.
- **Data-neutral for the observed layer:** `store_card()` is additive; `load()`
  still returns 131 events / 1,340,462 rows / the eight observed columns unchanged.
  No estimate that predates this re-pin changes because of it. Verified: the
  data-contract test asserts v0.3.0 and the unchanged observed shape, plus the new
  `store_card()` contract.
- **What `store_card()` actually ships:** `store_id`, `retailer_id`, `region` —
  and **no `store_format`.** The card is geography + banner identity; format is
  supplied consumer-side by judgment (next entry), and volume is derived by the
  estimator from observed velocity, never on the card.
- **Scope:** `pyproject.toml`; `tests/test_data_contract.py`; every Method 1 figure.
- **Do not:** report a Method 1 accuracy figure without recording the v0.3.0 SHA
  and seed alongside it.

### 2026-08-21 — `store_card().region` is package-assigned, not the SSOT draw. Never join it to platform store data.

- **Decision:** The `region` column from `store_card()` is a value the data
  package **assigns** to each synthetic store. It is **not** a draw from any
  single-source-of-truth store master, and it must **never** be joined to real
  platform store data — the store ids are synthetic and the join would be
  meaningless (and, if it appeared to work, misleading).
- **Why it still earns its place:** region is legitimate comparability identity —
  the estimator matches controls within a region — exactly the day-one store-master
  attribute a real vendor uses. Its being package-assigned is a property of the
  synthetic world, not a defect; the accuracy view measures how well identity-based
  matching recovers truth, and that measurement is honest whether the region labels
  are "real" or assigned, so long as they are never confused for platform data.
- **Scope:** all Method 1 code; any place `store_card()` output is used or displayed.
- **Do not:** join `store_card().region` to platform/real store data. Do not present
  it as a customer's actual region assignment.

### 2026-08-21 — Method 1 format class is a consumer JUDGMENT mapping (retailer → format), because store_card() ships no format.

- **Decision:** `store_card()` carries no `store_format`, so Method 1's match key
  uses a **consumer-side JUDGMENT mapping** from retailer to a coarse **format
  class**, tagged `JUDGMENT` in the estimator spec (§3):

      RET-COSTCO      -> club
      RET-WALMART     -> supercenter
      RET-WHOLEFOODS  -> natural
      RET-SPROUTS     -> natural
      RET-KROGER      -> conventional
      RET-REGIONAL    -> conventional

  The final match key is **region (`store_card()`) + format class (this mapping) +
  observed volume band**.
- **Why format class matters — it is what makes cross-banner matching valid:**
  banner alone leaves 80% of events with no controls (banner-wide promotion). Format
  class is coarser than banner — Whole Foods and Sprouts are both `natural` — so a
  Sprouts promo can borrow Whole Foods controls in the same region and volume band.
  That is the mechanism that turns the empty same-banner pool into a usable one.
- **Why it is JUDGMENT, and honest as such:** the mapping is the estimator author's
  retail knowledge, not read from the generator. It is cited as judgment (like every
  modelling assumption), predates any truth access, and is not tuned against error.
  A different analyst might class Sprouts separately from Whole Foods; that is a
  defensible alternative, logged if changed, never silently.
- **Scope:** `docs/estimators.md` §3; `method1.py`.
- **Do not:** derive format from `constants`/`config` or from truth. Do not change
  the mapping after first scoring without a logged re-run.

### 2026-08-21 — Method 1 matches hierarchically (format where it helps, region+volume where it can't). §3 amended r2, pre-truth.

- **Decision:** Method 1's comparable pool is matched by a **two-stratum hierarchy**,
  tightest stratum that clears `MIN_POOL`: (1) region + format class + volume band;
  (2) if that is `< MIN_POOL`, region + volume band with format class dropped. Below
  the relaxed stratum, `insufficient_comparable_pool`. `MIN_POOL = 5`,
  `VOLUME_BAND_FACTOR = 2`. Replaces the flat "region + format + band" match key of
  the first §3 freeze.
- **Why, measured on observed data before any truth access:** format class as a
  *hard* filter starves the pool, because `club` (Costco) and `supercenter`
  (Walmart) are **single-banner** format classes — "same format" collapses to "same
  banner," the empty pool the whole method exists to route around. Region+format
  clears `MIN_POOL` for only **33%** of the 4,070 store-events; region+volume clears
  it for **95%**. The flat match left **57 of 131** events estimable and dropped
  **all four seeded stories** (three are Walmart/supercenter). The hierarchy keeps
  format where it separates multi-banner classes (`natural` vs `conventional`) and
  degrades to region+volume exactly for the single-banner classes and nowhere else.
- **The relaxation is recorded per store-event in the artifact** (`full` vs
  `relaxed`), rolled up to a per-event relaxed share. It is an **observed** attribute,
  hence a legitimate regime dimension for the Accuracy view — "does error grow where
  matching relaxed?" — costing one boolean now versus an artifact migration later.
- **Pre-registration integrity:** this diverges from the match key frozen at
  `method1-preregistration`, so the amended spec is **re-tagged `method1-preregistration-r2`
  before any Method 1 code that loads truth exists** — no truth has been scored, both
  tags predate first truth access, and the evidence chain now contains the amendment
  and its measured justification. Tuned against **pool size, never error**.
- **Scope:** `docs/estimators.md` §3.3, §3.5; `method1.py`; the Scorecard artifact
  (new relaxed-share field).
- **Do not:** restore the flat format-as-hard-filter match. Do not tune `MIN_POOL`
  or the band against measured error. Do not drop the per-event relaxed share from
  the artifact — it is the accuracy view's regime handle.

### 2026-08-21 — Scorecard re-scored with both methods (artifact scorecard/v2). Logged re-run.

- **Decision:** Adding Method 1 re-scores the Scorecard, logged as a re-run per the
  pre-registration rule. The artifact is bumped to **scorecard/v2**: a portfolio
  header per method plus one record per event co-locating both methods' estimates,
  so the front-end toggle and the Method 0 → Method 1 delta are a lookup.
- **Method 0 is unchanged** — the shared-spine refactor was behavior-preserving, so
  the v2 `method0` block reproduces v1's numbers exactly (portfolio ROI 1.132, net
  incremental margin $118,200, 64 of 129 lost money). No before/after error to log:
  no truth was scored, and Method 1 is a *new* method, not an edit to Method 0.
- **Method 1's scorecard figures (blind, v0.3.0):** portfolio ROI **1.041** (vs
  Method 0's 1.132 — less rosy, the comparable baseline captures the concurrent
  trend Method 0 misses), net incremental margin $109,042, 129 estimable (a
  different 129: rescues PRE-0054, drops PRE-0097), 64 lost money. These are the
  numbers the toggle shows; whether either is closer to *truth* is the Accuracy
  view's question, not asserted here.
- **Scope:** `build_scorecard.py`; `tests/test_scorecard.py`; the front-end.
- **Do not:** read the Method 1 vs Method 0 ROI gap as an accuracy result — it is a
  difference between two blind estimates, pending truth scoring.

### 2026-08-17 — Slice 1 ships Method 0, the naive baseline, labeled as such.

- **Decision:** Baseline estimation is on the critical path of **every**
  downstream number, including ROI. Slice 1 uses **Method 0 (pre-period
  average)** explicitly and says so on screen. Comparable-store matching and
  seasonal adjustment arrive as their own later slices. Each method added
  re-scores the Scorecard as a logged re-run.
- **Why:** PLAN justified the ROI Scorecard as the first slice by calling it
  "the shallowest estimator." ROI is incremental profit over spend, and
  incremental units require a baseline — so the hardest statistical problem
  in the project is an input to slice 1, not a later one. Naming Method 0
  makes that honest, and it puts the anti-rigging exhibit first instead of
  last.
- **Deploy gate:** the tool does not go public until **at least two baseline
  methods exist**. A scorecard scored only by the naive method is the
  anti-rigging exhibit without the rigor exhibit.
- **Scope:** PLAN sequencing; every published figure.
- **Do not:** present a Method 0 number without the label. Do not change an
  estimator after first scoring without a DECISIONS entry recording
  before/after.

### 2026-08-17 — Truth flows one way. Nothing may import the accuracy module.

- **Decision:** The accuracy module is a **sink, never a source**. No module
  outside it may import it, directly or transitively. Enforced by a test of
  the dependency direction, not by convention.
- **The hole this closes:** `assert_no_truth_access` parses each file's AST
  for forbidden imports. The accuracy module is exempted **by name**, so it is
  unaudited — deliberately. But an estimation module that imports the accuracy
  module gains runtime access to truth while its *own* AST contains no
  forbidden import. The gate passes and the estimator is no longer blind.
  Whether the package's gate does transitive analysis is **unverified** —
  worth checking upstream. The test is cheap either way, and this is the
  project's central claim.
- **Scope:** all estimation code; the CI gate.
- **Do not:** rely on the AST gate alone for blindness. It protects against
  direct imports of `truth`. It does not protect against reaching truth
  through a module that is allowed to have it.

### 2026-08-19 — §2.4 giveaway share is a volume ratio, not retail-giveaway ÷ accrued-cost. Pre-freeze correction.

- **Decision:** `subsidized_cost_share(E) = Σ baseline_units / Σ observed_units`
  over **complied** promoted rows — the fraction of the volume sold on discount
  that would have sold anyway at baseline. Replaces the frozen §2.4 formula
  `Σ(baseline_units × (regular − promoted)) / accrued_cost`.
- **Why:** the original formula divided a **retail** giveaway (retail-discount
  dollars) by a **manufacturer** figure (`accrued_cost` is only 0.55–0.69× the
  retail discount, and that ratio is stable only for scan_based — billback and
  off_invoice range 0.24–1.75×). Mixed dimensions produced "shares" up to **936%**
  (`clean_winner`). Because discount depth is constant within an event, the
  discount cancels and the honest metric collapses to a plain volume ratio.
- **The equivalence that keeps the CEO copy usable:** for **scan-funded** events
  `accrued_cost = rate × promoted units`, so `baseline_units ÷ promoted_units`
  equals `baseline_dollars ÷ accrued_dollars` identically — there *"X% of trade
  dollars subsidized volume you'd have sold anyway"* is dimensionally true. For
  **fixed-funded** events the fund is not per-unit, so only the volume phrasing
  is honest; the universal on-screen stat is worded in volume.
- **Net-dip annotation:** a share `> 1` means the naive baseline sat above the
  promoted volume (a dip / pull-forward artifact), carried as the flag
  `baseline_exceeds_promoted` rather than shown as a >100% subsidy.
- **Why this is a correction, not a re-run:** caught by the dimension/schema check
  **before any truth was loaded or any accuracy scored** — the pre-registration
  ordering held. The §7 re-run discipline (before/after error, logged) applies to
  changes *after first scoring*; this is a pre-freeze fix. That the mixed-dimension
  bug's most absurd number (936%) landed on the story with the smallest subsidy
  base is confirmation the check caught a real defect, not cosmetics.
- **Scope:** `docs/estimators.md` §2.4; `method0.py`; the Scorecard artifact.
- **Do not:** divide a retail-dollar quantity by `accrued_cost`. Do not present
  the volume share as a dollar share for fixed-funded events.

### 2026-08-19 — Two §2.4-adjacent spec gaps resolved pre-freeze: event estimability and zero accrued cost.

- **Event estimability:** an event is estimable iff **≥1** of its store-events has
  a sufficient pre-period (store-events drop individually; an event is "not
  estimable" only with zero sufficient store-events). Exactly 2 of 131 events
  (`PRE-0048`, `PRE-0054`, both 2023-01-28, three weeks into the series) are not
  estimable → `N_estimable = 129`. The alternative reading (an event is estimable
  only if *all* its store-events are sufficient) was rejected: a single new store
  would knock out an entire event, contradicting the per-store-event exclusion
  language in §2.2.
- **Zero accrued cost:** 3 events accrued `$0.00` (2 phantom, 1 executed).
  `event_ROI = net/cost` is **null** there (division by zero has no honest numeric
  answer — not a sentinel, not a clamp); `event_lost_money` uses `net < cost` and
  stays defined. `portfolio_ROI` divides by the positive sum of estimable costs
  and is always defined.
- **Why logged:** both are gaps in the frozen spec surfaced during implementation.
  Recorded so the resolution is a decision, not a silent choice, per the
  pre-registration discipline.
- **Scope:** `docs/estimators.md` §2.2 and §2.6; `method0.py`.
- **Do not:** filter the two non-estimable events out silently, or emit a numeric
  ROI for a zero-cost event.

---

### 2026-08-19 — Upstream defects are fixed upstream, with their own regression test. No downstream paper-over.

- **Decision:** When a consumer-side gate catches a defect that lives in the
  data package, the fix goes **in the package**, ships as a new pinned version,
  and carries **its own regression test**. The consumer never swallows the
  error, ships a warm-cache workaround, or adapts its gate to tolerate the bug.
- **Why:** The pattern held four-for-four this cycle and before it — the
  FIGURES.md cold-cache crash (v0.1.1), the pandas-eager-import gate break
  (v0.2.1), and, in sibling repos, brand fonts missing from `package-data`. Each
  time a downstream guard surfaced an upstream packaging gap. A downstream
  paper-over (swallowed exception, tolerated import, shipped cache) hides the
  defect for the *next* consumer and rots the guard that caught it. Fixing
  upstream with a regression test means the class cannot recur silently.
- **The general rule it generalizes:** every file a package reads at runtime
  must be present in the built artifact, asserted against the **wheel**, not the
  source tree. Both v0.1.1 (FIGURES.md) and the brand-fonts bug were this exact
  class; both were invisible to a test run from a checkout.
- **Scope:** the consumer↔package boundary; any shared-dependency defect.
- **Do not:** swallow a data-package exception, ship a warm cache to dodge a
  cold-cache bug, or weaken a downstream gate to accommodate an upstream defect.
  Fix the source and add the test that proves it stays fixed.

## Positioning & Claims

Added 2026-08-17 during `/office-hours`. These entries govern what this
tool is allowed to claim and how the claim is worded.

### 2026-08-21 — The better baseline makes the book look worse. Note for the case study.

- **Observation:** Method 0 (naive pre-period) puts portfolio ROI at **1.13×**;
  Method 1 (comparable-store) puts it at **1.04×**. The stricter, more defensible
  baseline makes the promo book look *worse*, not better — because the comparable
  method catches the concurrent seasonal/market trend the naive pre-period average
  credits to the promo.
- **Why it is the thesis proving itself, unprompted:** every improvement in the
  baseline pulls measured incrementality down. That is exactly what a skeptical CFO
  suspects about their trade spend and exactly what no vendor will show — a vendor's
  incentive runs the other way. The tool demonstrates the direction of the bias, on
  data where the truth is knowable, without being asked to.
- **Where it goes:** the case study on `lailarallc.com/work` (external to this repo),
  and it informs the accuracy view's copy — "the naive method visibly losing" is the
  anti-rigging exhibit, and this ROI gap is its portfolio-level headline. Not an
  accuracy *result* yet (that needs truth scoring); it is a difference between two
  blind estimates, and the accuracy view says which direction is right.
- **Scope:** case study; accuracy view copy; positioning.

### 2026-08-17 — Synthetic data is the only publishable option, not a fallback.

- **Decision:** Frame synthetic data as a strength, not an apology. Inherit
  the fleet disclosure verbatim: *"Data is synthetic; methodology and
  deliverables are real."*
- **Why:** Client promo data can never be shown publicly — by any consultant
  or vendor, at any client count. Synthetic is simultaneously the only world
  where truth is **knowable** and the only world that can be **published**.
  The two constraints coincide, which is what makes the accuracy view
  possible at all.
- **The competitive line, which belongs in the accuracy view's copy:**
  anyone claiming to demonstrate accuracy on real client data is either
  breaching confidentiality or making it up.
- **Scope:** README, accuracy view copy, any case study.
- **Do not:** hedge or apologize for synthetic data. Do not bury the
  disclosure.

### 2026-08-17 — External validity: what the accuracy number is allowed to claim.

The objection this answers: *you built the world and you built the
estimator.* The AST gate is airtight against machine leakage and porous
against human leakage — no gate catches the author knowing the shape of her
own generator. Three defenses, at different strengths, against two different
attacks.

**(a) True today — the world is literature-grounded, not invented.** Every
generator coefficient carries CITE/DIRECTION/JUDGMENT; the dip schedule sits
in vHLW00's published band; the loss rate calibrates to Nielsen's US 71%; a
plausibility audit gates the release. **Cite the package for this, never
this repo.**

**(b) True by commitment — enforced structurally, since nothing automated
catches human leakage.**

1. **Estimators are textbook / vendor-standard methods only** — pre-period
   average, comparable-store matching, seasonal adjustment — each cited to
   methodology literature that **predates the generator**. No method may be
   justified by reference to how the generator works. *This is the defense
   against design-time leakage.*
2. **Pre-registration in git.** The estimator spec and implementation are
   committed and tagged **before** any code in this repo loads truth. The
   accuracy slice comes later in PLAN. Estimator changes after first scoring
   are re-runs, logged here with before/after — never silent. Git history is
   the blindness evidence. *This is the defense against post-hoc tuning. It
   does not cover design-time leakage — the generator predates this repo, so
   ordering here cannot speak to it. (b)(1) covers that. State them as
   covering different attacks; they are not redundant.*
3. **Ship the naive estimator alongside the good ones.** If the exercise
   were rigged, naive wouldn't lose. Its worse error is the anti-rigging
   exhibit — same logic as forecast value-add.

**(c) True by reporting rule.** Headline error is the **full event
population**. The four seeded stories — `pantry_trap`, `hero_cannibal`,
`pure_subsidy`, `clean_winner` — are marked and reported separately, never
as the headline. The mediocre middle is the honest denominator.

**Claim language, exactly:**

- *"Provably blind"* applies to **the code** — AST gate plus the `config`
  ban. It is precise there and overclaims if stretched further.
- The **method-level** claim is: *"this is the error a standard method makes
  under a realistic, fully-known world — measured, by regime, including
  where it is large."*

- **Scope:** global; every published accuracy figure and all surrounding copy.
- **Do not:** claim or imply that measured error on Cinderhaven predicts
  error on a client's data. That is a different claim and this tool does not
  support it.

---

## Data & Schema

### 2026-08-17 — Pin the upstream package version.

- **Why:** An accuracy number is meaningless without knowing which data
  generation it scored against. The package is seed-locked, so a version
  bump that changes generation changes every reported error.
- **Scope:** dependency manifest; any published accuracy figure.
- **Do not:** report an accuracy number without recording the
  `cinderhaven-promo-response` version and seed alongside it.

### 2026-08-18 — The upstream package is pinned by commit SHA in the manifest. Never an editable local path.

- **Decision:** `pyproject.toml` declares the dependency as a git URL pinned to
  the **full 40-character commit SHA** of the release:

      cinderhaven-promo-response @ git+https://github.com/MsShawnP/cinderhaven-promo-response@70021d4d472bdf4ab5132778472b4ca8a95fe0e8

  `70021d4` is v0.1.0. The tag name is recorded in a comment for humans; the
  pin is the SHA.
- **Why SHA and not the tag name:** annotated tags are mutable. A tag can be
  moved and the manifest still reads as pinned, which is the worst version of
  a pin — it satisfies review and not reproducibility. The rest of the fleet
  pins SHAs (`0f300ef`, `c4ea09e`); same discipline, same reason.
- **Why the full SHA and not the short form:** a short SHA is a prefix match,
  and prefixes collide as a repo grows.
- **The trap, which cost a wrong pin on 2026-08-18:** `git rev-parse v0.1.0`
  returns the **annotated tag object** (`1d3ec86`), not a commit. Use
  `git rev-parse v0.1.0^{commit}`. The first SHA proposed for this manifest,
  `a237910`, was neither — it was an unrelated ancestor commit dated 75 minutes
  before the release, predating the plausibility audit and the retired-figure
  scan. It resolves, it installs, and every accuracy figure scored against it
  would have been scored against a build that never passed its own release
  gate. **It was caught only because a SHA is checkable**; a tag name would
  have been right by accident and taught nothing.
- **Verification that the pin took effect** — pip records provenance, so this
  is checkable rather than assumed:

      .venv/Lib/site-packages/cinderhaven_promo_response-0.1.0.dist-info/direct_url.json
      → "commit_id": "70021d4d472bdf4ab5132778472b4ca8a95fe0e8"

- **Rejected — editable install from `../cinderhaven-promo-response`.** It
  makes "pinned at v0.1.0" describe a working tree rather than anything CI can
  reproduce, failing the pin decision it appears to satisfy. Local iteration is
  still fine as a **hand-run command** — `pip install -e ../cinderhaven-promo-response` —
  that the manifest never records.
- **Rejected — vendoring a wheel into this repo.** It is a pure-Python package
  that generates its data at first load; a committed binary artifact is just a
  second thing that can drift from the tag.
- **Scope:** the dependency manifest; every published accuracy figure.
- **Do not:** put an editable or local path in the manifest, for any reason,
  including "just while iterating." Do not pin a tag name. Do not pin a short
  SHA. Do not record a SHA without confirming it is the peeled commit of the
  intended tag.

### 2026-08-17 — The portfolio roll-up is a pipeline artifact with a reconciliation test.

- **Decision:** The Scorecard is a portfolio header plus a ranked list. The
  header's three numbers are the CFO answer: **total accrued trade spend,
  portfolio net incremental margin, portfolio ROI** — plus N of 131 events
  that lost money. All of it computed in the pipeline, never in the front end.
- **The test:** the portfolio total must tie to **both** the sum of event
  nets **and** the row-level grain sum. This is the package's reconciliation
  discipline crossing the repo boundary — the same move as the identity
  `observed_units ≡ baseline + lift − dip ± transfer + noise`, applied to
  this tool's own arithmetic.
- **Why it gets an assertion rather than an assumption:** transfer is
  zero-sum, which makes naive summation *look* safe. That is exactly the
  property that hides a double-count or a dropped sign until someone checks.
- **Scope:** pipeline; ROI Scorecard header.
- **Do not:** compute any portfolio figure in the front end. Do not treat
  transfer's zero-sum property as self-evidently safe.

### 2026-08-17 — Money is integer cents. Reconciliation is exact, not tolerant.

- **Decision:** Carry money as **integer cents** through the pipeline,
  quantized once at the row grain with **round-half-even**. The portfolio
  reconciliation asserts **equality**, not approximate equality.
  ~~Units are already integers.~~ **Corrected 2026-08-19:** units are
  *continuous* — see the 2026-08-19 money-grain entry below, which supersedes
  this line. The exactness now rests on the shared row-level atomic integer,
  not on units being whole.
- **Why:** the roll-up ties to a row-level sum over 1,340,462 values. In
  float64, summation order changes the last bits, so the assertion would need
  a tolerance — and a tolerance is a number that only ever gets widened when
  it fails. Integer arithmetic removes the question. This matches the upstream
  package's ethos: the reconciliation identity there is **bit-exact per row**,
  not within epsilon.
- **Scope:** pipeline; every monetary figure and every reconciliation test.
- **Do not:** introduce a float tolerance into a reconciliation assertion. If
  one appears to be necessary, that is a signal the arithmetic is wrong, not
  that the tolerance is too tight.

### 2026-08-19 — Units are continuous; money is integer cents, round-half-even at the row grain.

- **Decision:** `observed_units` is **continuous** — fractional on all 1,340,462
  rows (the upstream noise deviate), range 0.03–396.5. Revenue = units × price is
  therefore inherently fractional-cents. Money is carried as **integer cents**,
  quantized **once at the row grain** with **round-half-even** (banker's). That
  per-row integer is the atomic unit; the event-sum and the row-grain-sum
  aggregate the *same* integers, so the portfolio reconciliation ties **exactly**
  with no float tolerance.
- **Why round-half-even, stated explicitly:** across 1.34M rows, always-round-
  half-up introduces a small systematic upward bias in totals; half-even removes
  it. An unstated rounding mode resurfaces as a one-cent reconciliation mystery
  in an environment with different defaults. Named here, in CLAUDE.md, and pinned
  by a portfolio-total test.
- **What this corrects:** the 2026-08-17 "units are already integers" premise
  (an eng-review assumption) was wrong; the schema check caught it before the
  Method 0 spec froze. Exactness never depended on integer units — it depends on
  the shared row-level atomic integer.
- **Scope:** every monetary figure; every reconciliation test.
- **Do not:** quantize at more than one grain, use half-up, or introduce a float
  tolerance. If a tolerance seems necessary the arithmetic is wrong.

### 2026-08-19 — The portfolio universe is all 131 events; phantom included and marked.

- **Decision:** The ROI Scorecard scores **all 131 events** — 121 `executed`,
  7 `phantom` (planned and funded, ran nowhere), 3 `unplanned` (ran without a
  plan). Phantom and unplanned are **marked** in the artifact, never dropped.
- **Why:** phantom promos accrued $5,277 while producing no real lift — trade-
  spend leakage rendered in ROI form, the clearest loss story the tool exists to
  show. Excluding them would quietly flatter the portfolio number, which is the
  exact sin the tool indicts. Matches CLAUDE.md's "N of 131." Method 0 handles
  them without special-casing: a phantom's promo weeks are `complied=False` with
  no lift, so incremental units ≈ 0 and ROI is deeply negative by construction.
- **Scope:** portfolio roll-up; the ranked event list; the "N lost money" count.
- **Do not:** filter to executed-only for the headline. If a view needs an
  executed-only cut it is an explicit, labeled secondary view, not the default.

### 2026-08-17 — Published artifacts carry error metrics, never truth — including in their labels.

- **Decision:** Artifacts written for the front end may contain **error
  metrics derived from truth**. They may never contain **truth values**. The
  accuracy artifact's schema is asserted by a test.
- **Why `.gitignore` does not cover this:** the ignore file correctly excludes
  `.cache/` and `*.parquet`, so the quarantined truth table cannot reach git.
  But the accuracy module *writes* a precomputed artifact — `accuracy.json` or
  similar — into the site's data directory, which is committed or built and
  published by design. Nothing in the ignore file protects it. This repo will
  be public.
- **The subtler channel — regime labels.** Regime definitions in the accuracy
  artifact must be built from **observed features only**: promo type, depth,
  duration, season, product line, calendar position. Truth-derived regime
  labels — actual compliance draw, actual dip magnitude, actual transfer —
  leak generator structure **even with every truth value aggregated away**.
  "Error by actual-compliance band" reveals per-event compliance by
  inspection. If a truth-derived cut is analytically necessary, it aggregates
  to **≥N events per bucket** and is labeled truth-derived in the artifact
  schema. Default is observed-features-only.
- **The general form, worth carrying:** the gate protects **values**;
  structure can walk out through **labels**. Same class of hole as the
  transitive-import entry above — the named defense is narrower than the thing
  it is defending.
- **Scope:** every artifact written for the front end.
- **Do not:** cut error by any truth-derived feature without the aggregation
  floor and the schema label.

---

## Visualization

[Chart conventions, palette decisions, interactivity choices. The Lailara
design system at `~/projects/reference/lailara-design-system/LAILARA_DESIGN_SYSTEM.md`
governs colors, typography and chart rules; entries here record only
project-specific choices on top of it.]

### 2026-08-17 — Mobile responsibility splits by surface, not by view.

- **Decision:** The **30-second surface** — the Scorecard header: verdict
  line, one chart, three numbers — is **phone-first** and must fully work at
  375px. The **exploration surfaces** — ranked-list interactions, Event
  Anatomy, Accuracy — are **desktop-first**: readable and functional on
  mobile, but comparison mode and dense waterfall interactions may degrade
  gracefully with a "best on desktop" note.
- **Why:** Distribution is a link from `lailarallc.com/work`, and links get
  opened on phones. The first impression is therefore a phone impression, and
  a 30-second verdict that only works at 1440px fails its own brief. The
  exploration surfaces are consumed differently — nobody runs a comparison
  across 131 events on a phone.
- **What this buys:** the responsive work is bounded to **one** genuinely
  responsive component instead of three. The global deployed-UI gate still
  requires checking every surface at 1440px and 375px; this decision sets
  what "passing" means at 375px for each.
- **Scope:** all three views; the deployed-UI gate.
- **Do not:** treat "responsive" as a uniform requirement across surfaces, and
  do not let the Scorecard header inherit the exploration surfaces' mobile
  allowances. It is the one component with no degradation budget.

---

## Output Formats

[Decisions about deliverable formats, structure, organization]

---

## Writing & Voice

[Voice, style, terminology decisions specific to this project]

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

This preserves the history of why something is the way it is.
