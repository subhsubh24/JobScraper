"""ATS detection from company careers pages."""
import re
import requests
from typing import Optional, Tuple

from src.db.models import ATSType


class ATSDetector:
    """Detects which ATS a company uses from their careers page."""

    ATS_PATTERNS = {
        ATSType.GREENHOUSE: [
            r"boards\.greenhouse\.io/(\w+)",
            r"greenhouse\.io",
            r"grnh\.se",
        ],
        ATSType.LEVER: [
            r"jobs\.lever\.co/(\w+)",
            r"lever\.co",
        ],
        ATSType.ASHBY: [
            r"jobs\.ashbyhq\.com/(\w+)",
            r"ashbyhq\.com",
        ],
        ATSType.WORKDAY: [
            r"myworkday\.com",
            r"workday\.com",
            r"wd\d+\.myworkdayjobs\.com",
        ],
    }

    def detect_from_url(self, url: str) -> Tuple[ATSType, Optional[str]]:
        """
        Detect ATS type from a URL.

        Returns:
            Tuple of (ATSType, identifier) where identifier is the company's
            board token/slug if detected.
        """
        url_lower = url.lower()

        for ats_type, patterns in self.ATS_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, url_lower)
                if match:
                    identifier = match.group(1) if match.lastindex else None
                    return ats_type, identifier

        return ATSType.UNKNOWN, None

    def detect_from_careers_page(self, careers_url: str) -> Tuple[ATSType, Optional[str]]:
        """
        Detect ATS by fetching and analyzing a careers page.

        Returns:
            Tuple of (ATSType, identifier)
        """
        # First check if the URL itself reveals the ATS
        ats_type, identifier = self.detect_from_url(careers_url)
        if ats_type != ATSType.UNKNOWN:
            return ats_type, identifier

        # Fetch the page and look for ATS indicators
        try:
            response = requests.get(
                careers_url,
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (compatible; CareerOperator/1.0)"},
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching careers page: {e}")
            return ATSType.UNKNOWN, None

        # Check final URL after redirects
        ats_type, identifier = self.detect_from_url(response.url)
        if ats_type != ATSType.UNKNOWN:
            return ats_type, identifier

        # Check page content for embedded job boards
        content = response.text.lower()

        for ats_type, patterns in self.ATS_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    identifier = match.group(1) if match.lastindex else None
                    return ats_type, identifier

        # Look for iframes or scripts pointing to ATS
        iframe_patterns = [
            (ATSType.GREENHOUSE, r'src=["\']https?://boards\.greenhouse\.io/(\w+)'),
            (ATSType.LEVER, r'src=["\']https?://jobs\.lever\.co/(\w+)'),
            (ATSType.ASHBY, r'src=["\']https?://jobs\.ashbyhq\.com/(\w+)'),
        ]

        for ats_type, pattern in iframe_patterns:
            match = re.search(pattern, response.text, re.IGNORECASE)
            if match:
                return ats_type, match.group(1)

        return ATSType.UNKNOWN, None

    def get_client_for_company(self, ats_type: ATSType, identifier: str):
        """Get the appropriate ATS client for a company."""
        from .greenhouse import GreenhouseClient
        from .lever import LeverClient

        if ats_type == ATSType.GREENHOUSE:
            return GreenhouseClient(identifier)
        elif ats_type == ATSType.LEVER:
            return LeverClient(identifier)
        else:
            raise ValueError(f"No client available for ATS type: {ats_type}")
