"""SSRF guard for server-side fetches of user-supplied URLs.

The ATS import feature fetches a careers URL the *user* provides. Without a guard an
authenticated user could point it at internal infrastructure (cloud metadata at
169.254.169.254, localhost databases, RFC1918 hosts) and use timing/error differences
as a port-scanning oracle. We block non-http(s) schemes and any URL whose hostname
resolves to a private / loopback / link-local / reserved address.

The HTTP-redirect vector is closed by ``get_with_redirect_guard`` below (every hop is
re-validated before it is fetched). Residual risk still documented, not yet closed here: a
hostname that passes this check but is re-resolved to a private IP at connect time (DNS
rebinding). Fully closing that needs a custom connection-validating transport — tracked in
PENDING_OPS. This guard closes the direct, hostname->private, AND redirect vectors.
"""
import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import requests


class UnsafeURLError(ValueError):
    """Raised when a URL is not safe to fetch server-side."""


# HTTP status codes that carry a ``Location`` redirect (per requests' REDIRECT_STATI).
_REDIRECT_STATI = (301, 302, 303, 307, 308)
# A page behind more than a handful of redirects is not a legitimate careers page; cap it so a
# redirect loop can never spin (and so an attacker can't chain hops to probe many internal hosts).
MAX_REDIRECTS = 5


def assert_public_http_url(url: str) -> None:
    """Raise UnsafeURLError unless `url` is an http(s) URL that resolves only to public IPs."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise UnsafeURLError("Only http(s) URLs are allowed.")
    host = parsed.hostname
    if not host:
        raise UnsafeURLError("URL has no host.")

    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as e:
        raise UnsafeURLError(f"Host could not be resolved: {host}") from e

    for info in infos:
        sockaddr = info[4]
        ip = ipaddress.ip_address(sockaddr[0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise UnsafeURLError(f"URL resolves to a non-public address: {ip}")


def get_with_redirect_guard(url, *, timeout, headers=None, max_redirects=MAX_REDIRECTS):
    """GET a user-supplied URL, re-validating EVERY redirect hop against the SSRF guard.

    ``requests``' ``allow_redirects=True`` validates only the INITIAL url; a 3xx whose
    ``Location`` points at an internal host (cloud metadata, localhost, RFC1918) would then be
    fetched, silently bypassing ``assert_public_http_url``. So we disable auto-redirects and
    follow them manually, asserting each hop is a public http(s) URL BEFORE it is connected to.

    Raises ``UnsafeURLError`` on an unsafe hop or too many redirects; otherwise propagates
    ``requests.RequestException`` exactly like a normal ``requests.get`` so existing callers'
    error handling is unchanged. Returns the final ``requests.Response`` (``resp.url`` is the
    last, fully-validated URL).
    """
    current = url
    for _ in range(max_redirects + 1):
        assert_public_http_url(current)  # validate BEFORE connecting — the whole point
        resp = requests.get(current, timeout=timeout, headers=headers, allow_redirects=False)
        location = resp.headers.get("location")
        if resp.status_code in _REDIRECT_STATI and location:
            # Resolve relative redirects against the current URL, then loop to re-validate.
            current = urljoin(current, location)
            continue
        return resp
    raise UnsafeURLError(f"Too many redirects (> {max_redirects}).")
