"""No published surface may carry a portfolio trade-spend-to-revenue ratio.

Upstream v0.4.0 made **per-unit** promotion economics defensible and left
**portfolio** economics deliberately unrealistic: only ~1% of the dataset's
volume runs on promotion against a real brand's 20-40%, so total trade spend is
0.0693% of revenue against a 15-25% industry norm. Upstream pins that figure as
a locked value explicitly marked NOT a gate, and pins spend/promoted-revenue
(6.7148%) as the one defensible ratio. Neither is quotable as a headline here.

Why a test and not a note in DECISIONS.md: the previous copy carried exactly
this defect for a full release. `+page.svelte` told the reader the portfolio
total "sits far below the 11-20%-of-revenue all-in trade figures cited
elsewhere" — an of-revenue comparison that invites the reader to compute a
ratio the data cannot support, and which blamed instrument scope (slotting,
allowances, deductions) when the dominant cause is calendar density. A note
would not have caught it; a scan does.

This lapses when upstream v0.5.0 lands the calendar-density fix. Until then the
tool leads with counts and per-event economics. See DECISIONS.md.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: Published surfaces. Front-end source is what a reader actually sees; README
#: is what a visitor reads first. Generated artifacts under web/src/lib/data are
#: excluded — they carry raw figures, not claims, and are gitignored.
SURFACES = sorted(
    [p for p in (ROOT / "web" / "src").rglob("*") if p.suffix in {".svelte", ".js", ".ts"}]
    + [ROOT / "README.md"]
    # The social card is a published surface too: it renders to og-card.png and
    # is what a scraper shows. It carries no figure by design (scrapers cache the
    # image, so a number here outlives the re-pin that moved it) and this keeps
    # that true.
    + [ROOT / "web" / "card-source" / "card.html", ROOT / "web" / "src" / "app.html"]
)

#: A percentage within ~60 characters of trade-spend vocabulary. The window is
#: what makes this a claim rather than a coincidence: "26% median error" near
#: the word "error" is fine; "0.07% of revenue" near "trade spend" is not.
_MONEY = r"(trade[- ]spend|spend|trade book|promo book)"
_SCALE = r"(revenue|sales|turnover|of the brand|brand)"
_PCT = r"\d+(?:\.\d+)?\s?%"

#: Prose only. `[^.{};:]` keeps a match inside one sentence and stops it
#: crossing CSS punctuation — `height: 100%` three lines above the word "sales"
#: is a stylesheet rule, not a claim, and an earlier draft of this scan flagged
#: exactly that. Every pattern requires spend vocabulary; a bare percentage near
#: "sales" is not enough.
_W = r"[^.{};:]{0,60}?"

PATTERNS = (
    re.compile(rf"{_MONEY}{_W}{_PCT}{_W}{_SCALE}", re.IGNORECASE),
    re.compile(rf"{_SCALE}{_W}{_MONEY}{_W}{_PCT}", re.IGNORECASE),
    re.compile(rf"{_PCT}{_W}of{_W}{_SCALE}", re.IGNORECASE),
    # The two upstream-pinned ratios, in any rendering.
    re.compile(r"0\.0?69\d?\s?%|6\.7\d?\s?%|0\.07\s?%", re.IGNORECASE),
    # The construction that actually shipped.
    re.compile(r"%[-–— ]?of[-–— ]?revenue", re.IGNORECASE),
)


def _hits(text):
    out = []
    for pat in PATTERNS:
        for m in pat.finditer(text):
            frag = " ".join(m.group(0).split())
            if len(frag) <= 200:
                out.append(frag)
    return out


@pytest.mark.parametrize("surface", SURFACES, ids=lambda p: str(p.relative_to(ROOT)))
def test_surface_carries_no_portfolio_spend_ratio(surface):
    hits = _hits(surface.read_text(encoding="utf-8"))
    assert not hits, (
        f"{surface.relative_to(ROOT)} states or implies a portfolio "
        f"trade-spend-to-revenue ratio: {hits}. Upstream pins this as not "
        f"quotable until the v0.5.0 calendar-density release. Lead with counts "
        f"and per-event economics instead. See DECISIONS.md."
    )


def test_the_scan_actually_fires():
    """A gate never shown to fail is indistinguishable from no gate.

    The first case is the exact sentence that shipped in +page.svelte and went
    undetected through a full copy audit.
    """
    shipped_defect = (
        "It excludes slotting, off-invoice allowances, and deductions, which "
        "is why it sits far below the 11\u201320%-of-revenue all-in trade figures "
        "cited elsewhere."
    )
    assert _hits(shipped_defect), "the scan misses the defect that actually shipped"

    for bad in (
        "Trade spend is 0.07% of revenue.",
        "Promotions consume 6.7% of sales.",
        "The promo book runs at 18% of revenue for a brand this size.",
    ):
        assert _hits(bad), f"scan missed: {bad!r}"


def test_the_scan_does_not_fire_on_legitimate_copy():
    """Percentages are everywhere in this tool. Only spend-vs-revenue is banned."""
    for ok in (
        "Median absolute error is 26% against quarantined truth.",
        "35% of promotions did not pay back.",
        "Its giveaway share is 62.5% of promoted volume.",
        "Execution compliance runs 65-85% of authorized stores.",
        "The portfolio clears 1.47x on the dollar.",
        # The CSS false positive an earlier draft of this scan produced.
        "figure { width: 100%; } .sales-note { color: red; }",
    ):
        assert not _hits(ok), f"false positive on: {ok!r}"
