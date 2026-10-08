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
