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
    Validates a URL against SSRF vulnerabilities.
    Blocks private IP spaces (RFC 1918), loopback, link-local (169.254.x.x), and AWS/GCP metadata endpoints.
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
