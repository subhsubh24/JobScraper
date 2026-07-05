"""Base class for ATS clients."""
import logging
import time
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

import requests

logger = logging.getLogger("career_operator.ingestion")

# Transient upstream statuses worth a bounded retry: rate limiting + gateway/server errors.
# A busy Greenhouse/Lever board returns these briefly; without a retry ONE transient blip is
# reported to the user as "board unreachable" and every good job in it is dropped.
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
# Bounded so the added latency stays well under the serverless budget: at most 2 retries with
# 0.5s then 1.0s backoff (~1.5s worst case) on top of the (fast-returning) error responses.
_MAX_RETRIES = 2
_BACKOFF_BASE = 0.5


def get_with_retry(url: str, *, timeout: int, **kwargs) -> requests.Response:
    """GET with a bounded retry on TRANSIENT upstream failures.

    Retries only on fast-failing signals — a retryable HTTP status (429/5xx, which return
    quickly) or a ``ConnectionError`` — and NEVER on a ``Timeout``: a timeout has already
    consumed part of the serverless budget, so retrying it risks overrunning the function
    (DEEP_DIAGNOSIS rule a). Returns the final ``Response`` (so the caller's ``raise_for_status``
    handling is unchanged) or re-raises the final ``requests`` exception on exhaustion — the
    caller's existing ``except requests.RequestException`` still degrades honestly.
    """
    attempt = 0
    while True:
        try:
            response = requests.get(url, timeout=timeout, **kwargs)
        except requests.Timeout:
            # A timeout has already consumed part of the serverless budget — retrying risks
            # overrunning the function (DEEP_DIAGNOSIS rule a), so NEVER retry it. This clause
            # MUST precede the ConnectionError one: ``requests.ConnectTimeout`` subclasses BOTH
            # Timeout AND ConnectionError, so catching ConnectionError first would wrongly retry
            # a connect-timeout (up to 3×timeout ≈ past the 60s budget) — the exact overrun this
            # helper exists to avoid.
            raise
        except requests.ConnectionError:
            if attempt >= _MAX_RETRIES:
                raise
        else:
            if response.status_code not in _RETRYABLE_STATUS or attempt >= _MAX_RETRIES:
                return response
            logger.info(
                "ATS fetch got transient %s from %s; retry %d/%d",
                response.status_code, url, attempt + 1, _MAX_RETRIES,
            )
        attempt += 1
        time.sleep(_BACKOFF_BASE * (2 ** (attempt - 1)))


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
