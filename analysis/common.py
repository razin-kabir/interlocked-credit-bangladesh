"""Shared paths, sample restrictions and LaTeX helpers for the analysis.

Input data are never stored in this repository. By default they are read from
``data/`` (git-ignored); set the environment variables below to read them from
somewhere else instead. See ``data/README.md`` for the files that are needed.

    MATS_DATA_DIR    folder that contains ``trader_data/clean/*.dta``
    BD_DISTRICT_SHP  path to the 2022 district boundary shapefile (Figure 4 only)
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# ── Inputs (git-ignored) ─────────────────────────────────────────────────────
MATS_DIR = Path(os.environ.get("MATS_DATA_DIR", REPO_ROOT / "data" / "mats_2018"))
TRADER_DIR = MATS_DIR / "trader_data" / "clean"
DISTRICT_SHP = Path(
    os.environ.get("BD_DISTRICT_SHP", REPO_ROOT / "data" / "shapefiles" / "district2022.shp")
)

# ── Outputs (committed, \input{}-ed by paper/main.tex) ───────────────────────
TABLES = REPO_ROOT / "paper" / "tables"
FIGURES = REPO_ROOT / "paper" / "figures"

# ── Sample restrictions ──────────────────────────────────────────────────────
PRICE_MIN, PRICE_MAX = 5, 50  # BDT/kg; monthly paddy prices outside are dropped
SURVEY_YEAR = 2018

# ── Confidentiality ──────────────────────────────────────────────────────────
# Published statistics for a geographic unit (district or upazila) must pool at
# least this many distinct traders, so no row or map cell describes one or two
# identifiable businesses.
MIN_TRADERS = 3


def trader_file(name: str) -> Path:
    """Path to a cleaned MATS 2018 trader module, with a helpful error if missing."""
    path = TRADER_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. The MATS 2018 microdata are not distributed with "
            "this repository; see data/README.md for how to obtain them and point "
            "MATS_DATA_DIR at the folder that contains trader_data/clean/."
        )
    return path


def pct_of_answered(s, value) -> float:
    """Percent of non-missing responses equal to ``value`` (missing answers excluded)."""
    s = s.dropna()
    return float((s == value).mean() * 100)


# ── LaTeX table helpers ──────────────────────────────────────────────────────
def stars(p: float) -> str:
    if p < 0.01:
        return r"$^{***}$"
    if p < 0.05:
        return r"$^{**}$"
    if p < 0.10:
        return r"$^{*}$"
    return ""


def fmt_c(v: float, p: float, digits: int = 4) -> str:
    """Coefficient with significance stars."""
    return f"{v:.{digits}f}{stars(p)}"


def fmt_se(v: float, digits: int = 4) -> str:
    return f"({v:.{digits}f})"


def write_tex(path: Path, lines: list[str]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Wrote {path.relative_to(REPO_ROOT)}")
