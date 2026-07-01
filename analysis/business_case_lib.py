"""Shared scenario inputs for the Year-1 ARR projection (docs/BUSINESS_CASE.md).

Committed, deterministic inputs only (FACTORY_STANDARD S22) -- no live network/secrets.
Each scenario is (paying subscribers at end of Y1, blended realized ARPA/yr in USD).
Update this file (and re-cite the recomputed value in BUSINESS_CASE.md) whenever the
underlying assumption changes -- never hand-edit the doc's numbers independently.
"""

SCENARIOS = {
    "conservative": {"subs": 150, "arpa": 110},
    "base": {"subs": 500, "arpa": 115},
    "optimistic": {"subs": 1100, "arpa": 120},
}


def arr(scenario):
    s = SCENARIOS[scenario]
    return s["subs"] * s["arpa"]
