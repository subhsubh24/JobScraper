#!/usr/bin/env python3
"""validate-gtm — deterministic GTM honesty gate (the GTM analog of check_validation.py).

Fails CLOSED so the factory cannot report a GTM number it cannot source. The independent
Growth/GTM auditor judges the SOFT stuff (is the analysis sound?); this enforces the HARD,
machine-checkable honesty rules — a Python port of AptDesignerAI's scripts/validate-gtm.mjs:

  1. GROWTH_STATUS fenced YAML parses.
  2. METRIC-WITHOUT-A-SOURCE tripwire: if any funnel/acquisition/pmf/channels metric is
     non-zero, a connected source MUST be declared (channels_connected truthy, OR a
     sources/validation block with a connected/available entry). A real number with no
     connected source = fabrication risk -> FAIL. (Pre-launch: all 0/null -> passes.)
  3. GTM_SCORECARD (if present) parses, grades in {A+,A,B,C,D,F,null}, ship_gate_met set.
  4. --readiness: additionally require GTM_SCORECARD to exist with no ship_critical dim < A.

Reads only committed GTM feeds; never prints a secret.
"""
import argparse
import re
import sys
from pathlib import Path

import yaml  # declared dependency (requirements-dev.txt: pyyaml)

ROOT = Path(__file__).resolve().parent.parent
STATUS = ROOT / "docs" / "growth" / "GROWTH_STATUS.md"
SCORECARD = ROOT / "docs" / "growth" / "GTM_SCORECARD.md"
GRADES = {"A+", "A", "B", "C", "D", "F", None}
METRIC_SECTIONS = ["funnel", "acquisition", "pmf", "channels"]


def _block(path: Path, key):
    if not path.exists():
        return None
    for raw in re.findall(r"```yaml\n(.*?)```", path.read_text(), re.DOTALL):
        try:
            d = yaml.safe_load(raw)
        except yaml.YAMLError:
            continue
        if isinstance(d, dict):
            if key is None:
                return d
            if key in d:
                return d[key]
    return None


def _walk_nonzero(v, p, out):
    if v is None or isinstance(v, bool):      # bools are flags, not metrics
        return
    if isinstance(v, (int, float)):
        if v > 0:
            out.append(f"{p}={v}")
        return
    if isinstance(v, list):
        for i, x in enumerate(v):
            _walk_nonzero(x, f"{p}[{i}]", out)
    elif isinstance(v, dict):
        for k, val in v.items():
            _walk_nonzero(val, f"{p}.{k}", out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--readiness", action="store_true", help="also require a graded GTM_SCORECARD")
    args = ap.parse_args()
    errors = []

    # --- 1 + 2. GROWTH_STATUS parses + metric-without-a-source tripwire ---
    if not STATUS.exists():
        errors.append("docs/growth/GROWTH_STATUS.md is missing (the dashboard feed).")
    else:
        gs = _block(STATUS, "GROWTH_STATUS")
        if gs is None:
            errors.append("GROWTH_STATUS.md has no parseable fenced `GROWTH_STATUS:` YAML block.")
        else:
            reported = []
            for s in METRIC_SECTIONS:
                if s in gs:
                    _walk_nonzero(gs[s], s, reported)
            cc = gs.get("channels_connected")
            channels_connected = (
                cc is True
                or (isinstance(cc, list) and len(cc) > 0)
                or (isinstance(cc, str) and cc.strip() != "" and cc.strip().lower() not in ("none", "n/a", "[]"))
            )
            src = gs.get("sources") or gs.get("validation")
            source_declared = False
            if src:
                txt = str(src).lower()
                source_declared = ("connected" in txt or "available" in txt) and "unavailable" not in txt
            if reported and not channels_connected and not source_declared:
                shown = ", ".join(reported[:8]) + (" ..." if len(reported) > 8 else "")
                errors.append(
                    f"METRIC WITHOUT A SOURCE: {len(reported)} non-zero GROWTH_STATUS metric(s) reported but "
                    "no connected source declared (channels_connected falsy, no sources/validation entry "
                    "connected/available). A real number with no source is a fabrication risk.\n"
                    f"    reported: {shown}\n"
                    "    -> set to 0/null until a source is connected, OR declare the connected source "
                    "(channels_connected / a sources block) + a gtm-connect-* OWNER_ACTION."
                )

    # --- 3 + 4. GTM_SCORECARD validity (if present) ---
    sc_exists = SCORECARD.exists()
    if sc_exists:
        sc = _block(SCORECARD, "GTM_SCORECARD")
        if sc is None:
            sc = _block(SCORECARD, None)
        if sc is None:
            errors.append("GTM_SCORECARD.md exists but has no parseable fenced YAML block.")
        else:
            dims = sc.get("dimensions") or sc.get("grades") or sc
            bad = []
            if isinstance(dims, dict):
                for k, v in dims.items():
                    if isinstance(v, str) and len(v) <= 2 and v not in GRADES:
                        bad.append(f"{k}={v}")
                    elif isinstance(v, dict) and "grade" in v and v["grade"] not in GRADES:
                        bad.append(f"{k}.grade={v['grade']}")
            if bad:
                errors.append(f"GTM_SCORECARD invalid grade(s) (allowed A+/A/B/C/D/F/null): {', '.join(bad)}")
            has_ship_gate = ("ship_gate_met" in sc) or (isinstance(dims, dict) and "ship_gate_met" in dims)
            if not has_ship_gate:
                errors.append("GTM_SCORECARD is missing `ship_gate_met`.")
            if args.readiness and isinstance(dims, dict):
                for k, v in dims.items():
                    if isinstance(v, dict) and v.get("ship_critical") and v.get("grade") not in ("A+", "A"):
                        errors.append(f"--readiness: ship_critical GTM dim '{k}' grade={v.get('grade')} (< A)")
    elif args.readiness:
        errors.append("--readiness: docs/growth/GTM_SCORECARD.md does not exist yet (GTM not graded) — "
                      "cannot assert GTM readiness.")

    if errors:
        sys.stderr.write(f"\nvalidate-gtm: FAIL ({len(errors)})\n")
        for e in errors:
            sys.stderr.write(f" - {e}\n")
        sys.exit(1)
    tail = " (GTM_SCORECARD present)" if sc_exists else " (no GTM_SCORECARD yet)"
    print(f"validate-gtm: OK{tail}{' [readiness]' if args.readiness else ''}")


if __name__ == "__main__":
    main()
