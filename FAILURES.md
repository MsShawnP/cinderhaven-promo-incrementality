# cinderhaven-promo-incrementality — Failure Log

What was attempted that didn't work, why it didn't work, and what was
tried next.

Lower bar than DECISIONS.md — capture failures even when they didn't
produce a durable rule. The whole point: future-you (or future-Claude)
shouldn't re-attempt dead ends because the lesson got lost.

Worth carrying in from the data package build, because the pattern held four
times out of four: **every problem that looked like it needed a coefficient
tuned turned out to be a measurement or modelling error.** Nothing was ever
calibrated to hit a target. Expect the same here — an estimator whose error
looks wrong is more likely measuring the wrong thing than needing a knob.

---

## Format

### YYYY-MM-DD — [One-line failure description]

**Attempted:** [What was tried]

**Why it didn't work:** [Concrete reason, not "it broke." If the
failure mode was technical, name the specific issue. If the failure
mode was scope or approach, name that.]

**What we tried instead:** [The next attempt, which may also have
failed and may have its own entry below]

**Status:** Resolved / open / abandoned

**Tags:** [keywords for future text-search — e.g., "rendering, pandoc,
quarto" or "scope, scrollytelling, decoration"]

---

## Entries

[New entries get added here, most recent at the top]
