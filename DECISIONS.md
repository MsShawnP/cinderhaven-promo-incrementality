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

### 2026-08-17 — PENDING: front-end stack. Deferred to the planning process.

**Status: open. This is the first task in PLAN.md.** Recorded here so the
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

---

## Data & Schema

### 2026-08-17 — Pin the upstream package version.

- **Why:** An accuracy number is meaningless without knowing which data
  generation it scored against. The package is seed-locked, so a version
  bump that changes generation changes every reported error.
- **Scope:** dependency manifest; any published accuracy figure.
- **Do not:** report an accuracy number without recording the
  `cinderhaven-promo-response` version and seed alongside it.

---

## Visualization

[Chart conventions, palette decisions, interactivity choices. The Lailara
design system at `~/projects/reference/lailara-design-system/LAILARA_DESIGN_SYSTEM.md`
governs colors, typography and chart rules; entries here record only
project-specific choices on top of it.]

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
