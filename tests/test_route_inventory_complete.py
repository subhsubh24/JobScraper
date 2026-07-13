"""Guard: docs/ci/ROUTE_INVENTORY.md's route matrix stays COMPLETE and HONEST.

The inventory calls itself "the checklist the journey suites are measured against" and claims to
list every route in `asgi.py`. That claim drifted before (routes shipped without a row), which is
an artifact-integrity bug — a doc that contradicts reality. This test makes the completeness
MECHANICAL: the set of `@app.<verb>("path")` routes declared in asgi.py must exactly equal the set
of rows in the matrix. Add a route without a matrix row (or leave a stale row) and this fails LOUD.
"""
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_ASGI = _ROOT / "asgi.py"
_INVENTORY = _ROOT / "docs" / "ci" / "ROUTE_INVENTORY.md"

_VERBS = ("get", "post", "patch", "put", "delete")


def _routes_in_asgi() -> set:
    """Every (METHOD, path) declared with an @app.<verb>(...) decorator in asgi.py.

    Handles multi-line decorators (the path string may sit on a following line) by scanning a
    small window after each decorator opener — mirrors how the routes are actually declared.
    """
    lines = _ASGI.read_text().splitlines()
    found = set()
    for i, line in enumerate(lines):
        m = re.search(r"@app\.(" + "|".join(_VERBS) + r")\(", line)
        if not m:
            continue
        verb = m.group(1)
        window = " ".join(lines[i:i + 4])
        pm = re.search(r"@app\." + verb + r"\(\s*[\"']([^\"']+)[\"']", window)
        assert pm, f"could not parse the path for an @app.{verb}( at asgi.py:{i + 1}"
        found.add((verb.upper(), pm.group(1)))
    return found


def _routes_in_matrix() -> set:
    """Every (METHOD, path) row in the 'Complete API route -> coverage matrix' table."""
    text = _INVENTORY.read_text()
    # Anchor on the '###' heading line specifically (not the intro-paragraph mention of the same
    # phrase) so an unrelated doc edit between the intro and the table can't move the parse window.
    start = text.index("### Complete API route")
    body = text[start:]
    found = set()
    for row in re.finditer(r"^\|\s*(GET|POST|PATCH|PUT|DELETE)\s*\|\s*`([^`]+)`\s*\|", body, re.M):
        found.add((row.group(1), row.group(2)))
    return found


def test_matrix_lists_exactly_the_asgi_routes():
    asgi_routes = _routes_in_asgi()
    matrix_routes = _routes_in_matrix()

    missing = asgi_routes - matrix_routes  # real routes with no inventory row (the drift bug)
    phantom = matrix_routes - asgi_routes  # inventory rows for routes that no longer exist

    assert not missing, (
        "routes in asgi.py are MISSING from the ROUTE_INVENTORY matrix (add a row + a real test): "
        + ", ".join(f"{m} {p}" for m, p in sorted(missing))
    )
    assert not phantom, (
        "ROUTE_INVENTORY matrix lists routes that don't exist in asgi.py (stale rows): "
        + ", ".join(f"{m} {p}" for m, p in sorted(phantom))
    )


def test_matrix_is_non_trivial():
    """Sanity: the parser actually found the table (guards against a silent regex/format break)."""
    assert len(_routes_in_matrix()) >= 40
