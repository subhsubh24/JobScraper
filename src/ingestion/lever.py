"""Lever ATS client."""
import logging

import requests
from typing import List, Optional
from .base import BaseATSClient, JobListing, get_with_retry

logger = logging.getLogger("career_operator.ingestion.lever")

# Shorter than the serverless function budget so a slow board fails inside our handler
# rather than being killed mid-request (DEEP_DIAGNOSIS rule a).
HTTP_TIMEOUT = 20


class LeverClient(BaseATSClient):
    """Client for Lever job postings API."""

    BASE_URL = "https://api.lever.co/v0/postings"

    def fetch_jobs(self) -> List[JobListing]:
        """Fetch all open jobs from Lever."""
        url = f"{self.BASE_URL}/{self.company_identifier}"

        self.last_error = None
        try:
            response = get_with_retry(url, params={"mode": "json"}, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self.last_error = str(e)
            logger.warning("Lever fetch failed for board %s: %s", self.company_identifier, e)
            return []

        # Lever's board API returns a JSON array of postings. This runs on the LIVE import-preview
        # path (POST /api/jobs/import-preview → detector → LeverClient.fetch_jobs) over arbitrary
        # third-party JSON, so a malformed payload that is NOT a list (an error object, null, a
        # string) would make ``for job_data in data`` iterate the wrong thing or crash — the same
        # graceful-degrade gap the per-record guards below cover. Degrade to an empty board.
        if not isinstance(data, list):
            self.last_error = "unexpected Lever payload (expected a list of postings)"
            logger.warning(
                "Lever board %s: unexpected payload shape (%s), skipping",
                self.company_identifier,
                type(data).__name__,
            )
            return []

        jobs = []
        for job_data in data:
            # The required fields ("id"/"text") are read outside the request try/except above
            # (which only catches RequestException) — a bare ``["id"]`` raises KeyError on ONE
            # malformed posting and escapes this method. The callers wrap the whole fetch in a
            # blanket ``except Exception``, so that single bad record loses the ENTIRE board (the
            # company is falsely reported unreachable and every good posting is dropped). Skip just
            # the bad posting (like the optional fields already do with ``.get()``) and keep the rest.
            if not isinstance(job_data, dict):
                logger.warning(
                    "Lever board %s: skipping non-object posting", self.company_identifier
                )
                continue
            lever_id = job_data.get("id")
            title = job_data.get("text")
            if not lever_id or not title:
                logger.warning(
                    "Lever board %s: skipping malformed posting (missing id/text)",
                    self.company_identifier,
                )
                continue
            # Lever includes full details in listing. ``categories`` may be a non-object (null, a
            # string) on a malformed posting — reading ``.get(...)`` on a non-dict would 500 the
            # whole import (same crash class as the greenhouse ``location`` guard), so only read it
            # when it is actually a dict; otherwise degrade to empty fields.
            categories = job_data.get("categories")
            if not isinstance(categories, dict):
                categories = {}
            location = categories.get("location", "") or ""
            team = categories.get("team", "") or ""
            commitment = categories.get("commitment", "") or ""

            # Build description from lists. ``lists`` may be absent or a non-list, and an individual
            # section may be a non-object — skip anything that isn't a dict rather than crash.
            description_parts = []
            sections = job_data.get("lists")
            if isinstance(sections, list):
                for section in sections:
                    if not isinstance(section, dict):
                        continue
                    description_parts.append(f"## {section.get('text', '')}")
                    description_parts.append(section.get("content", ""))

            description = "\n\n".join(description_parts)

            # Add additional description
            if job_data.get("descriptionPlain"):
                description = job_data["descriptionPlain"] + "\n\n" + description

            job = JobListing(
                external_id=lever_id,
                title=title,
                location=location,
                description=description,
                requirements=None,  # Embedded in description
                url=job_data.get("hostedUrl", ""),
                posted_at=None,  # Lever doesn't provide this easily
                department=team,
                remote_type=self._detect_remote_type(
                    f"{title} {location} {commitment}"
                ),
            )
            jobs.append(job)

        return jobs

    def fetch_job_details(self, job_id: str) -> Optional[JobListing]:
        """Fetch details for a specific job."""
        # Lever includes full details in listing, so just filter
        jobs = self.fetch_jobs()
        for job in jobs:
            if job.external_id == job_id:
                return job
        return None
