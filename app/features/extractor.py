"""URL feature extraction — pure functions, no I/O, no network."""

import logging
import re
from urllib.parse import parse_qs, urlparse

import numpy as np
import tldextract

from .constants import BRAND_NAMES, FEATURE_NAMES, SUSPICIOUS_TLDS

logger = logging.getLogger(__name__)

IP_PATTERN = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")


def _default_features() -> dict[str, float]:
    """Return default feature dict (all zeros)."""
    return {name: 0.0 for name in FEATURE_NAMES}


def _is_valid_ip(hostname: str) -> bool:
    """Validate that hostname is a valid IPv4 address."""
    parts = hostname.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        num = int(part)
        if num < 0 or num > 255:
            return False
    return True


def has_ip_address(hostname: str) -> int:
    """Return 1 if hostname is a raw IPv4 address, else 0."""
    if not IP_PATTERN.match(hostname):
        return 0
    return int(_is_valid_ip(hostname))


def has_brand_in_subdomain(subdomain: str, domain: str) -> int:
    """Return 1 if a known brand appears in subdomain but not in domain."""
    subdomain_lower = subdomain.lower()
    domain_lower = domain.lower()
    for brand in BRAND_NAMES:
        if brand in subdomain_lower and brand not in domain_lower:
            return 1
    return 0


def extract_features(url: str) -> dict[str, float]:
    """
    Extract 15 numerical features from a URL string.
    Pure function — no network calls, no I/O.
    Returns dict with keys matching FEATURES.md exactly.
    On any parse error, returns default feature dict (all zeros).
    """
    if not url or not isinstance(url, str):
        return _default_features()

    try:
        parsed = urlparse(url)

        if not parsed.scheme or not parsed.netloc:
            # No scheme provided; url is not a valid http/https URL
            return _default_features()

        ext = tldextract.extract(url)

        domain = ext.domain
        registered_domain = ext.registered_domain or domain

        url_length = len(url)
        domain_length = len(registered_domain)
        path_length = len(parsed.path)

        num_dots = url.count(".")
        num_hyphens = url.count("-")
        num_at_symbols = url.count("@")

        query_params = parse_qs(parsed.query)
        num_query_params = len(query_params)

        hostname = parsed.hostname or ""
        # Only validate as IP if scheme present, otherwise hostname may be None/empty
        has_ip = 1 if hostname and has_ip_address(hostname) else 0

        has_https = 1 if parsed.scheme == "https" else 0

        tld = ext.suffix
        tld_suspicious = 1 if tld and tld.lower() in SUSPICIOUS_TLDS else 0

        # Count subdomain parts: ext.subdomain may be "a.b.c"
        subdomain_parts = ext.subdomain.split(".") if ext.subdomain else []
        subdomain_depth = len([p for p in subdomain_parts if p])

        # Path depth: count non-empty path segments
        path_segments = parsed.path.split("/") if parsed.path else []
        path_depth = len([seg for seg in path_segments if seg])

        brand_subdomain = has_brand_in_subdomain(ext.subdomain, domain)

        lexical_diversity = len(set(url)) / len(url) if url else 0.0

        digit_count = sum(c.isdigit() for c in url)
        digit_ratio = digit_count / len(url) if url else 0.0

        return {
            "url_length": float(url_length),
            "domain_length": float(domain_length),
            "path_length": float(path_length),
            "num_dots": float(num_dots),
            "num_hyphens": float(num_hyphens),
            "num_at_symbols": float(num_at_symbols),
            "num_query_params": float(num_query_params),
            "has_ip_address": float(has_ip),
            "has_https": float(has_https),
            "tld_is_suspicious": float(tld_suspicious),
            "subdomain_depth": float(subdomain_depth),
            "path_depth": float(path_depth),
            "has_brand_in_subdomain": float(brand_subdomain),
            "lexical_diversity": float(lexical_diversity),
            "digit_ratio": float(digit_ratio),
        }

    except Exception:
        # Malformed URL: return defaults, never raise
        return _default_features()


def features_to_vector(features: dict[str, float]) -> np.ndarray:
    """Convert feature dict to numpy array in correct index order."""
    return np.array([[features[name] for name in FEATURE_NAMES]], dtype=np.float64)
