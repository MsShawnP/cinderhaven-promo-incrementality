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

## 2026-08-18 13:31

**What changed:** Task 3 done — two-job CI live, truth gate proven green and
the data contract proven red for the documented reason, with real runner
evidence.

**Why:** Local green proved the gate function; only a push proves the workflow
wiring, the secret, and the `--no-deps` install work on a runner. It took three
runs to get clean evidence — each failure was a real setup defect the CI caught.

**State:** Green — `truth-gate` (AST over `src/`, `--no-deps`, pandas-absent
asserted; demonstrated to fail via a planted `src/` violation plus two permanent
fixtures covering both channels). Red by design — `data-contract`, failing only
at the test step on the upstream `FIGURES.md` cold-cache defect, after auth +
install + pin-verification all pass. Three setup bugs found and fixed along the
way: secret on the wrong repo (upstream, not consumer) → added a token preflight;
secret name mismatch (`PROMO_RESPONSE_READ` vs `..._TOKEN`) → aligned code to the
existing name; token regenerated and re-verified on a runner. Exemption list is
now a named file (`src/incrementality/accuracy.py`), not a directory, with an
invariant test. 10 tests pass locally, ruff clean. Untouched: SvelteKit scaffold,
any estimator, the walking skeleton.

**Next:** Task 5 — the walking skeleton. One Python-computed number → JSON →
rendered by the real front end → deployed to a real static host. This is what
actually answers "is this stack right?" and is the cheapest insurance against
the stall risk. Scaffold SvelteKit + adapter-static first.

---

## 2026-08-18 14:40

**What changed:** Re-pinned the upstream package to v0.1.1 (7cfe95c); the
data-contract CI job is now green cold. CI is fully green.

**Why:** Upstream v0.1.1 fixed the FIGURES.md cold-cache crash that made the
data job red by design. Moving the pin closes the loop the red job held open.

**State:** pyproject.toml pins 7cfe95c (v0.1.1, peeled commit) with updated
human comments; test_data_contract.py asserts 0.1.1 and its docstring records
the fix; CI job comments no longer say "expected red". Full consumer suite: 10
passed on a cold cache — every pr.load() test included. Truth gate still green.
Repo skeleton, CI, and the re-pin are all done. Untouched: SvelteKit scaffold,
any estimator, the walking skeleton.

**Next:** Task 5 — the walking skeleton. One Python-computed number → JSON →
SvelteKit (adapter-static) → Cloudflare Pages. Scaffold the front end first.

## 2026-08-19 11:40

**What changed:** Walking skeleton built end to end — Python computes observed
facts → deterministic JSON → SvelteKit adapter-static prerenders them to static
HTML. Both halves pushed (e3d2bd4, 58f3be9). Deploy is the only remaining step.

**Why:** Task 5 is the arc's real "is this stack right?" test and the cheapest
insurance against the stall. Proving the pipe before any estimator means the
stack fails fast and cheap if it's going to.

**State:** Working — full pipe verified: real numbers (13,838,493 units, 131
events, 1,340,462 rows, v0.1.1) baked into static build/index.html at prerender
time, not fetched at runtime. `scripts/build.sh` runs pipeline-first with set -e
so no stale artifact ships. 16 Python tests green, ruff clean, front-end build
green. Two determinism bugs caught by tests, not shipped (CRLF translation;
redundant int cast). No D3 yet (renders one number; dep arrives with first
chart). Untouched: any estimator, Method 0, ROI Scorecard, accuracy view.
Pending on Shawn: (1) platform paste push — committed 421beef in the platform
repo, held; (2) Cloudflare deploy creds.

**Next:** Deploy via Path B — build in GitHub Actions, `wrangler pages deploy
web/build`. Blocked until Shawn creates a Cloudflare API token + account ID and
adds them as CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID repo secrets, plus a
Direct-Upload Pages project named cinderhaven-promo-incrementality. Then write
the deploy job (folding in the Node-20 action-version bump).

## 2026-08-19 13:27

**What changed:** Walking skeleton deployed and verified live — CI's deploy job
builds and ships to Cloudflare Pages; the served HTML carries the pipeline's
prerendered numbers. Task 5 done, deploy included.

**Why:** Closes the arc's real "is this stack right?" question with a live URL,
not an assertion. Biggest cut yet to the named stall risk.

**State:** Green end to end. https://cinderhaven-promo-incrementality.pages.dev
returns 200 with 131 / 1,340,462 / 13,838,493 / 0.1.1 baked into static HTML at
prerender. CI three jobs green (truth-gate, data-contract, deploy). Deploy job
gated needs:[truth-gate,data-contract] + push-to-main; preflights now name every
credential failure (wrong-repo PAT → empty token → malformed account id, each
caught with a clear message). Platform paste pushed (421beef). This .pages.dev
is the unstyled plumbing check — NOT the flagship; Lailara design system + the
two-method public-deploy gate apply before any lailarallc.com subdomain.
Untouched: any estimator, ROI numbers, truth, the accuracy view.

**Next:** Slice 1 — ROI Scorecard on Method 0. Pre-registration rule governs
commit order: Commit 1 is docs/estimators.md (Method 0 spec, cited, no code),
committed before any code loads truth. Then observed-only estimation pipeline
with the exact portfolio reconciliation test, then the Scorecard view. Truth
gate stays green throughout; no accuracy numbers in this slice.

## 2026-08-19 17:07

**What changed:** Slice 1 spec frozen — ROI framing A confirmed (#7), giveaway
share added; upstream shipped economics() (v0.2.0 → v0.2.1 fix), consumer pinned
to v0.2.1, CI fully green. Ready to write Method 0 pipeline code.

**Why:** #7 was the last open modeling fork (manufacturer margin vs retail);
confirming it froze the pre-registration spec so the estimator can be built and
tagged as blindness evidence. economics() is the demand-free margin basis.

**State:** Frozen spec at docs/estimators.md (framing A: numerator = mfr margin
wholesale−COGS on incremental units; giveaway = decomposition of accrued_cost,
displayed as % of trade dollars). Upstream v0.2.1 (economics() + lazy-pandas fix
+ regression test, 254 tests). Consumer pinned 11caa13, all 3 CI jobs green.
Commits 1–2 of slice 1 are spec-only, no estimation code yet. Untouched: the
Method 0 pipeline, the import-ban check, the Scorecard view.

**Next:** Method 0 pipeline. First land the supplementary import-ban check
(bans config/constants in src/, alongside the truth gate), then the estimation
module: baseline → incremental units → margin (via economics()) → ROI →
portfolio roll-up with the exact reconciliation test. Then the artifact writer.

## 2026-08-19 17:22 — /wrap

**Started from:** Docs-only repo, stack decided; task 2 (skeleton) next.

**Did:** Skeleton (task 2), two-job CI with truth gate proven-to-fail (task 3),
walking skeleton deployed live to Cloudflare Pages (task 5). Three upstream
releases — v0.1.1 (FIGURES.md cold-cache fix), v0.2.0 (economics() accessor),
v0.2.1 (pandas-eager-import regression fix) — consumer re-pinned through each.
Slice 1 pre-registration: froze docs/estimators.md (Method 0), resolved 3
modeling forks (continuous units + integer-cent round-half-even; all-131 with
phantom marked; economics() margin basis), confirmed ROI framing A (#7), landed
the generator-import ban. Platform canonical paragraph pushed at v0.1.1 SHA.

**State:** Consumer pinned upstream v0.2.1, all 3 CI jobs green, skeleton live.
Slice 1 spec frozen + import-ban guardrail in. Upstream v0.2.1, 254 tests.
Untouched: the Method 0 estimation module, the Scorecard view.

**Next:** Write src/incrementality/method0.py — baseline (8-wk pre-period,
promo weeks excluded, insufficiency flag) → incremental units → margin via
economics() → integer-cent round-half-even at row grain → portfolio roll-up
with the EXACT reconciliation test + property tests (sign, phantom→~0 lift,
estimable-count labeling) + giveaway-share per event. Then artifact writer,
then Scorecard view. Tracked guard-gap: deploy token value-validity is only
checkable at runtime (wrangler), not preflighted — acceptable, noted.

## 2026-08-19 (later) — Method 0 pipeline + Scorecard artifact landed

**What changed:** The Method 0 estimation module and the ROI Scorecard artifact
writer are built, tested, and committed (3 commits: 33d59f2 spec correction,
e08532c estimator+tests, 9ee2b84 writer+wiring). Slice 1's pipeline is done end
to end; only the SvelteKit view remains.

**Why:** Slice 1's pipeline — the frozen spec made real. Implemented cold from
`docs/estimators.md` (the spec's own completeness test). One genuine spec bug
surfaced during implementation and was corrected pre-freeze (see below).

**The spec bug — §2.4 giveaway share (asked, user chose volume share).** The
frozen formula divided a *retail* giveaway (`baseline×(regular−promoted)`) by the
*manufacturer* `accrued_cost` — mixed dimensions, "shares" to 936% (clean_winner,
smallest subsidy base). Corrected to `Σ baseline_units / Σ observed_units` over
complied rows (discount is constant within an event, so it cancels). Scan-funded
events keep the "% of trade dollars" copy (accrued = rate×promoted units makes it
exact); fixed-funded are volume-only; net-dip events (share>1) flagged. Logged as
a **pre-freeze correction, not a re-run** (no truth loaded yet). DECISIONS +
FAILURES entries written. Two adjacent gaps also clarified pre-freeze: event
estimability (≥1 sufficient store-event → N_estimable=129) and zero accrued cost
(3 events → ROI null, lost_money still defined).

**State — Method 0 numbers (v0.2.1, this generation):** portfolio ROI 1.132
(naive, expected rosy), net incremental margin $118,200.37, accrued spend
$104,425.13, **64 of 129 estimable events lost money**, 2 of 131 not estimable
(PRE-0048/PRE-0054, series-start). Reconciliation ties exactly (11,820,037 cents,
event-grain == row-grain). **40 tests pass, ruff clean, truth gate + import ban
green over all of src/, artifact byte-identical across builds.** scorecard.json
(scorecard/v1) written to web/src/lib/data/ (gitignored), wired into build.sh as
a pipeline-first step. NOT pushed — CI has not run these commits.

**Untouched:** the SvelteKit Scorecard view (deliberately stopped before it), the
dependency-direction test (PLAN, still `[ ]`), Method 1 (deploy gate needs two
baseline methods), the accuracy view.

**Next:** The ROI Scorecard **view** — SvelteKit consuming scorecard.json. First
paint must satisfy the 30-second rule (verdict line, one chart, three numbers)
before any filter, and the header must fully work at 375px. Ranking is a view
choice (artifact is in canonical promo_id order); non-estimable events shown
unranked and marked; every portfolio figure labeled "of 129 estimable events".
Then the dependency-direction test, then Method 1 (comparable-store) to clear the
two-method public-deploy gate.

## 2026-08-21 — Scorecard view landed (header + ranked list); all pushed, CI green

**What changed:** Built the SvelteKit ROI Scorecard view end to end and pushed
everything. Method 0 pipeline (33d59f2/e08532c/9ee2b84) plus the view: a9fc411
(header) and b2e3c4d (ranked list). All on main, CI green including the Cloudflare
Pages deploy.

**Why:** Closes slice 1's user-visible half — the 30-second verdict front door on
the Method 0 artifact — on the vendored Lailara brand frame. "go — Scorecard view
per PLAN."

**State — the view (web/src/routes/+page.svelte):**
- **Header (30-second surface):** eyebrow "ROI Scorecard · Method 0"; verdict
  "64 of 129 promotions lost money."; three numbers (trade spend $104,425, net
  incremental margin $118,200, portfolio ROI 1.13×); one chart — the 129 estimable
  events by return tier, a red Tokyo "lost money" bar (64) against three teal
  Hong-Kong profit tiers (39/17/9). DOM bars, not SVG (vector-crisp for print,
  natively responsive — deviation from the SVG-charts rule, noted, to meet the
  hard 375px constraint).
- **Ranked list:** 129 estimable events by net margin; net/spend/ROI/giveaway per
  row; lost-money rows carry a Tokyo leading rule + red ROI; the 4 seeded stories
  and phantom/unplanned events badged (marked, NOT claimed "found"); 2 non-estimable
  events listed unranked beneath. Filters DEFERRED (cross-view state = Event Anatomy
  arc).
- **Frame:** vendored lailara-frame.css + 8 self-hosted woff2 into web/static/lailara/;
  brand header/footer in +layout.svelte; canvas on body. Skeleton demo moved to
  /skeleton. Shared formatters in web/src/lib/format.js.
- **Verified (DOM, not screenshot — see limitation):** both fonts load, palette
  correct, no page horizontal scroll at 1280 or 375, header collapses to one column
  on mobile, table scrolls inside its own container, production build bakes all real
  numbers + 129 rows into prerendered HTML.

**Limitation:** the Browser pane was not displayable this session (0-width /
non-compositing), so no screenshot was captured. Everything was verified through
read_page + computed styles + build output. **A human visual review at 1440 and
375 is still owed** before this counts as design-gate-passed. Dev server: `web-dev`
in .claude/launch.json → http://localhost:5173.

**Untouched:** filters, the dependency-direction test (PLAN `[ ]`), Method 1
(deploy gate needs two baseline methods), the accuracy view, the one-timed-session
30-second verification with a trade-marketing person.

**Next:** pick one — (a) the dependency-direction test (small, closes a PLAN item
and a blindness guarantee), (b) Method 1 comparable-store baseline (unblocks the
two-method public-deploy gate), or (c) a human design pass on the Scorecard once
the Browser pane is viewable. Event Anatomy + filters are the following arc.
