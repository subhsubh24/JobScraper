"""Greenhouse ATS client."""
import logging

import requests
from typing import List, Optional
from .base import BaseATSClient, JobListing, get_with_retry

logger = logging.getLogger("career_operator.ingestion.greenhouse")

# Shorter than any serverless function budget (Vercel maxDuration 60s) so a slow board
# fails inside our handler instead of being killed mid-request (DEEP_DIAGNOSIS rule a).
HTTP_TIMEOUT = 20


class GreenhouseClient(BaseATSClient):
    """Client for Greenhouse job board API."""

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def fetch_jobs(self) -> List[JobListing]:
        """Fetch all open jobs from Greenhouse."""
        url = f"{self.BASE_URL}/{self.company_identifier}/jobs"

        self.last_error = None
        try:
            response = get_with_retry(url, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self.last_error = str(e)
            logger.warning("Greenhouse fetch failed for board %s: %s", self.company_identifier, e)
            return []

        # Greenhouse's board API returns a JSON object ``{"jobs": [...]}``. This runs on the LIVE
        # import-preview path over arbitrary third-party JSON, so a malformed payload that is NOT a
        # dict (an error array, null, a string) would make ``data.get(...)`` raise AttributeError
        # and 500 the whole import — the same graceful-degrade gap the per-record guard below
        # covers. Degrade to an empty board.
        if not isinstance(data, dict):
            self.last_error = "unexpected Greenhouse payload (expected an object with 'jobs')"
            logger.warning(
                "Greenhouse board %s: unexpected payload shape (%s), skipping",
                self.company_identifier,
                type(data).__name__,
            )
            return []

        # A PRESENT-but-non-list "jobs" field is a malformed payload, not an empty board — so set
        # last_error (like the top-level guard above) and degrade. This keeps the caller's honesty
        # contract intact: import-preview must report "temporarily unreachable", never fall through
        # to the "no open roles are posted" message on a broken response. (An ABSENT "jobs" key
        # defaults to [], a list — a legitimately empty board, no error.)
        raw_jobs = data.get("jobs", [])
        if not isinstance(raw_jobs, list):
            self.last_error = "unexpected Greenhouse payload ('jobs' was not a list)"
            logger.warning(
                "Greenhouse board %s: 'jobs' field is not a list (%s), skipping",
                self.company_identifier,
                type(raw_jobs).__name__,
            )
            return []

        jobs = []
        for job_data in raw_jobs:
            if not isinstance(job_data, dict):
                logger.warning(
                    "Greenhouse board %s: skipping non-object job", self.company_identifier
                )
                continue
            # The required top-level fields ("id"/"title") are read OUTSIDE the request try/except
            # above, which only catches RequestException — so a bare ``["id"]`` raises KeyError on
            # ONE malformed/partial job and escapes this method. The callers (import-preview,
            # main.ingest) wrap the whole fetch in a blanket ``except Exception``, so that single
            # bad record loses the ENTIRE board: the company is falsely reported unreachable and
            # every well-formed job in the same payload is dropped. Skip just the bad job (like the
            # optional fields already do with ``.get()``) so one upstream defect can't sink the batch.
            job_id = job_data.get("id")
            title = job_data.get("title")
            if job_id is None or not title:
                logger.warning(
                    "Greenhouse board %s: skipping malformed job (missing id/title)",
                    self.company_identifier,
                )
                continue
            # Parse location defensively. This runs on the LIVE import-preview path
            # (POST /api/jobs/import-preview → detector → GreenhouseClient.fetch_jobs), which
            # ingests arbitrary third-party board JSON. A malformed/partial payload where a job's
            # "location" is a non-object (a bare string, null, a number) would make
            # ``.get("location", {}).get(...)`` raise AttributeError on the non-dict and 500 the
            # whole import — the same graceful-degrade gap the id/title skip above guards. Only
            # read the name when location is actually a dict; otherwise degrade to "".
            loc = job_data.get("location")
            location = loc.get("name", "") if isinstance(loc, dict) else ""

            job = JobListing(
                external_id=str(job_id),
                title=title,
                location=location,
                description=None,  # Need to fetch separately
                requirements=None,
                url=job_data.get("absolute_url", ""),
                posted_at=job_data.get("updated_at"),
                department=None,
                remote_type=self._detect_remote_type(f"{title} {location}"),
            )
            jobs.append(job)

        return jobs

    def fetch_job_details(self, job_id: str) -> Optional[JobListing]:
        """Fetch full details for a specific job."""
        url = f"{self.BASE_URL}/{self.company_identifier}/jobs/{job_id}"

        self.last_error = None
        try:
            response = get_with_retry(url, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            job_data = response.json()
        except requests.RequestException as e:
            self.last_error = str(e)
            logger.warning("Greenhouse detail fetch failed for job %s: %s", job_id, e)
            return None

        # Required fields are read outside the request try/except — a partial/malformed detail
        # payload missing "id"/"title" would raise KeyError and 500 the fetch. Treat it as a
        # failed fetch (set last_error, return None) so the caller degrades honestly, exactly
        # like an upstream error.
        gh_id = job_data.get("id")
        title = job_data.get("title")
        if gh_id is None or not title:
            self.last_error = "Greenhouse returned a malformed job detail (missing id/title)"
            logger.warning("Greenhouse detail fetch for job %s: malformed payload (missing id/title)", job_id)
            return None

        location = job_data.get("location", {}).get("name", "")
        content = job_data.get("content", "")

        # Parse departments. Use ``.get("name")`` — a Greenhouse department object can be
        # present but lack a "name" key (partial/malformed API payload), and a bare
        # ``["name"]`` would raise KeyError and 500 the whole detail fetch on one bad job.
        departments = job_data.get("departments", [])
        department = departments[0].get("name") if departments else None

        return JobListing(
            external_id=str(gh_id),
            title=title,
            location=location,
            description=content,
            requirements=None,  # Usually embedded in description
            url=job_data.get("absolute_url", ""),
            posted_at=job_data.get("updated_at"),
            department=department,
            remote_type=self._detect_remote_type(f"{title} {location} {content}"),
        )

    def fetch_all_with_details(self) -> List[JobListing]:
        """Fetch all jobs with their full details."""
        jobs = self.fetch_jobs()
        detailed_jobs = []

        for job in jobs:
            details = self.fetch_job_details(job.external_id)
            if details:
                detailed_jobs.append(details)

        return detailed_jobs
