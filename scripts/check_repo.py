#!/usr/bin/env python3
"""Pre-publication privacy checks. Standard library only; exits 1 on any failure.

Checks every file git would publish (tracked files plus untracked, non-ignored
files) for:
  * survey microdata / GIS files (by extension)
  * Jupyter notebooks that contain outputs or execution counts
  * references to directly identifying MATS variables (names, addresses, GPS,
    interviewer, questionnaire number, gender)
  * local absolute paths, e-mail addresses not on the allow-list,
    Bangladeshi phone numbers and high-precision GPS coordinates
  * files larger than 10 MB
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_EXT = {
    ".dta", ".rdata", ".rds", ".sav", ".csv", ".tsv", ".xls", ".xlsx", ".parquet",
    ".feather", ".pkl", ".shp", ".shx", ".dbf", ".prj", ".cpg", ".sbn", ".sbx",
    ".gpkg", ".geojson", ".kml", ".zip", ".7z", ".gz",
}
TEXT_EXT = {".py", ".ipynb", ".tex", ".bib", ".md", ".toml", ".cff", ".yml", ".yaml",
            ".txt", ".cfg", ".sha256", ""}
# Survey variables that directly identify respondents or enumerators.
# a01 trader name, a06 union/ward, a07 village/street, a08 interviewer,
# a10_* GPS, q_no questionnaire no., b00* miller name/address, b02 gender.
IDENTIFYING_VARS = re.compile(
    r"""["'](a01|a06|a07|a08|a10_\w+|q_no|b00\w*|b02)["']"""
)
ALLOWED_EMAILS = {"r.kabir@cgiar.org"}
PATTERNS = {
    "local absolute path": re.compile(r"(/Users/|/home/[a-z]|[A-Za-z]:\\\\?Users|Dropbox)"),
    "phone number": re.compile(r"(?<!\d)(?:\+?880[- ]?|0)1[3-9]\d{2}[- ]?\d{6}(?!\d)"),
    "GPS coordinate": re.compile(r"(?<![\d.])(2[0-6]\.\d{5,}|(8[89]|9[0-2])\.\d{5,})"),
    "e-mail address": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
}
MAX_BYTES = 10 * 1024 * 1024


def publishable_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout.decode()
    return [ROOT / p for p in out.split("\0") if p and (ROOT / p).is_file()]


def main() -> int:
    problems: list[str] = []
    files = publishable_files()
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        if rel == "scripts/check_repo.py":
            continue  # contains the patterns themselves
        ext = path.suffix.lower()
        if ext in DATA_EXT:
            problems.append(f"{rel}: data/GIS file must not be published")
            continue
        if path.stat().st_size > MAX_BYTES:
            problems.append(f"{rel}: larger than 10 MB")
        if ext == ".pdf":
            raw = path.read_bytes()
            for needle in (b"/Users/", b"Dropbox"):
                if needle in raw:
                    problems.append(f"{rel}: PDF contains '{needle.decode()}'")
            continue
        if ext not in TEXT_EXT and path.name not in {"Makefile", "LICENSE", ".gitignore"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if ext == ".ipynb":
            nb = json.loads(text)
            for i, cell in enumerate(nb.get("cells", [])):
                if cell.get("cell_type") == "code" and (cell.get("outputs") or cell.get("execution_count")):
                    problems.append(f"{rel}: cell {i} has outputs (clear all outputs before committing)")
        for m in IDENTIFYING_VARS.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            problems.append(f"{rel}:{line}: references identifying survey variable {m.group(1)}")
        for name, pat in PATTERNS.items():
            for m in pat.finditer(text):
                if name == "e-mail address" and m.group(0).lower() in ALLOWED_EMAILS:
                    continue
                if name == "e-mail address" and m.group(0).lower().endswith("users.noreply.github.com"):
                    continue
                line = text.count("\n", 0, m.start()) + 1
                problems.append(f"{rel}:{line}: {name}: {m.group(0)!r}")

    if problems:
        print("Privacy check FAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"Privacy check passed ({len(files)} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
