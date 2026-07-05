"""Profile enrichment from a user's public GitHub profile (Track A — the market's ``/expand``).

Honest, robust design (VISION "honest > flashy"): we do NOT scrape arbitrary user-supplied
URLs — raw HTML is fragile, JS-rendered, an SSRF surface, and a hallucination magnet (exactly
the "obviously-AI / inaccurate output real users penalise" counter-signal). Instead we accept a
GitHub username / ``github.com`` profile URL, validate the username, and call the PUBLIC GitHub
REST API at the FIXED host ``api.github.com`` — the same shape as the ATS clients hitting fixed
greenhouse/lever hosts, so there is no arbitrary-URL fetch and no SSRF surface.

Each repo's own ``language`` (GitHub-computed) and ``topics`` (author-tagged) are STRUCTURED,
factual signals GitHub already derived from the code — we aggregate them into source-tagged
competencies and NEVER invent a skill. Enrichment is always OPTIONAL metadata: any failure
(unknown user, private-only account, API/network error, rate limit) degrades to an empty
result and never blocks scoring or generation.
"""
import logging
import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

import requests

from src.db.models import EnrichedCompetency, User

logger = logging.getLogger("career_operator.enrichment.github")

# Fixed, trusted host (no arbitrary-URL fetch → no SSRF surface, unlike scraping a user URL).
GITHUB_API = "https://api.github.com"
# Shorter than the serverless function budget (Vercel maxDuration 60s) so a slow API call fails
# INSIDE our handler with a graceful degrade instead of being killed mid-request
# (DEEP_DIAGNOSIS rule a: every external call needs a timeout shorter than the runtime budget).
HTTP_TIMEOUT = 15
# GitHub's real username rule: 1–39 chars, alphanumerics or single non-consecutive hyphens,
# no leading/trailing hyphen. Validating up front means we only ever hit api.github.com with a
# well-formed path segment (defence-in-depth alongside the fixed host).
_USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
# Newest-pushed repos first; cap the page so a prolific account can't drive cost/noise.
_MAX_REPOS = 100
# Cap the persisted competencies so one account can't flood its own profile.
_MAX_COMPETENCIES = 40

SOURCE_TYPE = "github"


@dataclass
class DiscoveredCompetency:
    """One competency derived from structured GitHub data (never invented)."""

    skill: str  # normalized (lowercased) skill/topic name
    evidence: str  # human-readable provenance, e.g. "Primary language in 4 repositories"


def parse_github_username(value: str) -> Optional[str]:
    """Extract a valid GitHub username from a raw handle or a ``github.com`` profile URL.

    Returns ``None`` when the input isn't a valid username or ``github.com`` URL, so the caller
    can degrade honestly (a clear 400) rather than fetch a garbage path.
    """
    value = (value or "").strip()
    if not value:
        return None
    # A URL or dotted host form → require it to be github.com and take the first path segment.
    if "/" in value or "." in value:
        try:
            parsed = urlparse(value if "//" in value else f"https://{value}")
        except ValueError:
            return None
        if (parsed.hostname or "").lower() not in ("github.com", "www.github.com"):
            return None
        segments = [seg for seg in (parsed.path or "").split("/") if seg]
        if not segments:
            return None
        candidate = segments[0]
    else:
        candidate = value
    candidate = candidate.strip()
    return candidate if _USERNAME_RE.match(candidate) else None


def discover_github_competencies(username: str) -> List[DiscoveredCompetency]:
    """Fetch the user's public repos and derive competencies from languages + topics.

    Pure network + parsing; NEVER raises — returns ``[]`` on any failure (unknown user, private
    account, network/API error, non-JSON). Forks are skipped (they aren't evidence of the user's
    own skills). STRUCTURED data only: each repo's own ``language`` + ``topics``.
    """
    url = f"{GITHUB_API}/users/{username}/repos"
    try:
        resp = requests.get(
            url,
            params={"per_page": _MAX_REPOS, "sort": "pushed", "type": "owner"},
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "CareerOperator",
            },
            timeout=HTTP_TIMEOUT,
        )
        if resp.status_code == 404:
            logger.info("GitHub enrichment: user not found: %s", username)
            return []
        resp.raise_for_status()
        repos = resp.json()
    except requests.RequestException as e:
        logger.warning("GitHub enrichment fetch failed for %s: %s", username, e)
        return []
    except ValueError:  # non-JSON body
        logger.warning("GitHub enrichment returned non-JSON for %s", username)
        return []

    if not isinstance(repos, list):
        return []

    lang_counts: "Counter[str]" = Counter()
    topic_counts: "Counter[str]" = Counter()
    for repo in repos:
        if not isinstance(repo, dict) or repo.get("fork"):
            continue
        lang = repo.get("language")
        if isinstance(lang, str) and lang.strip():
            lang_counts[lang.strip()] += 1
        topics = repo.get("topics")
        if isinstance(topics, list):
            for topic in topics:
                if isinstance(topic, str) and topic.strip():
                    topic_counts[topic.strip()] += 1

    discovered: List[DiscoveredCompetency] = []
    seen: set = set()
    # Languages first (strongest signal — GitHub computed them from the actual code).
    for lang, count in lang_counts.most_common():
        key = lang.lower()
        if key in seen:
            continue
        seen.add(key)
        noun = "repository" if count == 1 else "repositories"
        discovered.append(
            DiscoveredCompetency(skill=key, evidence=f"Primary language in {count} {noun}")
        )
    # Then author-tagged topics that aren't already covered by a language.
    for topic, count in topic_counts.most_common():
        key = topic.lower()
        if key in seen:
            continue
        seen.add(key)
        noun = "repository" if count == 1 else "repositories"
        discovered.append(
            DiscoveredCompetency(skill=key, evidence=f"Repository topic ({count} {noun})")
        )
    return discovered[:_MAX_COMPETENCIES]


def replace_github_competencies(
    db, user: User, source_url: str, discovered: List[DiscoveredCompetency]
) -> int:
    """Replace this user's GitHub-sourced competencies with the freshly discovered set.

    Replace (not merge) so a re-import reflects the CURRENT state of the account — a language
    that dropped off (repo deleted / made private) disappears, no stale rows accrue. Flushes but
    does not commit (the caller owns the transaction). Returns the number of rows written.
    """
    db.query(EnrichedCompetency).filter(
        EnrichedCompetency.user_id == user.id,
        EnrichedCompetency.source_type == SOURCE_TYPE,
    ).delete(synchronize_session=False)
    for item in discovered:
        db.add(
            EnrichedCompetency(
                user_id=user.id,
                skill=item.skill,
                source_type=SOURCE_TYPE,
                source_url=source_url[:500],
                evidence=item.evidence[:200],
            )
        )
    db.flush()
    return len(discovered)


def user_enriched_skills(db, user: User) -> set:
    """The user's link-discovered competencies as a lowercase skill set (empty if none).

    Optional signal: a query failure never propagates (enrichment must never break the core
    scoring/generation flow it feeds).
    """
    try:
        rows = (
            db.query(EnrichedCompetency.skill)
            .filter(EnrichedCompetency.user_id == user.id)
            .all()
        )
    except Exception:
        logger.warning("failed to load enriched competencies", exc_info=True)
        return set()
    return {row[0] for row in rows}
