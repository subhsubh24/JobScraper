#!/usr/bin/env python3
"""Prune orphaned Neon PREVIEW branches (Vercel-integration leftovers).

The Vercel<->Neon integration creates a ``preview/<git-branch>`` Neon branch per PR preview and
does not always delete it on merge, so they accumulate and hit the plan's branch cap. This
deletes ONLY ``preview/*`` Neon branches whose git branch has NO open PR. Safe by construction:
NEVER the default or protected branch, NEVER a non-preview branch (production, vercel-dev, etc.).
Set DRY_RUN=true to list what WOULD be deleted without deleting.

Env: NEON_API_KEY, NEON_PROJECT_ID, GITHUB_TOKEN, GITHUB_REPOSITORY, [DRY_RUN].
"""
import json
import os
import sys
import urllib.error
import urllib.request

NEON = "https://console.neon.tech/api/v2"
GH = "https://api.github.com"
DRY = os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")


def _get(url, token, scheme="Bearer"):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"{scheme} {token}")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _open_pr_heads(repo, token):
    heads, page = set(), 1
    while True:
        data = _get(f"{GH}/repos/{repo}/pulls?state=open&per_page=100&page={page}", token, "token")
        if not data:
            break
        for pr in data:
            heads.add(pr["head"]["ref"])
        if len(data) < 100:
            break
        page += 1
    return heads


def _delete_branch(project, bid, token):
    req = urllib.request.Request(f"{NEON}/projects/{project}/branches/{bid}", method="DELETE")
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status


def main():
    neon_key = os.environ["NEON_API_KEY"]
    project = os.environ["NEON_PROJECT_ID"]
    repo = os.environ["GITHUB_REPOSITORY"]
    gh_token = os.environ["GITHUB_TOKEN"]

    open_heads = _open_pr_heads(repo, gh_token)
    print(f"open PR head branches ({len(open_heads)}): {sorted(open_heads) or '(none)'}")

    branches = _get(f"{NEON}/projects/{project}/branches", neon_key)["branches"]
    to_delete, kept = [], []
    for b in branches:
        name = b.get("name", "")
        if b.get("default") or b.get("protected"):
            kept.append(f"{name} (default/protected)")
        elif not name.startswith("preview/"):
            kept.append(f"{name} (not a preview branch)")
        elif name[len("preview/"):] in open_heads:
            kept.append(f"{name} (open PR)")
        else:
            to_delete.append(b)

    print("\nKEEP:")
    for k in kept:
        print(f"  - {k}")

    verb = "WOULD DELETE (dry-run)" if DRY else "DELETING"
    print(f"\n{verb} {len(to_delete)} orphaned preview branch(es):")
    errs = 0
    for b in to_delete:
        name, bid = b.get("name"), b.get("id")
        if DRY:
            print(f"  - {name} ({bid})")
            continue
        try:
            status = _delete_branch(project, bid, neon_key)
            print(f"  - deleted {name} ({bid}) -> {status}")
        except urllib.error.HTTPError as exc:
            errs += 1
            print(f"  - FAILED {name} ({bid}): {exc.code} {exc.read().decode()[:200]}")
    if errs:
        sys.exit(f"{errs} deletion(s) failed")
    print("\ndone.")


if __name__ == "__main__":
    main()
