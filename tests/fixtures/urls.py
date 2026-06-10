"""Test URLs with expected feature values for URLGuard."""

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

PHISHING_URLS = [
    "http://paypal.verify-account.tk/login",
    "https://secure-login.xyz/verify/account",
    "http://free-prize.ml/claim/now",
    "https://account-update-paypal.cf/signin",
    "http://amazon-discount.top/offers/checkout",
    "https://netflix-renewal.cc/billing/update",
    "http://bankofamerica-alert.ga/verify",
    "https://instagram-followers.click/login",
    "http://wellsfargo-secure.top/account",
    "https://dropbox-share.gq/document",
]

LEGITIMATE_URLS = [
    "https://www.google.com/search?q=python+tutorial",
    "https://github.com/yashbodake/URLGuard",
    "https://stackoverflow.com/questions/tagged/python",
    "https://www.python.org/downloads/",
    "https://docs.pydantic.dev/latest/",
    "https://fastapi.tiangolo.com/tutorial/",
    "https://pypi.org/project/typer/",
    "https://www.amazon.com/dp/product-example",
    "https://en.wikipedia.org/wiki/Phishing",
    "https://www.realpython.com/python-logging/",
]
