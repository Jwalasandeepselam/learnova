"""Application boundary tests: old demo endpoints cannot bypass v2 ownership."""
from fastapi.testclient import TestClient
from backend.app.main import app


def test_demo_endpoints_are_not_exposed():
    with TestClient(app) as client:
        for path in ("/api/documents", "/api/student/progress", "/api/student/mastery"):
            assert client.get(path).status_code == 404


def test_cross_origin_mutations_rejected_before_auth():
    with TestClient(app) as client:
        response = client.post("/api/v2/sessions", json={"title": "Denied"}, headers={"Origin": "https://untrusted.invalid"})
        assert response.status_code == 403


def test_health_and_security_headers():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_login_rate_limit_is_enforced(monkeypatch):
    from backend.app import main
    main.rate_buckets.clear()
    with TestClient(app) as client:
        for _ in range(10):
            client.post('/api/v2/auth/login', json={'email': 'limit@example.com', 'password': 'not-a-password'})
        response = client.post('/api/v2/auth/login', json={'email': 'limit@example.com', 'password': 'not-a-password'})
    assert response.status_code == 429
    assert response.headers['Retry-After'] == '60'
