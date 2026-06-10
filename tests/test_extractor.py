"""Tests for the URL feature extractor — Day 1."""

import numpy as np
import pytest

from app.features.extractor import (
    extract_features,
    features_to_vector,
    has_brand_in_subdomain,
    has_ip_address,
)


def test_has_ip_address_true() -> None:
    """has_ip_address should return 1 for a raw IPv4 address."""
    assert has_ip_address("192.168.1.1") == 1


def test_has_ip_address_false() -> None:
    """has_ip_address should return 0 for a hostname."""
    assert has_ip_address("www.google.com") == 0


def test_has_ip_address_invalid() -> None:
    """has_ip_address should return 0 for invalid IP strings."""
    assert has_ip_address("256.1.1.1") == 0
    assert has_ip_address("192.168.1") == 0
    assert has_ip_address("192.168.1.1.1") == 0


def test_brand_in_subdomain_true() -> None:
    """Brand in subdomain should be 1 when brand is in subdomain but not domain."""
    assert has_brand_in_subdomain("paypal", "verify-account") == 1


def test_brand_in_subdomain_false() -> None:
    """Brand in subdomain should be 0 when brand is in domain."""
    assert has_brand_in_subdomain("www", "paypal") == 0


def test_brand_in_subdomain_no_subdomain() -> None:
    """Brand in subdomain should be 0 when there is no subdomain."""
    assert has_brand_in_subdomain("", "example") == 0


def test_url_length_normal() -> None:
    """URL length should be correct for a known URL."""
    url = "https://www.google.com/search?q=python+tutorial"
    features = extract_features(url)
    assert features["url_length"] == len(url)


def test_tld_is_suspicious_xyz() -> None:
    """tld_is_suspicious should be 1 for .xyz domain."""
    features = extract_features("https://example.xyz/login")
    assert features["tld_is_suspicious"] == 1


def test_tld_is_suspicious_com() -> None:
    """tld_is_suspicious should be 0 for .com domain."""
    features = extract_features("https://www.google.com")
    assert features["tld_is_suspicious"] == 0


def test_tld_is_suspicious_tk() -> None:
    """tld_is_suspicious should be 1 for .tk domain."""
    features = extract_features("http://paypal.verify-account.tk/login")
    assert features["tld_is_suspicious"] == 1


def test_has_brand_in_subdomain_positive() -> None:
    """Brand in subdomain should be detected."""
    features = extract_features("http://paypal.verify-account.tk/login")
    assert features["has_brand_in_subdomain"] == 1


def test_has_brand_in_subdomain_negative() -> None:
    """Brand in domain (not subdomain) should not be flagged."""
    features = extract_features("https://www.paypal.com/signin")
    assert features["has_brand_in_subdomain"] == 0


def test_malformed_url_returns_defaults() -> None:
    """Malformed URL should return default features without raising."""
    features = extract_features("not-a-valid-url")
    assert isinstance(features, dict)
    for key, value in features.items():
        assert value == 0.0


def test_empty_url_returns_defaults() -> None:
    """Empty URL should return default features."""
    features = extract_features("")
    for key, value in features.items():
        assert value == 0.0


def test_none_url_returns_defaults() -> None:
    """None URL should return default features."""
    features = extract_features(None)  # type: ignore[argument-type]
    for key, value in features.items():
        assert value == 0.0


def test_features_to_vector_shape() -> None:
    """features_to_vector should return shape (1, 15) with dtype float64."""
    features = extract_features("https://www.google.com")
    vector = features_to_vector(features)
    assert vector.shape == (1, 15)
    assert vector.dtype == np.float64
