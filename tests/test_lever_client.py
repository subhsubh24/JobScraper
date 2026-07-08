"""Unit coverage for the Lever ATS client's resilience to malformed upstream payloads.

Mirrors the Greenhouse client's contract: the required top-level fields ("id"/"text") are read
outside the request try/except (which only catches RequestException), so a partial/malformed
posting must be SKIPPED, never allowed to raise KeyError and 500 the whole import-preview. The
well-formed postings in the same payload still parse.
"""
import requests
from unittest.mock import patch

from src.ingestion.lever import LeverClient


class _Resp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        # A real requests.Response has a status_code; the retry helper (get_with_retry) reads it
        # to decide whether the response is transient. 200 = non-retryable (returned as-is).
        self.status_code = status_code

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_fetch_jobs_parses_well_formed_posting():
    payload = [
        {
            "id": "abc-123",
            "text": "Senior Backend Engineer",
            "categories": {"location": "Remote", "team": "Platform", "commitment": "Full-time"},
            "descriptionPlain": "Python, FastAPI, PostgreSQL. Work from anywhere.",
            "hostedUrl": "https://jobs.lever.co/acme/abc-123",
        }
    ]
    client = LeverClient("acme")
    with patch("src.ingestion.lever.requests.get", return_value=_Resp(payload)):
        jobs = client.fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0].external_id == "abc-123"
    assert jobs[0].title == "Senior Backend Engineer"
    assert jobs[0].department == "Platform"
    assert "FastAPI" in (jobs[0].description or "")
    assert client.last_error is None


def test_fetch_jobs_skips_malformed_posting_missing_required_field():
    """A posting missing a required field ("text"/"id") is skipped rather than KeyError-500ing
    the whole batch; the well-formed postings still come through."""
    payload = [
        {"id": "1", "text": "Staff Engineer", "hostedUrl": "https://x/1"},
        {"id": "2", "hostedUrl": "https://x/2"},              # malformed: no "text"
        {"text": "Ghost Role", "hostedUrl": "https://x/3"},   # malformed: no "id"
        {"id": "4", "text": "Backend Engineer", "hostedUrl": "https://x/4"},
    ]
    client = LeverClient("acme")
    with patch("src.ingestion.lever.requests.get", return_value=_Resp(payload)):
        jobs = client.fetch_jobs()

    assert [j.external_id for j in jobs] == ["1", "4"]
    assert client.last_error is None


def test_fetch_jobs_unreachable_sets_last_error_distinct_from_empty():
    """A board that errors returns [] AND sets last_error — so the caller can tell "unreachable"
    from "open board with zero roles" (the import-preview honesty contract)."""
    client = LeverClient("acme")
    with patch(
        "src.ingestion.lever.requests.get",
        side_effect=requests.RequestException("503 Service Unavailable"),
    ):
        jobs = client.fetch_jobs()
    assert jobs == []
    assert client.last_error == "503 Service Unavailable"


def test_fetch_jobs_empty_board_returns_empty_with_no_error():
    client = LeverClient("acme")
    with patch("src.ingestion.lever.requests.get", return_value=_Resp([])):
        jobs = client.fetch_jobs()
    assert jobs == []
    assert client.last_error is None


def test_fetch_jobs_non_list_payload_degrades_not_crashes():
    """A payload that is NOT a list (an error object, null, a string) degrades to an empty board
    with last_error set — it must never crash the whole import-preview."""
    for bad in ({"error": "not found"}, None, "oops", 42):
        client = LeverClient("acme")
        with patch("src.ingestion.lever.requests.get", return_value=_Resp(bad)):
            jobs = client.fetch_jobs()
        assert jobs == []
        assert client.last_error is not None


def test_fetch_jobs_skips_non_dict_posting():
    """A non-object element in the postings array is skipped, not crashed on."""
    payload = [
        {"id": "1", "text": "Staff Engineer", "hostedUrl": "https://x/1"},
        "not-an-object",
        None,
        {"id": "2", "text": "Backend Engineer", "hostedUrl": "https://x/2"},
    ]
    client = LeverClient("acme")
    with patch("src.ingestion.lever.requests.get", return_value=_Resp(payload)):
        jobs = client.fetch_jobs()
    assert [j.external_id for j in jobs] == ["1", "2"]


def test_fetch_jobs_handles_non_dict_categories_and_lists():
    """A malformed posting whose "categories"/"lists" are non-object/non-list still parses
    (the crash class that PR #306 fixed for greenhouse's "location") — degrades to empty fields,
    never AttributeError-500s the batch."""
    payload = [
        {
            "id": "1", "text": "Engineer", "hostedUrl": "https://x/1",
            "categories": "should-be-an-object",   # non-dict → empty location/team/commitment
            "lists": "should-be-a-list",            # non-list → no description sections
        },
        {
            "id": "2", "text": "Engineer 2", "hostedUrl": "https://x/2",
            "categories": {"location": "Remote"},
            "lists": ["not-a-section", {"text": "About", "content": "We build things."}],
        },
    ]
    client = LeverClient("acme")
    with patch("src.ingestion.lever.requests.get", return_value=_Resp(payload)):
        jobs = client.fetch_jobs()
    assert [j.external_id for j in jobs] == ["1", "2"]
    assert jobs[0].location == ""            # degraded from the non-dict categories
    assert jobs[1].location == "Remote"
    assert "We build things." in (jobs[1].description or "")  # the one valid section parsed
    assert client.last_error is None
