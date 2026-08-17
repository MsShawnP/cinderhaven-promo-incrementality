# Test conventions for this project's `tests/`

This file applies when Claude is working in
`cinderhaven-promo-incrementality/tests/`.

## The test that is not optional

`assert_no_truth_access` over `src/` runs in CI on every push. It is the
credibility of the accuracy view — without it, "the estimator was blind" is
an assertion about good intentions.

```python
from cinderhaven_promo_response.testing import assert_no_truth_access

def test_estimation_path_is_blind():
    assert_no_truth_access("src", exclude=("src/accuracy/",))
```

Two rules around it:

- **The exemption is named, narrow, and singular.** One module — the accuracy
  view — sees truth. A directory-wide or glob exemption turns the gate off
  while looking like it is on.
- **It must be shown to fail.** Commit a deliberate violation fixture, watch
  CI go red, then remove it. A gate never demonstrated to fail is not
  evidence. This is how the upstream package proved all four of its
  quarantine layers.

Do not mark it `skip` or `xfail`. Do not make it conditional on anything.

## What gets tested

- Public-facing functions and behaviors.
- Every estimator: at least one property it must hold, and its behavior on
  the edge cases that break baselines — an event in the first weeks of the
  series, a SKU with a sparse authorization window, a store that never
  complied.
- Anything in FAILURES.md that has a corresponding fix in code.

## What doesn't need a test

- Glue code (one-line wrappers, trivial mappings).
- Configuration constants.
- Pure type definitions.

## Structure

- Mirror the source tree: `src/foo/bar.py` → `tests/test_bar.py`.
- One file per source module unless tests are huge.
- Group related tests by behavior, not by function name.

## Test names

- Describe what the test verifies, in plain English.
- Pattern: `test_<behavior>_when_<condition>`.
- Bad: `test_estimator_1`, `test_roi`.
- Good: `test_baseline_excludes_promo_weeks_when_event_spans_year_end`,
  `test_accuracy_refuses_truth_from_a_different_generation`.

## Assertions

- One concept per test. If a test asserts five unrelated things, split it.
- Assertions print useful failure messages — what was expected, what was got.
- **Assert properties, not golden numbers.** `assert roi > 1.0` for
  `clean_winner` survives a legitimate refactor; `assert roi == 4.21` locks
  in whatever the code did on the day it was written, including its bugs.
  Where a pinned figure genuinely is the point, say so in a comment and name
  the file it is pinned in.
- A test that asserts the seeded stories are found must also assert something
  about the background distribution. Finding four planted outliers proves
  nothing on its own.

## Setup and teardown

- Prefer fresh state per test over shared mutable state.
- `pr.load()` is ~8.5s cold and ~0.6s warm. Load once per session via a
  fixture rather than per test.
- If a test needs truth, it goes in a clearly named file and calls
  `assert_aligned_with_observed` first — same rule as production code.

## Mocks and fakes

- Mock at the boundary (filesystem, time), not internal pure functions.
- Do not mock the data package to make a test faster. Its whole value is
  being real data with known truth; a mocked version tests nothing.
- If you mock a function, comment why — what real behavior would be
  unreliable in this test.

## Running

- Tests must be runnable with a single command. Document it in README.md.
- A failing test is more useful than an unrun test.
- No test is skipped. A skipped test reports green and satisfies a slice
  gate falsely.

## When a test fails

- Read the actual output, not what you expected to see.
- Bisect: which change broke it?
- Don't suppress with `skip` or `xfail` without a PLAN item to come back.
