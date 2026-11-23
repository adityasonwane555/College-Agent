"""
BUDDY AI 2.0 — Server-Side Request Forgery (SSRF) URL Security Validator

Architecture & Threat Modeling:
  - SSRF Mitigation:
      - Validates all external target URLs before outbound network requests are dispatched by search or scraper tools.
  - Multi-Stage Network Filtering:
      - Protocol Enforcement: Permits only explicit 'http' and 'https' schemes; rejects file://, ftp://, gopher://, etc.
      - Hostname Blacklisting: Prohibits loopback names ('localhost', '127.0.0.1', '::1', '0.0.0.0') and cloud metadata hostnames
        ('metadata.google.internal', 'instance-data').
      - Dynamic DNS Resolution & IP Inspection: Resolves hostnames to underlying IPv4/IPv6 addresses via socket.gethostbyname.
      - RFC IP Range Enforcement: Uses python's ipaddress module to block private subnets (RFC 1918 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16),
        loopback addresses (127.0.0.0/8), link-local autoconfiguration (169.254.0.0/16), and reserved spaces.
      - Cloud Metadata Protection: Explicitly blocks direct IP requests to 169.254.169.254 (AWS, Azure, GCP metadata endpoints).
"""

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple


BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "metadata.google.internal",
    "instance-data",
}


def is_safe_url(url: str) -> Tuple[bool, str]:
    """
    Validates an untrusted target URL against Server-Side Request Forgery (SSRF) vulnerabilities.
    Blocks private IP spaces (RFC 1918), loopback, link-local (169.254.x.x), and cloud metadata endpoints.

    Args:
        url: Target web URL string to validate.

    Returns:
        Tuple[bool, str]: (is_safe, reason_or_status_message).
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"Unsupported scheme '{parsed.scheme}'. Only http and https allowed."

        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname in URL."

        if hostname.lower() in BLOCKED_HOSTNAMES:
            return False, f"Access to '{hostname}' is prohibited (SSRF prevention)."

        # Resolve IP address
        try:
            ip_str = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_str)
        except Exception as e:
            return False, f"Failed to resolve hostname '{hostname}': {str(e)}"

        # Explicitly protect AWS/Azure/GCP metadata IP 169.254.169.254
        if ip_str == "169.254.169.254":
            return False, "Access to cloud instance metadata endpoint is blocked."

        # Check if private, loopback, link_local, or reserved
        if ip_obj.is_private:
            return False, f"Access to private IP space ({ip_str}) is blocked."
        if ip_obj.is_loopback:
            return False, f"Access to loopback address ({ip_str}) is blocked."
        if ip_obj.is_link_local:
            return False, f"Access to link-local address ({ip_str}) is blocked."
        if ip_obj.is_reserved:
            return False, f"Access to reserved IP space ({ip_str}) is blocked."

        return True, "URL is safe."
    except Exception as e:
        return False, f"URL validation error: {str(e)}"


def is_https_url(url: str) -> bool:
    """
    Checks whether a URL uses secure HTTPS protocol.

    Args:
        url: Web URL string.

    Returns:
        bool: True if scheme is https.
    """
    try:
        return urlparse(url).scheme.lower() == "https"
    except Exception:
        return False


def sanitize_url_for_display(url: str) -> str:
    """
    Strips query parameters containing sensitive tokens or sessions from URLs for safe chat display.

    Args:
        url: Raw URL string.

    Returns:
        str: Cleaned URL showing scheme, host, and path.
    """
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}{p.path}"
    except Exception:
        return url
