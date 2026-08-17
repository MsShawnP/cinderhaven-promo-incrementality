# cinderhaven-promo-incrementality — Handoff Log

Session-by-session state. Updated by /log mid-session and /wrap at
session end.

For durable choices, see DECISIONS.md.
For the current work arc, see PLAN.md.
For things that didn't work, see FAILURES.md.

---

## 2026-08-17 — Project initialized

**Started from:** `cinderhaven-promo-response` v0.1.0, shipped and tagged.
Its HANDOFF.md carries the consumer contract this project builds on. Nothing
existed here before this session.

**Did:**
- Scaffolded the repo: CLAUDE.md, PLAN.md, HANDOFF.md, DECISIONS.md,
  FAILURES.md, README.md, `src/CLAUDE.md`, `tests/CLAUDE.md`, `.gitignore`.
- Recorded the consumer contract in CLAUDE.md so it survives without
  re-reading the other repo.
- Logged three settled decisions and one open one.

**The finding that shaped the scaffold:** `assert_no_truth_access` parses
source with `ast`. It can audit `.py` files and nothing else. So the hard
requirement — CI runs that gate on all estimation code — **forces the
estimation engine to be Python**. That is a constraint, not a preference,
and it narrows the stack question to the front end alone. Logged in
DECISIONS.md.

**A second leak the gate does not catch, worth knowing before any estimator
is written:** the gate denies `truth`. It does not deny
`cinderhaven_promo_response.config`, which holds the generator's own
coefficients — the answer key by another route. CLAUDE.md prohibits it
explicitly because nothing automated will.

**State:** Scaffold only. No stack, no dependency manifest, no CI, no code.
Three candidate stacks are written up in DECISIONS.md as a pending decision,
with the constraints and the "does this compute at request time?" prior
question stated, so the planning process starts from there rather than cold.

**Next:** Run the planning process to settle the stack — `/clarify`, then
`/office-hours`, then `/plan-ceo-review` and `/plan-eng-review`. Log the
outcome in DECISIONS.md naming the rejected alternatives, not just the
winner. Then the repo skeleton, then CI with the truth gate proven to fail
before any estimator exists.

---

## 2026-08-17 15:52

**What changed:** `/clarify` run on the stack decision; requirements appended
to PLAN.md as `## Goal — clarified 2026-08-17`.

**Why:** DECISIONS.md framed the stack question around scrollytelling and a
1.34M-row browser payload. Both turned out to be assumptions, not requirements,
and the real deciding constraint — persistent cross-view filter state — wasn't
recorded at all.

**State:** Requirements settled: client-facing flagship, no landing page in
this repo, build-time precomputed artifacts only (DuckDB-WASM out), 30-second
verdict on first paint, cross-view filters with deep-linkable URLs, open-ended
timeline. Dash eliminated. Stack still unchosen — DECISIONS.md entry remains
open and untouched, correctly. No code, no manifest, no CI.

**Next:** Run `/office-hours` to stress-test the concept, carrying two items:
the recommendation now points at SvelteKit (cross-view state, not narrative),
and mobile is still undecided — the 375px cannibalization matrix is unresolved.

---
