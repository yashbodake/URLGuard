"""URL feature extraction — pure functions, no I/O, no network."""

import logging
import math
import re
from urllib.parse import parse_qs, urlparse

import numpy as np
import tldextract

from .constants import BRAND_NAMES, FEATURE_NAMES, SUSPICIOUS_TLDS, SUSPICIOUS_WORDS

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


def calculate_entropy(string: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not string:
        return 0.0
    # Count frequency of each character
    freq = {}
    for char in string:
        freq[char] = freq.get(char, 0) + 1
    # Calculate entropy
    entropy = 0.0
    length = len(string)
    for count in freq.values():
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)
    return entropy


def extract_features(url: str) -> dict[str, float]:
    """
    Extract numerical features from a URL string.
    Pure function — no network calls, no I/O.
    Returns dict with keys matching FEATURE_NAMES exactly.
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

        brand_subdomain = has_brand_in_subdomain(ext.subdomain, domain)

        lexical_diversity = len(set(url)) / len(url) if url else 0.0

        # NEW FEATURES
        
        # 1. path_entropy: Shannon entropy of path characters
        path_entropy = calculate_entropy(parsed.path)
        
        # 2. path_length_ratio: path length / domain length (capped at 5.0 to avoid extreme values)
        path_length_ratio = min(path_length / max(domain_length, 1), 5.0)
        
        # 3. special_char_count: count of special characters that might indicate obfuscation
        special_chars = set('-_./?&=%')
        special_char_count = sum(1 for c in url if c in special_chars)
        
        # 4. url_suspicious_word_count: count of suspicious words in URL (case-insensitive)
        url_lower = url.lower()
        url_suspicious_word_count = sum(1 for word in SUSPICIOUS_WORDS if word in url_lower)
        
        # 5. path_has_brand: 1 if brand name appears in path but NOT in domain
        path_has_brand_val = 0
        path_lower = parsed.path.lower()
        domain_lower = domain.lower()
        for brand in BRAND_NAMES:
            if brand in path_lower and brand not in domain_lower:
                path_has_brand_val = 1
                break

        # Build feature dict in the order of FEATURE_NAMES
        features = {
            "url_length": float(url_length),
            "domain_length": float(domain_length),
            "num_dots": float(num_dots),
            "num_hyphens": float(num_hyphens),
            "num_at_symbols": float(num_at_symbols),
            "num_query_params": float(num_query_params),
            "has_ip_address": float(has_ip),
            "has_https": float(has_https),
            "tld_is_suspicious": float(tld_suspicious),
            "subdomain_depth": float(subdomain_depth),
            "has_brand_in_subdomain": float(brand_subdomain),
            "lexical_diversity": float(lexical_diversity),
            # New features
            "path_entropy": float(path_entropy),
            "path_length_ratio": float(path_length_ratio),
            "special_char_count": float(special_char_count),
            "url_suspicious_word_count": float(url_suspicious_word_count),
            "path_has_brand": float(path_has_brand_val),
        }
        
        # Ensure we only return features in FEATURE_NAMES
        return {k: features[k] for k in FEATURE_NAMES}

    except Exception:
        # Malformed URL: return defaults, never raise
        return _default_features()


def features_to_vector(features: dict[str, float]) -> np.ndarray:
    """Convert feature dict to numpy array in correct index order."""
    return np.array([[features[name] for name in FEATURE_NAMES]], dtype=np.float64)
