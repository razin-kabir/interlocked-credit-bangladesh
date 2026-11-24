#!/usr/bin/env python3
"""Verify the input files against data/checksums.sha256.

Paths in the checksum file are relative to MATS_DATA_DIR (``mats_2018/...``)
or to the folder that holds BD_DISTRICT_SHP (``shapefiles/...``).
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
from common import DISTRICT_SHP, MATS_DIR, REPO_ROOT  # noqa: E402

ROOTS = {"mats_2018": MATS_DIR, "shapefiles": DISTRICT_SHP.parent}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ok = True
    for line in (REPO_ROOT / "data" / "checksums.sha256").read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        expected, rel = line.split(maxsplit=1)
        top, _, rest = rel.partition("/")
        path = ROOTS[top] / rest
        if not path.exists():
            print(f"MISSING   {rel}")
            ok = False
        elif sha256(path) != expected:
            print(f"MISMATCH  {rel}")
            ok = False
        else:
            print(f"ok        {rel}")
    print("All input files verified." if ok else "Some input files are missing or differ.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
