"""Unit coverage for the Greenhouse ATS client's detail-fetch paths.

The import-preview endpoint exercises `fetch_jobs()` only; the per-job detail parsing
(`fetch_job_details`) and the resilient bulk loop (`fetch_all_with_details`) were untested.
These assert the REAL behaviors: a job's content + department parse correctly, and a partial
detail-fetch failure is skipped (not raised) so one bad job never sinks the whole batch.
"""
from unittest.mock import MagicMock, patch

from src.ingestion.greenhouse import GreenhouseClient


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_fetch_job_details_parses_content_and_department():
    client = GreenhouseClient("acme")
    payload = {
        "id": 42,
        "title": "Senior Backend Engineer",
        "location": {"name": "Remote US"},
        "content": "Work from anywhere. Python, FastAPI, PostgreSQL.",
        "departments": [{"name": "Engineering"}, {"name": "Platform"}],
        "absolute_url": "https://example.com/jobs/42",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    with patch("src.ingestion.greenhouse.requests.get", return_value=_Resp(payload)):
        listing = client.fetch_job_details("42")

    assert listing is not None
    assert listing.external_id == "42"
    assert listing.title == "Senior Backend Engineer"
    assert listing.location == "Remote US"
    assert "FastAPI" in (listing.description or "")
    assert listing.department == "Engineering"  # first department wins
    assert listing.remote_type == "remote"  # "work from anywhere" in the content
    assert client.last_error is None


def test_fetch_job_details_returns_none_on_http_error():
    import requests

    client = GreenhouseClient("acme")
    with patch(
        "src.ingestion.greenhouse.requests.get",
        side_effect=requests.RequestException("boom"),
    ):
        assert client.fetch_job_details("99") is None
    # last_error is set so a caller can tell "unreachable" from "no data".
    assert client.last_error == "boom"


def test_fetch_all_with_details_skips_failed_details_not_raises():
    """A detail fetch that fails for one job must NOT blow up the whole batch — the bad
    job is silently skipped and the good ones are still returned."""
    client = GreenhouseClient("acme")

    good = MagicMock(external_id="1")
    bad = MagicMock(external_id="2")
    with patch.object(client, "fetch_jobs", return_value=[good, bad]):
        def _details(job_id):
            return MagicMock(external_id="1") if job_id == "1" else None

        with patch.object(client, "fetch_job_details", side_effect=_details):
            result = client.fetch_all_with_details()

    assert len(result) == 1
    assert result[0].external_id == "1"
