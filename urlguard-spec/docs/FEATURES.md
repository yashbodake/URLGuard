# Feature Definitions — URLGuard

> **AGENT INSTRUCTION**: This is the contract between the feature extractor and the model.
> Feature names (snake_case strings) and index order are FIXED.
> Never add, remove, or rename a feature without updating this file AND retraining.
> Feature extraction must be PURE — no network calls, no I/O.

---

## Reference URL for Examples
```
https://paypal-security-update.xyz/verify/account/login?user=admin&token=abc123#section
```
- scheme: https
- subdomain: (none)
- domain: paypal-security-update
- suffix (TLD): xyz
- path: /verify/account/login
- query: user=admin&token=abc123
- fragment: section

---

## The 15 Features

| Index | Name | Type | Description | Phishing signal |
|---|---|---|---|---|
| 0 | `url_length` | int | Total character length of the full URL | Long URLs hide true destination |
| 1 | `domain_length` | int | Length of the registered domain only | Long domains are suspicious |
| 2 | `path_length` | int | Length of the URL path component | Very deep paths are unusual |
| 3 | `num_dots` | int | Count of `.` in the full URL | `a.b.c.d.evil.com` — many dots = subdomain abuse |
| 4 | `num_hyphens` | int | Count of `-` in the full URL | `paypal-security-update` — hyphens in domain = phishing signal |
| 5 | `num_at_symbols` | int | Count of `@` in URL | `user@evil.com@legitimate.com` — `@` tricks parsers |
| 6 | `num_query_params` | int | Number of `&`-separated query parameters | Many params = tracking / obfuscation |
| 7 | `has_ip_address` | int | 1 if domain is raw IPv4 (e.g. `192.168.1.1`), else 0 | IP instead of domain = evasion |
| 8 | `has_https` | int | 1 if scheme is `https`, else 0 | Absence of HTTPS is weak but useful signal |
| 9 | `tld_is_suspicious` | int | 1 if TLD is in suspicious list (`.xyz`, `.tk`, `.ml`, `.ga`, `.cf`, `.gq`, `.top`, `.pw`, `.cc`, `.info`), else 0 | Cheap/free TLDs heavily abused |
| 10 | `subdomain_depth` | int | Number of subdomain levels (dots before registered domain) | `a.b.c.paypal.com` = 3 subdomains |
| 11 | `path_depth` | int | Number of `/` segments in path | Deep paths like `/a/b/c/d/e` are unusual |
| 12 | `has_brand_in_subdomain` | int | 1 if a known brand name appears in the subdomain but NOT in the registered domain | `paypal.evil.com` — brand in subdomain = phishing |
| 13 | `lexical_diversity` | float | Ratio of unique chars to total URL length | Low diversity = repetitive/generated URLs |
| 14 | `digit_ratio` | float | Ratio of digit characters to total URL length | High digit ratio = randomly generated domain |

---

## Suspicious TLD List
```python
SUSPICIOUS_TLDS = {
    "xyz", "tk", "ml", "ga", "cf", "gq", "top", "pw",
    "cc", "info", "click", "link", "online", "site",
    "website", "space", "live", "stream", "download"
}
```

## Brand Name List (for feature 12)
```python
BRAND_NAMES = {
    "paypal", "google", "facebook", "amazon", "apple", "microsoft",
    "netflix", "instagram", "twitter", "linkedin", "dropbox", "chase",
    "wellsfargo", "bankofamerica", "citibank", "hdfc", "sbi", "icici",
    "paytm", "phonepe", "razorpay"
}
```
This list can be extended. Keep all lowercase.

---

## Feature Extraction Code Contract

```python
import tldextract
import re
from urllib.parse import urlparse, parse_qs

def extract_features(url: str) -> dict[str, float]:
    """
    Extract 15 numerical features from a URL string.
    Pure function — no network calls, no I/O.
    Returns dict with keys matching FEATURES.md exactly.
    On any parse error, returns default feature dict (all zeros/defaults).
    """
    ...
    return {
        "url_length": ...,
        "domain_length": ...,
        "path_length": ...,
        "num_dots": ...,
        "num_hyphens": ...,
        "num_at_symbols": ...,
        "num_query_params": ...,
        "has_ip_address": ...,
        "has_https": ...,
        "tld_is_suspicious": ...,
        "subdomain_depth": ...,
        "path_depth": ...,
        "has_brand_in_subdomain": ...,
        "lexical_diversity": ...,
        "digit_ratio": ...,
    }
```

## Feature Vector for Model
```python
FEATURE_NAMES = [
    "url_length", "domain_length", "path_length", "num_dots",
    "num_hyphens", "num_at_symbols", "num_query_params",
    "has_ip_address", "has_https", "tld_is_suspicious",
    "subdomain_depth", "path_depth", "has_brand_in_subdomain",
    "lexical_diversity", "digit_ratio"
]

def features_to_vector(features: dict[str, float]) -> np.ndarray:
    """Convert feature dict to numpy array in correct index order."""
    return np.array([[features[name] for name in FEATURE_NAMES]], dtype=np.float64)
```

---

## Worked Examples

### Example 1 — Phishing URL
```
https://paypal-security-update.xyz/verify/account/login?user=admin&token=abc123
```
| Feature | Value | Why notable |
|---|---|---|
| url_length | 79 | Long |
| domain_length | 24 | Very long — `paypal-security-update` |
| num_hyphens | 2 | Two hyphens in domain |
| tld_is_suspicious | 1 | `.xyz` is in suspicious list |
| has_brand_in_subdomain | 0 | Brand is in domain, not subdomain |
| num_query_params | 2 | Multiple params |
| lexical_diversity | 0.51 | Moderate |

### Example 2 — Legitimate URL
```
https://www.google.com/search?q=python+tutorial
```
| Feature | Value | Why notable |
|---|---|---|
| url_length | 45 | Short |
| domain_length | 6 | Short — `google` |
| num_hyphens | 0 | No hyphens |
| tld_is_suspicious | 0 | `.com` is not suspicious |
| subdomain_depth | 1 | Just `www` |
| has_https | 1 | Secure |

### Example 3 — Subdomain brand abuse
```
http://paypal.verify-account.tk/login
```
| Feature | Value | Why notable |
|---|---|---|
| has_https | 0 | No HTTPS |
| tld_is_suspicious | 1 | `.tk` |
| has_brand_in_subdomain | 1 | `paypal` appears as subdomain but domain is `verify-account` |
| num_hyphens | 1 | |

---

## Implementation Notes

### IP detection
```python
import re
IP_PATTERN = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')

def has_ip_address(hostname: str) -> int:
    return int(bool(IP_PATTERN.match(hostname)))
```

### tldextract usage
```python
import tldextract

ext = tldextract.extract("https://paypal.verify-account.tk/login")
# ext.subdomain = "paypal"
# ext.domain = "verify-account"
# ext.suffix = "tk"
# registered_domain = ext.registered_domain  → "verify-account.tk"
```

### Brand in subdomain check
```python
def has_brand_in_subdomain(subdomain: str, domain: str) -> int:
    subdomain_lower = subdomain.lower()
    domain_lower = domain.lower()
    for brand in BRAND_NAMES:
        if brand in subdomain_lower and brand not in domain_lower:
            return 1
    return 0
```

### Lexical diversity
```python
def lexical_diversity(url: str) -> float:
    if len(url) == 0:
        return 0.0
    return len(set(url)) / len(url)
```
