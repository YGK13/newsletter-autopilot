"""
Loads config/brand.json -- the one file with mechanical settings (publication ID,
footer HTML, cadence, image palette). Voice, structure and editorial rules live in
PLAYBOOK.md and LEARNINGS.md at the repo root, not here -- see PROTOCOL.md section 3
for why the split is made this way.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BRAND_PATH = REPO_ROOT / "config" / "brand.json"
EXAMPLE_PATH = REPO_ROOT / "config" / "brand.example.json"


def load_brand() -> dict[str, Any]:
    if not BRAND_PATH.exists():
        sys.exit(
            f"Missing {BRAND_PATH}.\n"
            f"Copy config/brand.example.json to config/brand.json and fill in your own "
            f"values first -- see PROTOCOL.md section 5, step 3."
        )
    return json.loads(BRAND_PATH.read_text(encoding="utf-8"))


def load_playbook() -> str:
    path = REPO_ROOT / "PLAYBOOK.md"
    if not path.exists():
        sys.exit("Missing PLAYBOOK.md -- see PROTOCOL.md section 5, step 4.")
    return path.read_text(encoding="utf-8")


def load_learnings() -> str:
    path = REPO_ROOT / "LEARNINGS.md"
    if not path.exists():
        sys.exit("Missing LEARNINGS.md -- copy LEARNINGS.seed.md to LEARNINGS.md to start.")
    return path.read_text(encoding="utf-8")
