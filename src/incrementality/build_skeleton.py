"""Walking-skeleton pipeline step: compute real numbers, write deterministic JSON.

This is not a deliverable metric. Its only job is to prove the pipeline end to
end — Python computes from `pr.load()`, writes an artifact, the front end
renders it — before any estimator exists. Everything here is **observed only**:
counts and a sum of an observed column. No baseline, no truth, no estimate, so
it stays blind and the CI truth gate audits it like any other src/ module.

Determinism (a stated arc requirement): the artifact carries no wall-clock and
no unseeded value. Same pinned package + same code → byte-identical JSON. That
is what the reproducibility test checks, so nothing here may introduce a
timestamp or a float.
"""

import json
from pathlib import Path

import cinderhaven_promo_response as pr

SCHEMA = "walking-skeleton/v1"

# <repo>/src/incrementality/build_skeleton.py -> <repo>
_REPO_ROOT = Path(__file__).resolve().parents[2]
# The SvelteKit app imports this at build time. Gitignored and regenerated:
# a committed copy could ship stale, which is the one outcome the build
# contract forbids (see PLAN.md). A missing file fails the front-end build
# loudly at import rather than shipping yesterday's numbers.
DEFAULT_OUT = _REPO_ROOT / "web" / "src" / "lib" / "data" / "skeleton.json"


def compute():
    """Observed-only facts. Returns a plain dict of JSON-ready primitives."""
    events, delta = pr.load()

    # Integer throughout — units are already integers upstream, and the
    # determinism requirement rules out any float in the artifact.
    total_observed_units = int(delta["observed_units"].sum())

    return {
        "schema": SCHEMA,
        # Provenance: which generation these numbers came from. Deterministic
        # given the pinned SHA; recorded because a figure without its data
        # version is unmoored (DECISIONS.md).
        "package_version": pr.__version__,
        "event_count": len(events),
        "scan_row_count": len(delta),
        "total_observed_units": total_observed_units,
    }


def serialize(payload):
    """Canonical JSON bytes: sorted keys, fixed separators, trailing newline.

    Byte-stability is the point, so the formatting is pinned, not left to
    defaults that could change how the artifact hashes.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"


def build(out_path=DEFAULT_OUT):
    """Compute and write the artifact. Returns the path written."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # write_bytes, not write_text: text mode applies platform newline
    # translation (LF becomes CRLF on Windows), which would make the artifact
    # differ byte-for-byte between a Windows dev machine and Linux CI. The
    # determinism requirement is byte-identical, so the bytes are written
    # exactly as serialized.
    out_path.write_bytes(serialize(compute()).encode("utf-8"))
    return out_path


def main():
    path = build()
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
