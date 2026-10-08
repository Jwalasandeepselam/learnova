"""Offline contract tests for the source-only authenticated learning journey."""
import asyncio

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.learning import service


async def source_model(instruction, context):
    """A provider double: it only returns IDs and facts handed to it as sources."""
    sources = context.get("sources", [])
    source_id = sources[0]["id"]
    if "Extract the important concepts" in instruction:
        return {"concepts": [{
            "title": "Vector addition", "summary": "Components are added by dimension.",
            "source_ids": [source_id], "prerequisites": [], "prerequisite_basis": "explicit",
            "definitions": [], "formulas": [], "examples": [], "section": "Vectors", "importance": "foundational",
        }]}
    if "Create one novel question" in instruction:
        return {
            "prompt": "How are vector components combined?", "type": "multiple_choice",
            "options": ["By adding matching components", "By deleting a dimension"],
            "answer": "By adding matching components", "explanation": "Matching components are added.",
            "source_ids": [source_id],
        }
    if "Respond as a patient tutor" in instruction:
        return {"message": "Matching components are added. What happens in each dimension?", "source_ids": [source_id], "strategy": "simple"}
    raise AssertionError("Unexpected provider instruction")


def register(client, email):
    result = client.post("/api/v2/auth/register", json={"email": email, "password": "Learning-password-123"})
    assert result.status_code == 201


def test_uploaded_material_drives_learning_and_isolated_ownership(monkeypatch, tmp_path):
    db_path = tmp_path / "learning.db"
    monkeypatch.setattr(service.settings, "LEARNING_DB_PATH", str(db_path))
    monkeypatch.setattr(service, "generate_json", source_model)
    monkeypatch.setattr(service, "embed_texts", lambda values: asyncio.sleep(0, result=[]))
    with TestClient(app) as first, TestClient(app) as second:
        register(first, "first@example.test")
        session = first.post("/api/v2/sessions", json={"title": "My vector notes"}).json()
        session_id = session["id"]
        upload = first.post(
            f"/api/v2/sessions/{session_id}/files",
            files=[("files", ("vectors.txt", b"Vector addition adds corresponding components in every dimension.", "text/plain"))],
        )
        assert upload.status_code == 200
        detail = first.get(f"/api/v2/sessions/{session_id}").json()
        assert detail["status"] == "READY"
        assert detail["concepts"][0]["title"] == "Vector addition"
        assert detail["files"][0]["name"] == "vectors.txt"

        register(second, "second@example.test")
        assert second.get(f"/api/v2/sessions/{session_id}").status_code == 404

        answer = first.post(f"/api/v2/sessions/{session_id}/chat", json={"message": "Explain vector addition"})
        assert answer.status_code == 200
        assert answer.json()["citations"][0]["filename"] == "vectors.txt"

        # Answer keys are never present in the question payload and each question
        # can only influence mastery once.
        question = first.post(f"/api/v2/sessions/{session_id}/quiz", json={}).json()
        assert "answer" not in question
        scored = first.post(f"/api/v2/sessions/{session_id}/answers", json={"question_id": question["id"], "answer": "By adding matching components"})
        assert scored.status_code == 200 and scored.json()["correct"] is True
        assert first.post(f"/api/v2/sessions/{session_id}/answers", json={"question_id": question["id"], "answer": "By adding matching components"}).status_code == 409

        # Final assessment is finite: four cognitive levels per concept.
        for index in range(4):
            final = first.post(f"/api/v2/sessions/{session_id}/quiz", json={"final": True})
            assert final.status_code == 200
            payload = final.json()
            assert payload["assessment_position"] == index + 1
            assert payload["assessment_length"] == 4
            assert first.post(f"/api/v2/sessions/{session_id}/answers", json={"question_id": payload["id"], "answer": "By adding matching components"}).status_code == 200
        assert first.post(f"/api/v2/sessions/{session_id}/quiz", json={"final": True}).status_code == 409
        report = first.get(f"/api/v2/sessions/{session_id}/report").json()
        assert report["final_assessment"]["complete"] is True
        assert report["final_assessment"]["target"] == 4


def test_analysis_never_marks_failed_source_as_ready(monkeypatch, tmp_path):
    monkeypatch.setattr(service.settings, "LEARNING_DB_PATH", str(tmp_path / "learning.db"))
    with TestClient(app) as client:
        register(client, "failed@example.test")
        session_id = client.post("/api/v2/sessions", json={"title": "Unreadable"}).json()["id"]
        failed = client.post(f"/api/v2/sessions/{session_id}/files", files=[("files", ("program.exe", b"binary", "application/octet-stream"))])
        assert failed.status_code == 200
        detail = client.get(f"/api/v2/sessions/{session_id}").json()
        assert detail["status"] == "ERROR"
        assert detail["concepts"] == []
        assert "Unsupported file" in detail["files"][0]["error"]
