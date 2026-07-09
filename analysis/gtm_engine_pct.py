"""Growth-engine build percentage (docs/growth/GROWTH_STATUS.md `engine_pct`).

Committed, deterministic computation (FACTORY_STANDARD S22) -- no live network/secrets.
Parses ROADMAP.md Track G (Marketing engine + brand) and Track H (Growth-execution
engine), counts every `- [ ]` / `- [x]` checkbox line (top-level and indented sub-items)
in those two tracks, and reports the percentage checked. This is the SAME definition
`scripts/check_blocks.py` enforces at the readiness gate (`engine_built` iff
`engine_pct == 100`) -- so it stays honest as ROADMAP items in G/H tick or un-tick.
Re-run whenever Track G or H changes; re-cite the value in GROWTH_STATUS.md (never
hand-edit engine_pct independently).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROADMAP = ROOT / "ROADMAP.md"

TRACK_HEADERS = ("### G ", "### H ")
NEXT_HEADER = re.compile(r"^##\s")
CHECKBOX = re.compile(r"^\s*-\s\[([ xX])\]")


def engine_pct():
    lines = ROADMAP.read_text().splitlines()
    in_track = False
    total = 0
    checked = 0
    for line in lines:
        if line.startswith(TRACK_HEADERS):
            in_track = True
            continue
        if in_track and NEXT_HEADER.match(line) and not line.startswith(TRACK_HEADERS):
            in_track = False
            continue
        if in_track:
            m = CHECKBOX.match(line)
            if m:
                total += 1
                if m.group(1) in ("x", "X"):
                    checked += 1
    if total == 0:
        return 0
    return round(100 * checked / total)


if __name__ == "__main__":
    print(engine_pct())
