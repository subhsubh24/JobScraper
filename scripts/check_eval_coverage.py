#!/usr/bin/env python3
"""Eval-coverage ratchet — every AI-output module has a deterministic + a real-output eval.

The analog of check_validation.py for OUTPUT QUALITY. Fails CLOSED so a new LLM-using feature
can't ship un-evaluated:
  1. Scan src/ for modules that use the LLM client (get_llm_client / chat.completions.create /
     embeddings.create) — the AI-output surface. Every one MUST be declared in
     docs/ci/EVAL_COVERAGE.md under some feature's `modules`.
  2. Every named eval file (deterministic_evals + real_output_eval) MUST exist.
  3. Every feature MUST name a real_output_eval (the "real on all AI features" ratchet).

--report prints the dashboard counts. Reads only committed files; never runs the evals.
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "docs" / "ci" / "EVAL_COVERAGE.md"
LLM_USE = re.compile(r"get_llm_client|\.chat\.completions\.create|\.embeddings\.create")


def _block(path: Path, key: str):
    if not path.exists():
        sys.exit(f"FAIL: missing {path}")
    for raw in re.findall(r"```yaml\n(.*?)```", path.read_text(), re.DOTALL):
        if re.match(rf"^{re.escape(key)}\s*:", raw.strip()):
            return yaml.safe_load(raw)[key]
    sys.exit(f"FAIL: no `{key}:` yaml block in {path}")


def _llm_modules() -> set:
    found = set()
    for f in (ROOT / "src").rglob("*.py"):
        if f.name == "llm.py":  # the client factory itself, not a feature
            continue
        if LLM_USE.search(f.read_text()):
            found.add(str(f.relative_to(ROOT)))
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    features = _block(MANIFEST, "EVAL_COVERAGE")
    declared_modules = set()
    for feat in features:
        declared_modules.update(feat.get("modules", []) or [])

    if args.report:
        print("EVAL_COVERAGE_REPORT")
        print(f"ai_features_total={len(features)}")
        print(f"with_real_output_eval={sum(1 for f in features if f.get('real_output_eval'))}")
        print(f"llm_modules={sorted(_llm_modules())}")
        return

    problems = []

    # 1. every LLM-using module is declared
    undeclared = sorted(_llm_modules() - declared_modules)
    if undeclared:
        problems.append(
            f"AI-output module(s) with no eval declared in docs/ci/EVAL_COVERAGE.md: {undeclared} — "
            "add each to a feature's `modules` with a deterministic eval + a real_output_eval."
        )

    # 2 + 3. named eval files exist; every feature has a real_output_eval that exists
    for feat in features:
        fid = feat.get("feature", "?")
        for ev in feat.get("deterministic_evals", []) or []:
            if not (ROOT / ev).exists():
                problems.append(f"{fid}: deterministic eval '{ev}' does not exist")
        rov = feat.get("real_output_eval")
        if not rov:
            problems.append(f"{fid}: no real_output_eval named (required for every AI-output feature)")
        elif not (ROOT / rov).exists():
            problems.append(f"{fid}: real_output_eval '{rov}' does not exist")

    if problems:
        sys.exit("FAIL: eval-coverage gate:\n  - " + "\n  - ".join(problems))

    print(f"OK: eval coverage — {len(features)} AI-output features, all with deterministic + real-output evals")
    for feat in features:
        print(f"  {feat['feature']:12} modules={feat.get('modules')} real_output_eval={feat.get('real_output_eval')}")


if __name__ == "__main__":
    main()
