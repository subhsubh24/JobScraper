#!/usr/bin/env python3
"""Self-validation gate (FACTORY self-validation manifest) — convergence build.

Modes:
  (default, per-PR)   declaration + surfacing + honesty guards (always), and a SCOPED block:
                      a `blocking: true` capability that isn't validated fails ONLY if THIS PR
                      touches it (so an unmet capability never halts unrelated work).
  --readiness         the ship gate: ALL of the above PLUS any UNMET capability fails,
                      regardless of touch (you cannot ship an unvalidated capability).
  --report            print the dashboard block (capabilities_total, unmet ids) and exit 0.

Guards:
  1. DECLARATION (always, global): every secret-like env var read in RUNTIME app code
     (src/ + asgi.py — NOT tests/scripts/CI, so CI-only vars don't cause false drift) MUST be
     declared in docs/ci/VALIDATION.md. A NEW service can't ship undeclared.
  2. SURFACING (always): a GAP (validation: degraded_only) MUST name an owner_action that
     EXISTS in PENDING_OPS — so it reaches the owner/dashboard, not just CI logs.
  3. HONESTY (always): a capability claimed `real`/`mock` MUST name a `covered_by` test that
     exists — a "validated" capability that's really an un-exercised stub is the email-verify
     trap; the readiness auditors additionally reconcile that the test genuinely exercises it.
  4. BLOCKING: an unmet `blocking: true` capability fails (scoped per-PR / global at readiness).
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml  # declared dependency (requirements-dev.txt: pyyaml) — never rely on it transitively

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "docs" / "ci" / "VALIDATION.md"
PENDING = ROOT / "PENDING_OPS.md"
SCAN_DIRS = ["src"]          # RUNTIME app code only (pitfall B1)
SCAN_FILES = ["asgi.py"]

SECRET_RE = re.compile(r"(_KEY$|_KEY\b|_SECRET|_TOKEN|_PASSWORD|_WEBHOOK|_DSN|_CREDENTIAL|^DATABASE_URL$)")
ENV_RE = re.compile(r"""os\.(?:getenv|environ\.get)\(\s*["']([A-Z][A-Z0-9_]*)["']"""
                    r"""|os\.environ\[\s*["']([A-Z][A-Z0-9_]*)["']\s*\]""")


def _load_block(path: Path, key: str):
    text = path.read_text()
    for raw in re.findall(r"```yaml\n(.*?)```", text, re.DOTALL):
        if re.match(rf"^{re.escape(key)}\s*:", raw.strip()):
            return yaml.safe_load(raw)[key]
    sys.exit(f"FAIL: no `{key}:` yaml block in {path}")


def _runtime_files() -> list:
    files = []
    for d in SCAN_DIRS:
        files += list((ROOT / d).rglob("*.py"))
    files += [ROOT / f for f in SCAN_FILES]
    return [f for f in files if f.exists()]


def _env_to_files() -> dict:
    """Map each secret-like env var -> the runtime files that read it."""
    mapping: dict = {}
    for f in _runtime_files():
        rel = str(f.relative_to(ROOT))
        for m in ENV_RE.finditer(f.read_text()):
            name = m.group(1) or m.group(2)
            if name and SECRET_RE.search(name):
                mapping.setdefault(name, set()).add(rel)
    return mapping


def _changed_files():
    """Files changed vs the PR base, or None if it can't be computed (then: conservative)."""
    base_ref = os.getenv("GITHUB_BASE_REF") or "main"
    for base in (f"origin/{base_ref}", base_ref):
        try:
            out = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"],
                                 capture_output=True, text=True, cwd=ROOT, timeout=30)
            if out.returncode == 0:
                return set(filter(None, out.stdout.splitlines()))
        except Exception:
            pass
    return None


def _touched(cap, changed, env_files) -> bool:
    if changed is None:
        return True  # base diff unavailable -> block conservatively
    if "docs/ci/VALIDATION.md" in changed:
        return True
    for e in cap.get("env", []) or []:
        if env_files.get(e, set()) & changed:
            return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--readiness", action="store_true", help="ship gate: any unmet capability fails")
    ap.add_argument("--report", action="store_true", help="print the dashboard block and exit 0")
    args = ap.parse_args()

    caps = _load_block(MANIFEST, "VALIDATION_CAPABILITIES")
    declared = set()
    for c in caps:
        declared.update(c.get("env", []) or [])
    env_files = _env_to_files()
    unmet = [c["id"] for c in caps if c.get("validation") == "degraded_only"]

    if args.report:
        print("VALIDATION_REPORT")
        print(f"capabilities_total={len(caps)}")
        print(f"unmet={unmet}")
        return

    problems = []

    # 1. DECLARATION (global)
    undeclared = sorted(set(env_files) - declared)
    if undeclared:
        problems.append(
            f"undeclared external dependency in runtime code: {undeclared} — declare it in "
            "docs/ci/VALIDATION.md (env, validation, blocking), degrade gracefully, file an OWNER_ACTION"
        )

    oa_ids = {it["id"] for it in _load_block(PENDING, "OWNER_ACTIONS").get("items", [])}
    changed = _changed_files()

    for c in caps:
        cid, val = c["id"], c.get("validation")
        gap = val == "degraded_only"
        # 2. SURFACING
        if gap:
            owner = c.get("owner_action")
            if not owner:
                problems.append(f"{cid}: degraded_only but no owner_action named (won't reach the owner)")
            elif owner not in oa_ids:
                problems.append(f"{cid}: owner_action '{owner}' not in PENDING_OPS OWNER_ACTIONS")
        # 3. HONESTY
        if val in ("real", "mock"):
            cov = c.get("covered_by")
            if not cov:
                problems.append(f"{cid}: validation={val} but no covered_by test named (honesty)")
            elif not (ROOT / cov).exists():
                problems.append(f"{cid}: covered_by '{cov}' does not exist")
        # 4. BLOCKING
        if c.get("blocking") and (gap or not c.get("key_in_ci")):
            if args.readiness or _touched(c, changed, env_files):
                scope = "readiness" if args.readiness else "this PR touches it"
                problems.append(f"{cid}: blocking=true and not validated ({scope}) — add the key in CI "
                                "or set blocking=false consciously")

    # 5. READINESS: any unmet capability fails the ship gate.
    if args.readiness and unmet:
        problems.append(f"readiness: unvalidated capabilities present {unmet} — provide their keys "
                        "in CI (see the OWNER_ACTIONs) before shipping, or downgrade the claim honestly")

    if problems:
        sys.exit("FAIL: self-validation gate:\n  - " + "\n  - ".join(problems))

    mode = "readiness" if args.readiness else "per-PR"
    print(f"OK: self-validation manifest consistent ({mode}); {len(caps)} capabilities, unmet={unmet}")
    for c in caps:
        flag = " [BLOCKING]" if c.get("blocking") else ""
        note = "  <-- GAP (surfaced as OWNER_ACTION)" if c.get("validation") == "degraded_only" else ""
        print(f"  {c['id']:14} validation={str(c.get('validation')):13} key_in_ci={c.get('key_in_ci')}{flag}{note}")


if __name__ == "__main__":
    main()
