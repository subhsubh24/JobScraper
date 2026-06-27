"""Utility functions."""


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length with ellipsis."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def clean_html(html: str) -> str:
    """Remove HTML tags from text."""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html)


def extract_salary_range(text: str) -> tuple:
    """Extract salary range from text."""
    import re

    # Look for patterns like $100,000 - $150,000 or $100k-150k
    patterns = [
        r'\$(\d{1,3}(?:,\d{3})*)\s*[-–]\s*\$(\d{1,3}(?:,\d{3})*)',
        r'\$(\d+)k\s*[-–]\s*\$?(\d+)k',
        r'(\d{1,3}(?:,\d{3})*)\s*[-–]\s*(\d{1,3}(?:,\d{3})*)\s*(?:USD|per year)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            min_sal = int(match.group(1).replace(',', ''))
            max_sal = int(match.group(2).replace(',', ''))

            # Handle k notation
            if min_sal < 1000:
                min_sal *= 1000
            if max_sal < 1000:
                max_sal *= 1000

            return min_sal, max_sal

    return None, None
