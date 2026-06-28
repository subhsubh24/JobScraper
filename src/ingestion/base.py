"""Base class for ATS clients."""
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class JobListing:
    """Normalized job listing from any ATS."""
    external_id: str
    title: str
    location: Optional[str]
    description: Optional[str]
    requirements: Optional[str]
    url: str
    posted_at: Optional[str]
    department: Optional[str]
    remote_type: Optional[str]  # remote, hybrid, onsite


class BaseATSClient(ABC):
    """Base class for ATS API clients."""

    def __init__(self, company_identifier: str):
        """
        Initialize the client.

        Args:
            company_identifier: The company's identifier for this ATS
                              (e.g., board token for Greenhouse)
        """
        self.company_identifier = company_identifier
        # Set to the error string when the last fetch failed (network/HTTP), so callers
        # can tell "the board was unreachable" apart from "the board has no open jobs"
        # — the difference between an honest empty state and a silent lie.
        self.last_error: Optional[str] = None

    @abstractmethod
    def fetch_jobs(self) -> List[JobListing]:
        """Fetch all open jobs from this company."""
        pass

    @abstractmethod
    def fetch_job_details(self, job_id: str) -> Optional[JobListing]:
        """Fetch details for a specific job."""
        pass

    def _detect_remote_type(self, text: str) -> str:
        """Detect if a job is remote based on text content."""
        text_lower = text.lower()

        if any(phrase in text_lower for phrase in [
            "fully remote", "100% remote", "remote only",
            "work from anywhere", "remote position"
        ]):
            return "remote"
        elif any(phrase in text_lower for phrase in [
            "hybrid", "flexible", "partial remote",
            "2 days in office", "3 days in office"
        ]):
            return "hybrid"
        elif any(phrase in text_lower for phrase in [
            "on-site only", "in-office", "onsite required",
            "no remote", "in person"
        ]):
            return "onsite"

        return "unknown"
