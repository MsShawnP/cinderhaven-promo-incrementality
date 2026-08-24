"""Truth flows one way: nothing outside the accuracy module may import it.

The upstream truth gate (`assert_no_truth_access`) is **per file**. It exempts
the accuracy module by name, so that one module is allowed to import truth. But
an estimator that imports the accuracy module reaches truth at runtime while its
own file's AST stays clean — the gate passes and the estimator is no longer
blind. See DECISIONS.md, "Truth flows one way. Nothing may import the accuracy
module."

This closes that hole from the other side. If **no** file under `src/` (other
than the accuracy module itself) imports the accuracy module directly, then
nothing reaches it transitively either — there is no first hop. So a per-file
direct-import scan is the complete guarantee.

This guard was stood up **before** the accuracy module existed,
demonstrated-to-fail, so it was already in place the moment that module landed —
the same discipline that stood up the truth gate before the first estimator
existed. The module now exists and is the live sink this guard protects.
"""

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = _REPO_ROOT / "src"
FIXTURES = _REPO_ROOT / "tests" / "fixtures"

# The single module allowed to import truth (the truth-gate exemption). It is a
# sink: it may import truth, but nothing under src/ may import IT.
ACCURACY_MODULE = SRC / "incrementality" / "accuracy.py"


def _imports_accuracy(path):
    """Every import of the incrementality accuracy module in one file: (line, text).

    Catches all spellings — ``from incrementality.accuracy import x``,
    ``from incrementality import accuracy``, ``from . import accuracy``,
    ``from .accuracy import x``, ``import incrementality.accuracy``. Matches on
    the module name ``accuracy``; this repo has exactly one such module, so a
    bare-name match cannot collide with an unrelated third-party module.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            dots = "." * node.level
            if module.split(".")[-1] == "accuracy":  # from ...accuracy import <x>
                hits.append((node.lineno, f"from {dots}{module} import ..."))
            for alias in node.names:  # from incrementality import accuracy / from . import accuracy
                if alias.name == "accuracy":
                    hits.append((node.lineno, f"from {dots}{module} import accuracy"))
        elif isinstance(node, ast.Import):
            for alias in node.names:  # import incrementality.accuracy
                if alias.name.split(".")[-1] == "accuracy":
                    hits.append((node.lineno, f"import {alias.name}"))
    return hits


def assert_nothing_imports_accuracy(root):
    """Raise AssertionError if any .py under root — except the accuracy module — imports it."""
    root = Path(root)
    targets = sorted(root.rglob("*.py")) if root.is_dir() else [root]
    report = {}
    for target in targets:
        if target.resolve() == ACCURACY_MODULE.resolve():
            continue  # the sink itself, not a violator
        hits = _imports_accuracy(target)
        if hits:
            report[target] = hits
    if report:
        lines = ["a module outside the accuracy view imports it (truth would leak transitively):", ""]
        for target, hits in report.items():
            lines.append(f"  {target}")
            lines.extend(f"    line {ln}: {txt}" for ln, txt in hits)
        lines += [
            "",
            "The accuracy module is the one file allowed to import truth. Anything",
            "that imports it reaches truth at runtime while its own AST stays clean",
            "and the per-file truth gate passes. Truth flows one way — see DECISIONS.md.",
        ]
        raise AssertionError("\n".join(lines))


def test_nothing_outside_the_accuracy_module_imports_it():
    assert_nothing_imports_accuracy(SRC)


def test_src_is_not_empty_so_the_guard_is_not_vacuous():
    # A per-file scan over zero files passes trivially. src/ must actually hold
    # estimation modules for the guard above to mean anything.
    assert list(SRC.rglob("*.py")), "no modules under src/ — the guard is vacuous"


def test_guard_rejects_a_module_that_imports_the_accuracy_view():
    # The demonstrated-to-fail half: a fixture importing the accuracy module must
    # be caught, or the guard is indistinguishable from no guard.
    with pytest.raises(AssertionError):
        assert_nothing_imports_accuracy(FIXTURES / "violation_imports_accuracy.py")
