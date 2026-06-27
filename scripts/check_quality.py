#!/usr/bin/env python3
"""Guard for the independent Quality Auditor's scorecard (maker != checker).

We CONSUME the grade; we NEVER author docs/quality/QUALITY_SCORECARD.md or
QUALITY_RUBRIC.md (the auditor owns + bootstraps them). This guard only validates the
scorecard so a malformed one can't ship, and (in readiness mode) enforces A/A+ on every
ship-critical dimension and >= B elsewhere.

Consumption contract the auditor populates (a fenced ```yaml block keyed
QUALITY_SCORECARD inside docs/quality/QUALITY_SCORECARD.md):

    QUALITY_SCORECARD:
      as_of: 2026-06-27
      overall: null            # one of A+ A B C D F, or null when ungraded
      dimensions:
        - name: functional-reality
          grade: null          # one of A+ A B C D F, or null
          ship_critical: true
          top_gaps: ["..."]

Usage:
  check_quality.py parse      # CI: OK if file absent; FAIL if present but malformed
  check_quality.py readiness  # full gate: require present + A/A+ ship-critical, >= B else
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCORECARD = ROOT / "docs" / "quality" / "QUALITY_SCORECARD.md"
VALID = {"A+", "A", "B", "C", "D", "F"}
PASS_SHIP_CRITICAL = {"A+", "A"}
PASS_OTHER = {"A+", "A", "B"}


def load_block() -> dict:
    text = SCORECARD.read_text()
    for raw in re.findall(r"```yaml\n(.*?)```", text, re.DOTALL):
        if re.match(r"^QUALITY_SCORECARD\s*:", raw.strip()):
            try:
                data = yaml.safe_load(raw)
            except yaml.YAMLError as e:
                sys.exit(f"FAIL: QUALITY_SCORECARD is not valid YAML: {e}")
            return data["QUALITY_SCORECARD"]
    sys.exit("FAIL: no `QUALITY_SCORECARD:` yaml block in docs/quality/QUALITY_SCORECARD.md")


def grade_of(value) -> "str | None":
    return None if value is None else str(value).strip()


def validate(sc: dict) -> list:
    if not isinstance(sc, dict):
        sys.exit("FAIL: QUALITY_SCORECARD must be a mapping")
    grades = [grade_of(sc.get("overall"))]
    dims = sc.get("dimensions") or []
    if not isinstance(dims, list):
        sys.exit("FAIL: QUALITY_SCORECARD.dimensions must be a list")
    for d in dims:
        if not isinstance(d, dict) or d.get("name") is None:
            sys.exit("FAIL: each dimension needs a 'name'")
        grades.append(grade_of(d.get("grade")))
    for g in grades:
        if g is not None and g not in VALID:
            sys.exit(f"FAIL: invalid grade {g!r} (allowed: A+, A, B, C, D, F, null)")
    return dims


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "parse"
    if not SCORECARD.exists():
        if mode == "readiness":
            sys.exit("FAIL: docs/quality/QUALITY_SCORECARD.md missing — the auditor must grade before ship")
        print("OK: quality scorecard not present yet (auditor bootstraps it) — parse guard skipped")
        return

    sc = load_block()
    dims = validate(sc)

    if mode != "readiness":
        print("OK: QUALITY_SCORECARD parses; all grades valid")
        return

    if not dims:
        sys.exit("FAIL: QUALITY_SCORECARD has no dimensions to grade")
    for d in dims:
        name = d.get("name")
        g = grade_of(d.get("grade"))
        is_critical = bool(d.get("ship_critical"))
        if g is None:
            sys.exit(f"FAIL: dimension {name!r} is ungraded (null) — not ship-ready")
        if is_critical and g not in PASS_SHIP_CRITICAL:
            sys.exit(f"FAIL: ship-critical dimension {name!r} is {g} (needs A or A+)")
        if not is_critical and g not in PASS_OTHER:
            sys.exit(f"FAIL: dimension {name!r} is {g} (needs >= B)")
    print("OK: ship-critical dimensions A/A+, all others >= B")


if __name__ == "__main__":
    main()
