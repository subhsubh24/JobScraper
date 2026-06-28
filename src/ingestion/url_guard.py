"""SSRF guard for server-side fetches of user-supplied URLs.

The ATS import feature fetches a careers URL the *user* provides. Without a guard an
authenticated user could point it at internal infrastructure (cloud metadata at
169.254.169.254, localhost databases, RFC1918 hosts) and use timing/error differences
as a port-scanning oracle. We block non-http(s) schemes and any URL whose hostname
resolves to a private / loopback / link-local / reserved address.

Residual risk (documented, not yet closed here): a hostname that passes this check but
is later re-resolved to a private IP at connect time (DNS rebinding), or an HTTP redirect
to a private host. Fully closing those needs a custom connection-validating transport —
tracked in PENDING_OPS. This guard closes the direct and hostname->private vectors.
"""
import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeURLError(ValueError):
    """Raised when a URL is not safe to fetch server-side."""


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
