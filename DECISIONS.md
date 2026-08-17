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

---

## Positioning & Claims

Added 2026-08-17 during `/office-hours`. These entries govern what this
tool is allowed to claim and how the claim is worded.

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

- **Decision:** Carry money as **integer cents** through the pipeline. Units
  are already integers. The portfolio reconciliation asserts **equality**, not
  approximate equality.
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
