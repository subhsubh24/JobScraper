"""Regression coverage for scripts/validate_gtm.py's honesty gate.

Pins the METRIC-WITHOUT-A-SOURCE tripwire across ALL metric-bearing GROWTH_STATUS sections
(funnel/acquisition/pmf/channels/outreach/email/content) -- not just the original four. The
independent GTM Auditor (GTM_SCORECARD.md, as_of 2026-07-16, metric_integrity top_gap) found
that METRIC_SECTIONS omitted outreach/email/content, leaving a latent hole where a fabricated
non-zero number in one of those sections would escape the gate. Fixed in the same change that
adds this test; this test proves the fix by injecting an unsourced non-zero into each section.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import scripts.validate_gtm as vg  # noqa: E402

HONEST_HEADER = """# GROWTH STATUS test fixture

```yaml
GROWTH_STATUS:
  project: jobscraper
  phase: pre_launch
  channels_connected: []
"""

HONEST_TAIL = """
```
"""


def _write_status(tmp_path, body: str) -> Path:
    status = tmp_path / "GROWTH_STATUS.md"
    status.write_text(HONEST_HEADER + body + HONEST_TAIL)
    return status


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Point the module at a throwaway status/scorecard pair so the real repo files never load."""
    monkeypatch.setattr(vg, "STATUS", tmp_path / "GROWTH_STATUS.md")
    monkeypatch.setattr(vg, "SCORECARD", tmp_path / "GTM_SCORECARD.md")  # absent -> skipped
    yield


def _run(monkeypatch, argv=()):
    monkeypatch.setattr(sys, "argv", ["validate_gtm.py", *argv])
    try:
        vg.main()
        return 0
    except SystemExit as exc:
        return exc.code or 0


@pytest.mark.parametrize("section", ["funnel", "acquisition", "pmf", "channels"])
def test_unsourced_nonzero_fails_original_sections(tmp_path, monkeypatch, capsys, section):
    _write_status(tmp_path, f"  {section}:\n    signups_total: 1234\n")
    assert _run(monkeypatch) == 1
    assert "METRIC WITHOUT A SOURCE" in capsys.readouterr().err


@pytest.mark.parametrize("section", ["outreach", "email", "content"])
def test_unsourced_nonzero_fails_newly_covered_sections(tmp_path, monkeypatch, capsys, section):
    """The gap the auditor found: these three sections were NOT walked before this fix."""
    _write_status(tmp_path, f"  {section}:\n    drafted_7d: 7\n")
    assert _run(monkeypatch) == 1
    assert "METRIC WITHOUT A SOURCE" in capsys.readouterr().err


def test_zero_metrics_in_all_sections_pass(tmp_path, monkeypatch, capsys):
    body = (
        "  funnel:\n    signups_total: 0\n"
        "  outreach:\n    drafted_7d: 0\n"
        "  email:\n    list_size: 0\n"
        "  content:\n    published: 0\n"
    )
    _write_status(tmp_path, body)
    assert _run(monkeypatch) == 0
    assert "OK" in capsys.readouterr().out


def test_nonzero_with_declared_source_passes(tmp_path, monkeypatch, capsys):
    body = (
        "  outreach:\n    drafted_7d: 3\n"
        "  validation:\n"
        "    sources:\n"
        "      - name: gmail\n        status: available\n"
    )
    _write_status(tmp_path, body)
    assert _run(monkeypatch) == 0
    assert "OK" in capsys.readouterr().out
