"""Unit coverage for the Greenhouse ATS client's detail-fetch paths.

The import-preview endpoint exercises `fetch_jobs()` only; the per-job detail parsing
(`fetch_job_details`) and the resilient bulk loop (`fetch_all_with_details`) were untested.
These assert the REAL behaviors: a job's content + department parse correctly, and a partial
detail-fetch failure is skipped (not raised) so one bad job never sinks the whole batch.
"""
from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.greenhouse import GreenhouseClient


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


def test_fetch_job_details_survives_department_without_name():
    """A department object present but missing "name" must NOT KeyError-500 the fetch — the
    optional field degrades to None while the job still parses (real-world partial payload)."""
    client = GreenhouseClient("acme")
    payload = {
        "id": 7,
        "title": "Data Engineer",
        "location": {"name": "NYC"},
        "content": "ETL, warehousing.",
        "departments": [{"id": 123}],  # malformed: no "name" key
        "absolute_url": "https://example.com/jobs/7",
    }
    with patch("src.ingestion.greenhouse.requests.get", return_value=_Resp(payload)):
        listing = client.fetch_job_details("7")

    assert listing is not None
    assert listing.title == "Data Engineer"
    assert listing.department is None  # gracefully absent, not a crash


@pytest.mark.parametrize("bad_location", [
    "Remote",   # location is a bare string, not an object
    None,       # location is null
    123,        # location is a number
    [],         # location is a list
])
def test_fetch_jobs_survives_non_dict_location(bad_location):
    """A board job whose "location" is a non-object (a bare string / null / number / list) must
    NOT crash ``fetch_jobs`` — this is the LIVE ``/api/jobs/import-preview`` path (import-preview →
    detector → GreenhouseClient.fetch_jobs), which ingests arbitrary third-party board JSON.
    ``.get("location", {}).get(...)`` raises AttributeError on the non-dict and would 500 the whole
    import on one bad job; the guard degrades it to location="" while the well-formed job still
    parses. Mutation-catchable: reverting the isinstance guard reddens these cases."""
    client = GreenhouseClient("acme")
    payload = {"jobs": [
        {"id": 7, "title": "Staff Engineer", "location": bad_location,
         "absolute_url": "https://example.com/jobs/7"},
    ]}
    with patch("src.ingestion.greenhouse.requests.get", return_value=_Resp(payload)):
        jobs = client.fetch_jobs()

    assert len(jobs) == 1  # did not 500 on the malformed payload
    assert jobs[0].title == "Staff Engineer"
    assert jobs[0].location == ""  # gracefully empty, not a crash
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


def test_fetch_jobs_unreachable_sets_last_error_distinct_from_empty():
    """A board that errors (network/HTTP) must return [] AND set last_error, so the caller
    can tell "board unreachable" from "open board with zero roles" — reporting an outage as
    "no jobs" is a real honesty bug the import-preview endpoint depends on avoiding."""
    import requests

    client = GreenhouseClient("acme")
    with patch(
        "src.ingestion.greenhouse.requests.get",
        side_effect=requests.RequestException("503 Service Unavailable"),
    ):
        jobs = client.fetch_jobs()
    assert jobs == []
    assert client.last_error == "503 Service Unavailable"


def test_fetch_jobs_empty_board_returns_empty_with_no_error():
    """A reachable board with zero open roles returns [] and leaves last_error None — the
    truthful "no jobs" state, distinct from the unreachable case above."""
    client = GreenhouseClient("acme")
    with patch("src.ingestion.greenhouse.requests.get", return_value=_Resp({"jobs": []})):
        jobs = client.fetch_jobs()
    assert jobs == []
    assert client.last_error is None


def test_fetch_jobs_populated_board_smoke():
    """Completes the triad (populated vs empty vs unreachable): a board with roles yields
    JobListings and leaves last_error None — so the happy path is provably distinct from the
    two failure/empty states above. (Field-level parsing is covered by the detail-fetch test.)"""
    payload = {"jobs": [{"id": 7, "title": "Staff Engineer", "absolute_url": "https://x/7"}]}
    client = GreenhouseClient("acme")
    with patch("src.ingestion.greenhouse.requests.get", return_value=_Resp(payload)):
        jobs = client.fetch_jobs()
    assert len(jobs) == 1
    assert jobs[0].external_id == "7"
    assert client.last_error is None


def test_fetch_jobs_skips_malformed_job_missing_required_field():
    """A job object missing a required top-level field ("title"/"id") must NOT KeyError-500 the
    whole import — it is skipped (like the optional fields already degrade) and the well-formed
    jobs in the same payload are still returned."""
    payload = {
        "jobs": [
            {"id": 1, "title": "Staff Engineer", "absolute_url": "https://x/1"},
            {"id": 2, "absolute_url": "https://x/2"},          # malformed: no "title"
            {"title": "Ghost Role", "absolute_url": "https://x/3"},  # malformed: no "id"
            {"id": 4, "title": "Backend Engineer", "absolute_url": "https://x/4"},
        ]
    }
    client = GreenhouseClient("acme")
    with patch("src.ingestion.greenhouse.requests.get", return_value=_Resp(payload)):
        jobs = client.fetch_jobs()

    # Only the two well-formed jobs survive; the batch did not crash on the malformed ones.
    assert [j.external_id for j in jobs] == ["1", "4"]
    assert client.last_error is None


@pytest.mark.parametrize("bad", [["jobs", "as", "a", "list"], None, "oops", 42])
def test_fetch_jobs_non_dict_payload_degrades_not_crashes(bad):
    """A top-level payload that is NOT an object (an array, null, a string) must degrade to an
    empty board with last_error set — never AttributeError-500 on ``data.get("jobs")``. This is
    the LIVE import-preview path over arbitrary third-party JSON."""
    client = GreenhouseClient("acme")
    with patch("src.ingestion.greenhouse.requests.get", return_value=_Resp(bad)):
        jobs = client.fetch_jobs()
    assert jobs == []
    assert client.last_error is not None


def test_fetch_jobs_skips_non_dict_job_entry():
    """A non-object element inside the jobs array is skipped, not crashed on."""
    payload = {"jobs": [
        {"id": 1, "title": "Staff Engineer", "absolute_url": "https://x/1"},
        "not-an-object",
        None,
        {"id": 2, "title": "Backend Engineer", "absolute_url": "https://x/2"},
    ]}
    client = GreenhouseClient("acme")
    with patch("src.ingestion.greenhouse.requests.get", return_value=_Resp(payload)):
        jobs = client.fetch_jobs()
    assert [j.external_id for j in jobs] == ["1", "2"]
    assert client.last_error is None


@pytest.mark.parametrize("bad_jobs", [None, 42, "nope", {"not": "a list"}])
def test_fetch_jobs_non_list_jobs_field_degrades_with_last_error(bad_jobs):
    """A PRESENT-but-non-list "jobs" field is a malformed payload, not an empty board: degrade to
    [] AND set last_error so import-preview reports "temporarily unreachable" (honest), never the
    "no open roles" empty-board message. Non-iterable values (None/42) also prove the guard
    prevents a `TypeError: not iterable` crash — reverting it reddens this."""
    client = GreenhouseClient("acme")
    with patch("src.ingestion.greenhouse.requests.get", return_value=_Resp({"jobs": bad_jobs})):
        jobs = client.fetch_jobs()
    assert jobs == []
    assert client.last_error is not None


def test_fetch_job_details_returns_none_on_malformed_payload_missing_title():
    """A detail payload present but missing "title" (partial upstream response) degrades to a
    failed fetch (None + last_error), never a KeyError-500 — same contract as an HTTP error."""
    client = GreenhouseClient("acme")
    payload = {"id": 5, "location": {"name": "NYC"}, "content": "x"}  # no "title"
    with patch("src.ingestion.greenhouse.requests.get", return_value=_Resp(payload)):
        listing = client.fetch_job_details("5")
    assert listing is None
    assert client.last_error and "malformed" in client.last_error.lower()


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
