"""Test URLs with expected feature values for Day 1 development."""

# Feature names in correct order (matching FEATURES.md)
FEATURE_NAMES = [
    "url_length",
    "domain_length",
    "path_length",
    "num_dots",
    "num_hyphens",
    "num_at_symbols",
    "num_query_params",
    "has_ip_address",
    "has_https",
    "tld_is_suspicious",
    "subdomain_depth",
    "path_depth",
    "has_brand_in_subdomain",
    "lexical_diversity",
    "digit_ratio",
]

# URL fixtures with expected feature values (approximate for some floating point features)
URL_FIXTURES = {
    # Normal legitimate URL
    "normal": {
        "url": "https://www.google.com/search?q=python+tutorial",
        "expected": {
            "url_length": 45,
            "domain_length": 11,  # 'google.com'
            "path_length": 6,
            "num_dots": 2,
            "num_hyphens": 0,
            "num_at_symbols": 0,
            "num_query_params": 1,
            "has_ip_address": 0,
            "has_https": 1,
            "tld_is_suspicious": 0,
            "subdomain_depth": 1,  # www
            "path_depth": 1,
            "has_brand_in_subdomain": 0,
        },
    },
    # Phishing URL
    "phishing": {
        "url": "https://paypal-security-update.xyz/verify/account/login?user=admin&token=abc123",
        "expected": {
            "url_length": 79,
            "domain_length": 24,  # 'paypal-security-update'
            "path_length": 27,
            "num_dots": 3,
            "num_hyphens": 2,
            "num_at_symbols": 0,
            "num_query_params": 2,
            "has_ip_address": 0,
            "has_https": 1,
            "tld_is_suspicious": 1,  # .xyz
            "subdomain_depth": 0,
            "path_depth": 3,
            "has_brand_in_subdomain": 0,
        },
    },
    # IP-based URL
    "ip_based": {
        "url": "http://192.168.1.1/login",
        "expected": {
            "url_length": 26,
            "domain_length": 0,
            "path_length": 6,
            "num_dots": 5,
            "num_hyphens": 0,
            "num_at_symbols": 0,
            "num_query_params": 0,
            "has_ip_address": 1,
            "has_https": 0,
            "tld_is_suspicious": 0,
            "subdomain_depth": 0,
            "path_depth": 1,
            "has_brand_in_subdomain": 0,
        },
    },
    # Subdomain brand abuse
    "subdomain_brand": {
        "url": "http://paypal.verify-account.tk/login",
        "expected": {
            "url_length": 37,
            "domain_length": 14,  # 'verify-account'
            "path_length": 6,
            "num_dots": 3,
            "num_hyphens": 1,
            "num_at_symbols": 0,
            "num_query_params": 0,
            "has_ip_address": 0,
            "has_https": 0,
            "tld_is_suspicious": 1,  # .tk
            "subdomain_depth": 1,  # paypal
            "path_depth": 1,
            "has_brand_in_subdomain": 1,  # paypal in subdomain
        },
    },
    # Malformed URL (should return defaults without raising)
    "malformed": {
        "url": "not-a-valid-url",
        "expected": {
            "url_length": 0,
            "domain_length": 0,
            "path_length": 0,
            "num_dots": 0,
            "num_hyphens": 0,
            "num_at_symbols": 0,
            "num_query_params": 0,
            "has_ip_address": 0,
            "has_https": 0,
            "tld_is_suspicious": 0,
            "subdomain_depth": 0,
            "path_depth": 0,
            "has_brand_in_subdomain": 0,
            "lexical_diversity": 0,
            "digit_ratio": 0,
        },
    },
    # Simple legitimate with brand as domain (not subdomain)
    "brand_in_domain": {
        "url": "https://www.paypal.com/signin",
        "expected": {
            "url_length": 29,
            "domain_length": 11,  # paypal.com
            "path_length": 7,
            "num_dots": 2,
            "num_hyphens": 0,
            "num_at_symbols": 0,
            "num_query_params": 0,
            "has_ip_address": 0,
            "has_https": 1,
            "tld_is_suspicious": 0,
            "subdomain_depth": 1,  # www
            "path_depth": 1,
            "has_brand_in_subdomain": 0,  # paypal is in domain, not subdomain
        },
    },
}
