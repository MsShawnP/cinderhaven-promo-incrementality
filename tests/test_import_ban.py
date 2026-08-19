"""The demarcation guardrail — the ban the truth gate does not cover.

`assert_no_truth_access` (upstream) denies `truth`. It says nothing about
`config` (the response coefficients) or `constants` (the baseline-demand
generator). Both are the answer key by another route, and importing either
from estimation code defeats blindness while the truth gate stays green — the
"structure walks out past the gate" hole. This check closes it: it AST-scans
`src/` and fails on any import of `config` or `constants` from the data package.

Same mechanism as the upstream gate (imports only, source-level), so it is
dependency-light and runs in the AST-only CI job. Kept demonstrated-to-fail
with permanent fixtures, like the truth gate — a guardrail never shown to fire
is not evidence.
"""

import ast
from pathlib import Path

import pytest

# The banned generator modules. `truth` is intentionally NOT here — it is the
# upstream gate's job; duplicating it would blur which check owns what.
BANNED = ("config", "constants")

_REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = _REPO_ROOT / "src"
FIXTURES = _REPO_ROOT / "tests" / "fixtures"


def _banned_imports_in(path):
    """Every import of a BANNED module in one Python file, as (line, name)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[-1] in BANNED:
                hits.append((node.lineno, module))
            for alias in node.names:  # from cinderhaven_promo_response import config
                if alias.name in BANNED:
                    hits.append((node.lineno, alias.name))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[-1] in BANNED:
                    hits.append((node.lineno, alias.name))
    return hits


def assert_no_generator_access(root):
    """Raise AssertionError if any .py under `root` imports config or constants."""
    root = Path(root)
    targets = sorted(root.rglob("*.py")) if root.is_dir() else [root]
    report = {}
    for target in targets:
        hits = _banned_imports_in(target)
        if hits:
            report[target] = hits
    if report:
        lines = ["estimation-path code imports the generator (config/constants):", ""]
        for target, hits in report.items():
            lines.append(f"  {target}")
            lines.extend(f"    line {ln}: imports {name!r}" for ln, name in hits)
        lines += [
            "",
            "config holds the response coefficients; constants holds the",
            "baseline-demand generator. Either one is the answer key. If a prior",
            "is needed, derive it from observed data or economics(), never here.",
        ]
        raise AssertionError("\n".join(lines))


def test_estimation_path_does_not_import_the_generator():
    assert_no_generator_access(SRC)


def test_check_rejects_a_module_that_imports_config():
    with pytest.raises(AssertionError):
        assert_no_generator_access(FIXTURES / "violation_imports_config.py")


def test_check_rejects_a_module_that_imports_constants():
    with pytest.raises(AssertionError):
        assert_no_generator_access(FIXTURES / "violation_imports_constants.py")
