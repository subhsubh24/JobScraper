"""Lever ATS client."""
import requests
from typing import List, Optional
from .base import BaseATSClient, JobListing


class LeverClient(BaseATSClient):
    """Client for Lever job postings API."""

    BASE_URL = "https://api.lever.co/v0/postings"

    def fetch_jobs(self) -> List[JobListing]:
        """Fetch all open jobs from Lever."""
        url = f"{self.BASE_URL}/{self.company_identifier}"

        try:
            response = requests.get(url, params={"mode": "json"}, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"Error fetching Lever jobs: {e}")
            return []

        jobs = []
        for job_data in data:
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
                external_id=job_data["id"],
                title=job_data["text"],
                location=location,
                description=description,
                requirements=None,  # Embedded in description
                url=job_data.get("hostedUrl", ""),
                posted_at=None,  # Lever doesn't provide this easily
                department=team,
                remote_type=self._detect_remote_type(
                    f"{job_data['text']} {location} {commitment}"
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
