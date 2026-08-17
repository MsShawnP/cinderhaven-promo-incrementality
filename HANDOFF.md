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
