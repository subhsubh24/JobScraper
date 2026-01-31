"""Greenhouse ATS client."""
import requests
from typing import List, Optional
from .base import BaseATSClient, JobListing


class GreenhouseClient(BaseATSClient):
    """Client for Greenhouse job board API."""

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def fetch_jobs(self) -> List[JobListing]:
        """Fetch all open jobs from Greenhouse."""
        url = f"{self.BASE_URL}/{self.company_identifier}/jobs"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"Error fetching Greenhouse jobs: {e}")
            return []

        jobs = []
        for job_data in data.get("jobs", []):
            location = job_data.get("location", {}).get("name", "")

            job = JobListing(
                external_id=str(job_data["id"]),
                title=job_data["title"],
                location=location,
                description=None,  # Need to fetch separately
                requirements=None,
                url=job_data.get("absolute_url", ""),
                posted_at=job_data.get("updated_at"),
                department=None,
                remote_type=self._detect_remote_type(f"{job_data['title']} {location}"),
            )
            jobs.append(job)

        return jobs

    def fetch_job_details(self, job_id: str) -> Optional[JobListing]:
        """Fetch full details for a specific job."""
        url = f"{self.BASE_URL}/{self.company_identifier}/jobs/{job_id}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            job_data = response.json()
        except requests.RequestException as e:
            print(f"Error fetching job details: {e}")
            return None

        location = job_data.get("location", {}).get("name", "")
        content = job_data.get("content", "")

        # Parse departments
        departments = job_data.get("departments", [])
        department = departments[0]["name"] if departments else None

        return JobListing(
            external_id=str(job_data["id"]),
            title=job_data["title"],
            location=location,
            description=content,
            requirements=None,  # Usually embedded in description
            url=job_data.get("absolute_url", ""),
            posted_at=job_data.get("updated_at"),
            department=department,
            remote_type=self._detect_remote_type(f"{job_data['title']} {location} {content}"),
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
