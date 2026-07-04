"""Lever ATS client."""
import logging

import requests
from typing import List, Optional
from .base import BaseATSClient, JobListing

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
            response = requests.get(url, params={"mode": "json"}, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self.last_error = str(e)
            logger.warning("Lever fetch failed for board %s: %s", self.company_identifier, e)
            return []

        jobs = []
        for job_data in data:
            # The required fields ("id"/"text") are read outside the request try/except above
            # (which only catches RequestException) — a bare ``["id"]`` raises KeyError on ONE
            # malformed posting and escapes this method. The callers wrap the whole fetch in a
            # blanket ``except Exception``, so that single bad record loses the ENTIRE board (the
            # company is falsely reported unreachable and every good posting is dropped). Skip just
            # the bad posting (like the optional fields already do with ``.get()``) and keep the rest.
            lever_id = job_data.get("id")
            title = job_data.get("text")
            if not lever_id or not title:
                logger.warning(
                    "Lever board %s: skipping malformed posting (missing id/text)",
                    self.company_identifier,
                )
                continue
            # Lever includes full details in listing
            location = job_data.get("categories", {}).get("location", "")
            team = job_data.get("categories", {}).get("team", "")
            commitment = job_data.get("categories", {}).get("commitment", "")

            # Build description from lists
            description_parts = []
            for section in job_data.get("lists", []):
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
