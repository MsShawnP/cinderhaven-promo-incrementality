#!/usr/bin/env bash
# Build the static site, in the order the build contract requires.
#
# The Python pipeline runs FIRST: the front end imports artifacts the pipeline
# writes (web/src/lib/data/*.json — skeleton.json, scorecard.json), which are
# gitignored and regenerated, never committed. A build that skipped this step
# would either fail at import or ship yesterday's numbers — the latter is the
# outcome PLAN.md forbids for a tool whose premise is numeric credibility.
#
# `set -e` makes any failure abort the whole build loudly. There is no path here
# that swallows a pipeline error and continues to `npm build`.
#
# Assumes `python` resolves to an interpreter with the pinned package installed,
# and that `npm ci` has been run in web/. The deploy pipeline (a later PLAN task)
# sets those up; locally, activate .venv first — see README.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"

echo "[1/3] pipeline: walking-skeleton artifact (Python)"
python -m incrementality.build_skeleton

echo "[2/3] pipeline: ROI Scorecard artifact (Python, Method 0)"
python -m incrementality.build_scorecard

echo "[3/3] front end: static build (SvelteKit adapter-static)"
npm --prefix web run build

echo "done — static site at web/build/"
