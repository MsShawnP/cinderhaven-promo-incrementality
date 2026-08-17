# cinderhaven-promo-incrementality — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

**This arc: choose the stack and prove the spine.** End with a logged stack
decision and one view — the ROI Scorecard — running end-to-end on real data,
with the truth gate green in CI.

The full five-view arc is defined by the planning process, not here. This
plan is deliberately short until that runs.

## Why this arc, why now

The data package shipped at v0.1.0 with a causal promo signal and quarantined
ground truth, so the riskiest unknown ("does the data support the claims?")
is already a settled fact. The next riskiest unknown is the stack: this tool's
value is a story-driven waterfall and an accuracy view, and the wrong stack
makes both expensive. Deciding it after building three views is how a rewrite
happens.

Proving one view end-to-end before the other four is what keeps that decision
honest. A stack chosen on paper and never exercised is still an unknown.

## Business question this arc answers

How wrong is a trade-promotion incrementality estimate, and can that error be
shown rather than claimed?

## Goal — clarified 2026-08-17

Output of `/clarify`. Refines the arc goal above; does not replace it. These
are requirements for the stack decision, not the decision itself — that runs
through `/office-hours`, `/plan-ceo-review` and `/plan-eng-review`.

**Audience and framing**

- Primary audience is **prospective clients** — specialty food brands, trade
  marketing leads. This is a portfolio flagship, not an internal tool.
- **The tool is the product.** No landing page, no narrative wrapper in this
  repo. A case study on `lailarallc.com/work` carries the story separately.
- The front door is **the money, not the method**. Open on the ROI Scorecard;
  the accuracy view sits one click deeper as the proof behind the numbers. It
  closes the sale rather than opening it.

**The 30-second rule — governs arrival**

The ROI Scorecard's first paint must be readable by a CEO or CFO in 30 seconds
or less: **verdict line, one chart, three numbers** (the Question Engine
pattern). Exploration is opt-in depth *after* the verdict, never a prerequisite
for it. The zero-state — before any filter is touched — is a deliverable in its
own right, not a placeholder. "Genuine exploration" must not become "requires
exploration."

**Data shape**

- Python computes at **build time** and writes small precomputed artifacts.
- The 1,340,462 scan rows **do not ship to the browser**. DuckDB-WASM is out.
- Anything a view needs is precomputed; a view that wasn't precomputed needs a
  rebuild, and that is an accepted cost.

**Interaction**

Genuine exploration: filters that **persist across views**, deep-linkable URLs,
comparison mode. This is shared client state across routes — an application,
not a set of pages with widgets.

**Constraints**

- Python engine — fixed, see DECISIONS.md. Not revisitable.
- `cinderhaven-promo-response` pinned at v0.1.0, public API only.
- Static hosting. Lailara design system governs all visual output.
- Timeline **open-ended** — done when it's good. The only budget risk is
  stalling out, not overrunning a date.

**Two assumptions surfaced and revised**

1. *Scrollytelling is required.* — **False.** It appears twice in DECISIONS.md
   as a reason to reject Dash and favor SvelteKit, but nothing in CLAUDE.md or
   PLAN.md requires it. Dropped from the stack rationale entirely. This
   **weakens** the SvelteKit case.
2. *All 1.34M rows ship to the browser via DuckDB-WASM.* — **False.** Build-time
   precomputation makes the payload a few hundred KB. This removes the payload
   risk that partly justified Observable Framework's data-loader model.

**What this does to the stack question**

The deciding axis moved from *narrative ambition* to *cross-view state*.
Persistent filters, deep-linkable URLs and comparison mode are the one
requirement set where SvelteKit earns its extra week over Observable Framework —
whose per-page reactive model is least suited to shared cross-route state.
**Unverified:** Framework's actual cross-route state story. Check it at
`/plan-eng-review` rather than assuming.

Dash is now clearly out: an always-on server for data that never changes, and
Plotly defaults fighting the design system.

**Still open**

- **Mobile.** The global deployed-UI gate requires checking at 1440px *and*
  375px. A cannibalization matrix at 375px is a hard design problem. Working
  assumption is graceful reduction on phones, not full parity. Not confirmed.

## Tasks

Work in vertical slices — for this tool a slice is one view end-to-end
(estimator → accuracy measurement → rendered view → test), not a horizontal
layer.

- [ ] **Stack decision** — run the planning process (`/clarify`, then
      `/office-hours`, then `/plan-ceo-review` and `/plan-eng-review`).
      Log the outcome in DECISIONS.md with the alternatives that were
      rejected and why. Constraints and the three candidate stacks are
      already recorded in DECISIONS.md as a pending decision — start there,
      don't re-derive them.
- [ ] **Repo skeleton for the chosen stack** — dependency manifest with the
      upstream package pinned, test runner, lint config, `.gitignore`
      additions. Nothing rendering yet.
- [ ] **CI with the truth gate, before any estimator exists** — a workflow
      that installs the package and runs `assert_no_truth_access` over
      `src/`. It must be proven to *fail*: commit a deliberate violation
      fixture, watch CI go red, then remove it. A gate never shown to fail
      is not evidence.
- [ ] **Slice 1 — ROI Scorecard end-to-end.** Chosen deliberately as the
      first slice rather than Baseline Builder: it is the shallowest
      estimator (event-level, 131 rows, `accrued_cost` already supplied) and
      the deepest exercise of the stack — a ranked table, a per-event
      waterfall, and an accuracy panel. It answers "is this stack right?"
      at the lowest modelling cost.
- [ ] **Accuracy view, first pass** — score slice 1's estimates against
      `truth.load_truth()`, guarded by `assert_aligned_with_observed`. The
      one module that imports truth; exempt it by name in the CI gate.

## Out of scope for this arc

- **The other four views** — Baseline Builder, Lift Split, Net Lift,
  Portfolio. They are the next arc. Sequencing them now would be planning
  against a stack that isn't chosen yet.
- **Editing `cinderhaven-promo-response`.** It is released at v0.1.0 and is
  a separate repo. A data gap found here is logged here and released there.
- **Deployment and the public subdomain.** Nothing deploys until a view is
  worth looking at. The Lailara design system and the deployed-UI gate in
  the global CLAUDE.md apply when it does.
- **Client mode / brand wrapper.** The ~4-day wrapper phase in
  `incrementality-tool-notes.md` comes after the views work.
- **Household-panel integration** for buyer-level pantry-load validation.
  Follow-up once scan-level views are live.

## Definition of done for this arc

- [ ] Stack decision logged in DECISIONS.md, naming the rejected
      alternatives and the reason — not just the winner
- [ ] `assert_no_truth_access` runs in CI over all estimation code, and has
      been **demonstrated to fail** on a deliberate violation
- [ ] ROI Scorecard renders from `pr.load()` with no hand-entered figures
- [ ] Its accuracy panel reports error against `truth.load_truth()`, with
      `assert_aligned_with_observed` called before any number is shown
- [ ] The background distribution is visible alongside the seeded stories —
      finding `clean_winner` is not a result on its own
- [ ] Same package version + same seed reproduces the same numbers
- [ ] Tests run with a single documented command, and none are skipped

---

## Arc history

When an arc completes, archive its goal, completion date, and outcome
here. Then start a new arc above. Provides continuity without bloating
the active plan.

<!-- No completed arcs yet. -->

---

## Improvement history

Track when this project was reviewed and improved via /improve.
Each entry records what was found, what was fixed, and when to
check again.

<!-- Entries are added by /improve — don't delete this section -->
