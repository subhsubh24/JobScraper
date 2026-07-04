"""Greenhouse ATS client."""
import logging

import requests
from typing import List, Optional
from .base import BaseATSClient, JobListing

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
            response = requests.get(url, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self.last_error = str(e)
            logger.warning("Greenhouse fetch failed for board %s: %s", self.company_identifier, e)
            return []

        jobs = []
        for job_data in data.get("jobs", []):
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
            location = job_data.get("location", {}).get("name", "")

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
            response = requests.get(url, timeout=HTTP_TIMEOUT)
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
