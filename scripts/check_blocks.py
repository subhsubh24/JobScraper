#!/usr/bin/env python3
"""Validate the three dashboard-readable YAML blocks + their invariants.

Exits non-zero on the first problem so preflight can fail fast.
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def extract_block(path: Path, key: str) -> dict:
    """Pull the first ```yaml fenced block that defines `key:` and parse it."""
    if not path.exists():
        sys.exit(f"FAIL: missing file {path}")
    text = path.read_text()
    blocks = re.findall(r"```yaml\n(.*?)```", text, re.DOTALL)
    for raw in blocks:
        if re.match(rf"^{re.escape(key)}\s*:", raw.strip()):
            try:
                data = yaml.safe_load(raw)
            except yaml.YAMLError as e:
                sys.exit(f"FAIL: {key} in {path.name} is not valid YAML: {e}")
            return data[key]
    sys.exit(f"FAIL: no `{key}:` yaml block found in {path}")


def main() -> None:
    # BUSINESS_CASE_SUMMARY
    bc = extract_block(ROOT / "docs" / "BUSINESS_CASE.md", "BUSINESS_CASE_SUMMARY")
    for field in ("currency", "arr_year1", "planning_case", "floor_usd",
                  "floor_met_year1", "time_to_floor", "as_of"):
        if field not in bc:
            sys.exit(f"FAIL: BUSINESS_CASE_SUMMARY missing `{field}`")
    if not isinstance(bc["floor_met_year1"], bool):
        sys.exit("FAIL: floor_met_year1 must be a boolean")
    for s in ("conservative", "base", "optimistic"):
        if s not in bc["arr_year1"]:
            sys.exit(f"FAIL: arr_year1 missing `{s}`")

    # GROWTH_STATUS
    gs = extract_block(ROOT / "docs" / "growth" / "GROWTH_STATUS.md", "GROWTH_STATUS")
    for field in ("project", "as_of", "phase", "engine_built", "engine_pct",
                  "channels_connected", "awaiting_connect", "site_gate_up", "funnel",
                  "acquisition", "channels", "experiments", "email", "content",
                  "learnings", "next_actions", "owner_blockers", "links"):
        if field not in gs:
            sys.exit(f"FAIL: GROWTH_STATUS missing `{field}`")
    if gs["phase"] not in ("pre_launch", "launching", "post_launch"):
        sys.exit(f"FAIL: GROWTH_STATUS.phase invalid: {gs['phase']}")
    if not isinstance(gs["site_gate_up"], bool):
        sys.exit("FAIL: GROWTH_STATUS.site_gate_up must be a boolean")
    # Pinned invariant: engine_built iff engine_pct == 100
    if bool(gs["engine_built"]) != (gs["engine_pct"] == 100):
        sys.exit("FAIL: engine_built must equal (engine_pct == 100)")

    # OWNER_ACTIONS
    oa = extract_block(ROOT / "PENDING_OPS.md", "OWNER_ACTIONS")
    for field in ("project", "as_of", "items"):
        if field not in oa:
            sys.exit(f"FAIL: OWNER_ACTIONS missing `{field}`")
    for it in oa["items"]:
        for f in ("id", "title", "priority", "status", "why", "how"):
            if f not in it:
                sys.exit(f"FAIL: OWNER_ACTIONS item missing `{f}`: {it.get('id', '?')}")
        if it["priority"] not in ("urgent", "high", "normal"):
            sys.exit(f"FAIL: bad priority {it['priority']} in {it['id']}")
        if it["status"] not in ("open", "in_progress", "done"):
            sys.exit(f"FAIL: bad status {it['status']} in {it['id']}")

    print("OK: all three YAML blocks parse and satisfy invariants")
    # Emit a couple of values preflight uses for readiness gating
    print(f"floor_met_year1={str(bc['floor_met_year1']).lower()}")
    print(f"engine_pct={gs['engine_pct']}")


if __name__ == "__main__":
    main()
