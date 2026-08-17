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
