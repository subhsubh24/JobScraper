#!/usr/bin/env python3
"""Self-validation gate (FACTORY self-validation manifest).

Enforces that the loop can actually validate every external capability it ships:
  1. DECLARATION: every secret-like env var read in the backend code MUST be declared in
     docs/ci/VALIDATION.md — so a NEW external service can't ship undeclared/unvalidated.
  2. BLOCKING: any capability marked `blocking: true` that isn't truly validated
     (degraded_only, or its required key is absent right now) FAILS the gate.
  3. SURFACING: any capability that is a GAP (validation: degraded_only) MUST name an
     `owner_action` that actually exists in PENDING_OPS, so the gap shows on the dashboard.

Exit non-zero on the first problem so preflight fails fast.
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "docs" / "ci" / "VALIDATION.md"
PENDING = ROOT / "PENDING_OPS.md"
SCAN_DIRS = ["src"]
SCAN_FILES = ["asgi.py"]

# A name is a "secret/credential" (vs plain config) if it matches any of these.
SECRET_RE = re.compile(r"(_KEY$|_KEY\b|_SECRET|_TOKEN|_PASSWORD|_WEBHOOK|_DSN|_CREDENTIAL|^DATABASE_URL$)")
# os.getenv("X") / os.environ.get("X") / os.environ["X"]
ENV_RE = re.compile(r"""os\.(?:getenv|environ\.get)\(\s*["']([A-Z][A-Z0-9_]*)["']"""
                    r"""|os\.environ\[\s*["']([A-Z][A-Z0-9_]*)["']\s*\]""")


def _load_block(path: Path, key: str):
    text = path.read_text()
    for raw in re.findall(r"```yaml\n(.*?)```", text, re.DOTALL):
        if re.match(rf"^{re.escape(key)}\s*:", raw.strip()):
            return yaml.safe_load(raw)[key]
    sys.exit(f"FAIL: no `{key}:` yaml block in {path}")


def _scanned_secret_envs() -> set:
    found = set()
    targets = []
    for d in SCAN_DIRS:
        targets += list((ROOT / d).rglob("*.py"))
    targets += [ROOT / f for f in SCAN_FILES]
    for f in targets:
        if not f.exists():
            continue
        for m in ENV_RE.finditer(f.read_text()):
            name = m.group(1) or m.group(2)
            if name and SECRET_RE.search(name):
                found.add(name)
    return found


def main() -> None:
    caps = _load_block(MANIFEST, "VALIDATION_CAPABILITIES")
    declared = set()
    for c in caps:
        declared.update(c.get("env", []) or [])

    # 1. DECLARATION — every secret-like env var in code must be declared.
    used = _scanned_secret_envs()
    undeclared = sorted(used - declared)
    if undeclared:
        sys.exit(
            "FAIL: external dependency NOT declared in docs/ci/VALIDATION.md: "
            f"{undeclared}. Declare it (env, how it's validated, blocking), make the feature "
            "degrade gracefully, and file an OWNER_ACTION if it needs an owner key."
        )

    # Owner actions present (ids) for the surfacing check.
    oa = _load_block(PENDING, "OWNER_ACTIONS")
    oa_ids = {it["id"] for it in oa.get("items", [])}

    problems = []
    for c in caps:
        cid = c["id"]
        val = c.get("validation")
        blocking = bool(c.get("blocking"))
        gap = val == "degraded_only"
        # 3. SURFACING — a real gap must name an existing owner action.
        if gap:
            owner = c.get("owner_action")
            if not owner:
                problems.append(f"{cid}: validation=degraded_only but no owner_action named")
            elif owner not in oa_ids:
                problems.append(f"{cid}: owner_action '{owner}' not found in PENDING_OPS OWNER_ACTIONS")
        # 2. BLOCKING — blocking capability that isn't truly validated fails.
        if blocking and (gap or not c.get("key_in_ci")):
            problems.append(
                f"{cid}: blocking=true but not validated (validation={val}, key_in_ci="
                f"{c.get('key_in_ci')}) — provide the key in CI or set blocking=false consciously"
            )
    if problems:
        sys.exit("FAIL: self-validation gate:\n  - " + "\n  - ".join(problems))

    # Coverage summary (every run shows what is truly validated).
    print("OK: self-validation manifest consistent; all external deps declared")
    for c in caps:
        flag = " [BLOCKING]" if c.get("blocking") else ""
        gapnote = "  <-- GAP" if c.get("validation") == "degraded_only" else ""
        print(f"  {c['id']:10} validation={c.get('validation'):13} key_in_ci={c.get('key_in_ci')}{flag}{gapnote}")


if __name__ == "__main__":
    main()
