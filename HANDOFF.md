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
## 2026-08-17 16:51 — backfill (session ended without /wrap)

**What changed:** `/office-hours`, `/plan-ceo-review` and `/plan-eng-review`
run; scope collapsed to three views; stack decided.

**Why:** Entry written 2026-08-18 to close a hole — three commits landed
after the 15:52 entry and none were logged. No work was lost; the decisions
are all in DECISIONS.md. The log just didn't record them.

**State:** Stack settled — SvelteKit + D3, static, Cloudflare Pages; the
PENDING entry is struck through, not deleted. Scope is three views, not six.
Positioning, external-validity, mobile-split, integer-cents, artifact-label
and dependency-direction decisions all logged. Still docs-only: no manifest,
no CI, no code.

**Next:** Repo skeleton — task 2 in PLAN.md.

---

## 2026-08-18 09:45

**What changed:** Settled how the upstream package is installed: git URL
pinned to a commit SHA, not an editable local path and not a vendored wheel.

**Why:** An editable install off `../cinderhaven-promo-response` would make
"pinned at v0.1.0" describe the working tree rather than anything CI can
reproduce — it fails the pin decision it appears to satisfy. SHA over tag
name because annotated tags are mutable; the fleet pins SHAs everywhere else.

**State:** Nothing written yet. The SHA supplied in session, `a237910`, was
checked and is **wrong** — it is an ancestor of `v0.1.0` dated 75 minutes
before it, predating the plausibility audit and the retired-figure scan. The
v0.1.0 commit is `70021d4d472bdf4ab5132778472b4ca8a95fe0e8`. Still docs-only:
no manifest, no CI, no code. `cinderhaven_promo_response` is not importable
here — no venv exists yet.

**Next:** Write `pyproject.toml` pinning
`cinderhaven-promo-response @ git+https://github.com/MsShawnP/cinderhaven-promo-response@70021d4`,
plus pytest and ruff. Then create `.venv` and confirm `pr.load()` runs.

---
