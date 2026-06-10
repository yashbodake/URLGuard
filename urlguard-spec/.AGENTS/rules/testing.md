# Testing Conventions — URLGuard

## Structure
```
tests/
├── conftest.py                ← TestClient + model load fixture
├── fixtures/
│   └── urls.py                ← known phishing + legitimate URLs with expected values
├── test_extractor.py          ← unit tests for feature extraction
├── test_scorer.py             ← unit tests for model scoring
├── test_predict_route.py      ← integration tests for /predict
├── test_batch_route.py        ← integration tests for /predict/batch
├── test_health.py
└── test_cli.py
```

## URL Fixtures
```python
# tests/fixtures/urls.py
PHISHING_URLS = [
    "http://paypal.verify-account.tk/login",
    "http://192.168.1.1/admin/steal",
    "https://amazon-security-update.xyz/verify?token=abc",
    "http://bankofamerica.phishing-site.ml/login",
    "http://google.account-verify.gq/oauth",
]

LEGITIMATE_URLS = [
    "https://www.google.com/search?q=python",
    "https://github.com/microsoft/vscode",
    "https://docs.python.org/3/library/os.html",
    "https://stackoverflow.com/questions/tagged/python",
    "https://www.amazon.com/dp/B09XYZ",
]

MALFORMED_URLS = [
    "",
    "not-a-url",
    "ftp://wrong-scheme.com",
    "javascript:alert(1)",
]
```

## Feature Extractor Tests
```python
def test_has_ip_address():
    features = extract_features("http://192.168.1.1/login")
    assert features["has_ip_address"] == 1

def test_tld_is_suspicious():
    features = extract_features("https://example.xyz/page")
    assert features["tld_is_suspicious"] == 1

def test_brand_in_subdomain_positive():
    features = extract_features("http://paypal.evil.com/steal")
    assert features["has_brand_in_subdomain"] == 1

def test_brand_in_subdomain_negative():
    # paypal IS the domain — not subdomain abuse
    features = extract_features("https://paypal.com/login")
    assert features["has_brand_in_subdomain"] == 0

def test_malformed_url_returns_defaults():
    features = extract_features("not-a-url-at-all!!!")
    assert isinstance(features, dict)
    assert set(features.keys()) == set(FEATURE_NAMES)
    # No exception raised

def test_feature_vector_shape():
    features = extract_features("https://google.com")
    vector = features_to_vector(features)
    assert vector.shape == (1, 15)
    assert vector.dtype == np.float64
```

## Route Tests
```python
def test_predict_phishing(trained_client):
    resp = trained_client.post("/predict", json={"url": "http://paypal.verify.tk/login"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["label"] == "PHISHING"
    assert data["risk_score"] >= 0.4
    assert len(data["top_features"]) == 5
    assert len(data["features"]) == 15

def test_predict_invalid_url(client):
    resp = client.post("/predict", json={"url": "not-a-url"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "INVALID_URL"

def test_predict_no_model(client_without_model):
    resp = client_without_model.post("/predict", json={"url": "https://google.com"})
    assert resp.status_code == 503
    assert resp.json()["error"] == "MODEL_NOT_LOADED"
```

## Coverage Target
```bash
pytest --cov=app tests/ --cov-report=term-missing
```
Target: > 75% for `app/features/` and `app/model/`
