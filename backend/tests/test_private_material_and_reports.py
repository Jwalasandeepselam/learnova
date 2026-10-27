from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.learning import service


def register(client, email):
    assert client.post('/api/v2/auth/register', json={'email': email, 'password': 'Learning-password-123'}).status_code == 201


def test_tampered_storage_path_cannot_be_signed_or_deleted(monkeypatch, tmp_path):
    monkeypatch.setattr(service.settings, 'LEARNING_DB_PATH', str(tmp_path / 'learning.db'))
    signed, deleted = [], []
    monkeypatch.setattr(service, 'store_private_material', lambda user, session, file_id, name, *_: f'{user}/{session}/{file_id}/{name}')
    monkeypatch.setattr(service, 'signed_private_url', lambda path: signed.append(path) or 'https://signed.test/material')
    monkeypatch.setattr(service, 'delete_private_material', lambda path: deleted.append(path))
    with TestClient(app) as owner, TestClient(app) as other:
        register(owner, 'owner@example.test')
        session = owner.post('/api/v2/sessions', json={'title': 'Private material'}).json()['id']
        uploaded = owner.post(f'/api/v2/sessions/{session}/files', files=[('files', ('notes.txt', b'private notes', 'text/plain'))]).json()
        file_id = uploaded['files'][0]['id']
        with service.database() as db:
            db.execute('UPDATE files SET storage_path=? WHERE id=?', (f'other-user/{session}/{file_id}/notes.txt', file_id))
        assert owner.get(f'/api/v2/sessions/{session}/files/{file_id}/signed-url').status_code == 409
        assert owner.delete(f'/api/v2/sessions/{session}/files/{file_id}').status_code == 409
        assert signed == [] and deleted == []
        # Validation precedes the database delete so bad metadata cannot erase
        # a legitimate file record while it is being repaired.
        remaining = owner.get(f'/api/v2/sessions/{session}').json()['files']
        assert [file['id'] for file in remaining] == [file_id]
        register(other, 'other@example.test')
        assert other.get(f'/api/v2/sessions/{session}/files/{file_id}/signed-url').status_code == 404


def test_report_pdf_requires_the_session_owner(monkeypatch, tmp_path):
    monkeypatch.setattr(service.settings, 'LEARNING_DB_PATH', str(tmp_path / 'learning.db'))
    with TestClient(app) as owner, TestClient(app) as other, TestClient(app) as anonymous:
        register(owner, 'report-owner@example.test')
        session = owner.post('/api/v2/sessions', json={'title': 'Report'}).json()['id']
        response = owner.get(f'/api/v2/sessions/{session}/report.pdf')
        assert response.status_code == 200 and response.headers['content-type'].startswith('application/pdf')
        register(other, 'report-other@example.test')
        assert other.get(f'/api/v2/sessions/{session}/report.pdf').status_code == 404
        assert anonymous.get(f'/api/v2/sessions/{session}/report.pdf').status_code == 401
