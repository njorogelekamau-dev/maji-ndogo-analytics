"""Publishing rules for the Classification DSS module, enforced on every push."""
import re
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]   # tests/ -> 5_classification_dss/
README = MODULE / "README.md"
FIGURES = MODULE / "figures"

REQUIRED_SECTIONS = [
    "## 1. Purpose & scope",
    "## 2. How the system decides",
    "## 3. Trust tiers",
    "## 4. Pollution audit protocol",
    "## 5. Known failure modes",
    "## 6. Verification",
]


def readme_text():
    return README.read_text(encoding="utf-8")


def cited_figures():
    """Every figures/... path used as a Markdown image: ![alt](figures/name.png)."""
    return set(re.findall(r"!\[[^\]]*\]\((figures/[^)\s]+)\)", readme_text()))


def test_no_forbidden_files_published():
    """The manual ships alone: no data, notebooks, or model binaries."""
    forbidden = ["*.db", "*.csv", "*.ipynb", "*.pkl"]
    offenders = [p for pattern in forbidden for p in MODULE.rglob(pattern)]
    assert offenders == [], f"Forbidden files in module: {offenders}"


def test_every_cited_figure_exists():
    """No broken images: each figure the manual cites is really in figures/."""
    missing = sorted(c for c in cited_figures() if not (MODULE / c).is_file())
    assert missing == [], f"README cites figures that do not exist: {missing}"


def test_every_figure_is_cited():
    """No orphan evidence: each file in figures/ backs at least one claim."""
    on_disk = {f"figures/{p.name}" for p in FIGURES.iterdir()
               if p.is_file() and p.name != ".gitkeep"}
    uncited = sorted(on_disk - cited_figures())
    assert uncited == [], f"Figures never cited in README: {uncited}"


def test_required_sections_present_in_order():
    """The six fixed sections of the operations manual exist, in order."""
    text = readme_text()
    positions = [text.find(heading) for heading in REQUIRED_SECTIONS]
    missing = [h for h, pos in zip(REQUIRED_SECTIONS, positions) if pos == -1]
    assert missing == [], f"Missing sections: {missing}"
    assert positions == sorted(positions), "Sections are out of order"


def test_badge_is_first_line():
    """The live build badge opens the manual."""
    first_line = readme_text().splitlines()[0]
    assert first_line.startswith("![portfolio-checks]("), f"First line is not the badge: {first_line!r}"
    assert "actions/workflows/portfolio-checks.yml/badge.svg" in first_line
