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

### 2026-08-18 — `pr.load()` raises on first call in any fresh install of v0.1.0

**Attempted:** Install `cinderhaven-promo-response` from the pinned git SHA
(`70021d4`, v0.1.0) into a clean venv and call `pr.load()` — the first line of
this project's consumer contract.

**Why it didn't work:** `generate.py:write_generation_block` unconditionally
reads `FIGURES.md` from the package root after writing the parquet artifacts.
`FIGURES.md` exists in the upstream **source repo** (4,605 bytes) but is **not
packaged into the wheel**, so in an installed package the path resolves to
`site-packages/FIGURES.md`, which does not exist:

    FileNotFoundError: [Errno 2] No such file or directory:
    '...\.venv\Lib\site-packages\FIGURES.md'

The failure is **deterministic on a cold cache and invisible afterwards.** The
crash happens *after* the artifacts are written, so the failed run leaves a
valid `.cache/` behind and the *second* call succeeds in ~0.9s. Verified by
moving `.cache/` aside and re-running: crash, then success. That is why it did
not surface as "the package is broken" — locally it looks like one bad run.

**Why it matters here, not just upstream:** every consumer that installs rather
than checks out hits this exactly once. **CI is a fresh container with a cold
cache every time**, so the data job fails on first `pr.load()` — permanently,
not flakily, since nothing persists the cache between runs. PLAN's instruction
to split the truth-gate job from the data job now has a second, concrete
reason: the gate is pure AST parsing and stays green regardless of this.

**What we tried instead:** Nothing yet — and deliberately not a local patch.
Editing the data package from this session is scope creep by CLAUDE.md; it is
released at v0.1.0 and lives in a separate repo. This is a finding logged here
and a release to plan there. Options for that release, not decided:
package `FIGURES.md` as package data, make `write_generation_block` a no-op
when the file is absent, or confine it to the source-checkout path.

**Workaround available if the CI task lands before that release:** call
`pr.load()` once and tolerate the first failure, or ship a warm cache. Both are
ugly; neither should be adopted without an entry in DECISIONS.md, because a
consumer that swallows an exception from its data package is exactly the kind
of silent-failure path this project's premise argues against.

**Defect class — this is the second instance, so it is a pattern, not an
incident.** *A file the package reads at runtime is not in the built artifact.*
Same class as the brand-fonts bug found in the 2026-07-28 portfolio audit:
`datascope` and `data-hygiene-auditor` shipped `brand_fonts/__init__.py` but
not the TTF/woff2 files, because `tool.setuptools.package-data` never declared
them. Font embedding worked from a source checkout and nowhere else.

The two failure *symptoms* are opposite, which is why the first one did not
teach the lesson: the fonts failed **silently** — `_font_face_css()` did
`if not path.exists(): continue`, so every pip-installed report fell back to
Georgia/Arial and the guarding test passed regardless. `FIGURES.md` fails
**loudly**, but only on a cold cache, and the crash leaves a working cache
behind that hides it on every subsequent call. Silent-and-always versus
loud-and-once. The shared cause is the same line of `pyproject.toml` in both
repos.

**The testable rule this yields, for the release checklist:** *every file the
package reads at runtime is present in the built artifact* — asserted against
the built wheel, not the source tree. Both bugs were invisible to a test run
from a checkout and both were caught, or would have been caught, by installing
the wheel into a clean environment and exercising the path that reads the file.
The 2026-07-28 audit verified this empirically against the built wheel; that is
the technique worth carrying forward.

**Status:** Open — upstream defect, unpatched. Local dev is unblocked (the
cache is warm). CI is blocked until the upstream release or a logged workaround.

**Tags:** upstream, cinderhaven-promo-response, packaging, FIGURES.md,
pr.load, cold-cache, ci, wheel, package-data

### 2026-08-19 — v0.2.0 economics() broke the consumer's --no-deps truth gate

**Attempted:** Ship `economics()` upstream (v0.2.0) with `import pandas` at the
top of `economics.py`, and `from .economics import economics` in the package
`__init__`.

**Why it didn't work:** That made `import cinderhaven_promo_response` require
pandas. The consumer's truth-gate CI job installs the package with `--no-deps`
(dependency-light, never flakes on wheel resolution) and imports it to run the
AST check — with no pandas present, the import raised and the gate job went red.
The consumer's own `Confirm the gate imported without its data layer` step
caught it on the re-pin push.

**What we tried instead:** v0.2.1 — import pandas lazily *inside* `economics()`,
restoring the package's import-without-pandas property. Added a regression test
that spawns a fresh interpreter, imports the package, and asserts pandas is
absent, so the property cannot regress silently. Consumer re-pinned v0.2.0 →
v0.2.1 (v0.2.0 was never green in CI, so it was superseded, not shipped).

**The pattern, now four-for-four:** the consumer gate caught the upstream defect,
the fix landed upstream with its own regression test, and nothing was papered
over downstream. Same shape as the FIGURES.md cold-cache catch and the
brand-fonts package-data catch — a downstream guard surfacing an upstream
packaging gap. See DECISIONS.md, "No downstream paper-over."

**Status:** Resolved (v0.2.1).

**Tags:** upstream, cinderhaven-promo-response, packaging, pandas, lazy-import,
--no-deps, truth-gate, regression, economics

### 2026-08-19 — First §2.4 draft mixed retail-price subsidy into a manufacturer-margin ROI

**Attempted:** Draft the Method 0 subsidy math as
`baseline_units × (regular_price − promoted_price)` netted against margin.

**Why it didn't work:** The ROI numerator is *manufacturer* margin
(wholesale − COGS), which never touches retail price; the shelf discount is the
retailer's move. Netting a retail-price giveaway against a manufacturer-margin
numerator double-counts (for scan_based the baseline subsidy is already inside
`accrued_cost`, the denominator). Caught during the #7 verification, before the
spec was frozen or tagged.

**What we tried instead:** Framing A — numerator is manufacturer margin on
incremental units; the giveaway is a *decomposition of accrued_cost* (the
denominator), displayed as a share of trade dollars, never netted. Same lesson
the upstream calibration bug taught (retail margin ≠ manufacturer margin, ~2.8x).

**Status:** Resolved before freeze; framing A written into docs/estimators.md §2.4.

**Tags:** modeling, roi, manufacturer-margin, subsidy, pre-registration, near-miss

[New entries get added here, most recent at the top]
