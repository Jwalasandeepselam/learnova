"""Offline assertions for the production Supabase boundary and migration."""
from pathlib import Path

from backend.app.learning import service


def test_supabase_token_validation_returns_only_verified_identity(monkeypatch):
    class User:
        id = 'f6b4c9e0-2901-4df4-b7d9-8ea3181f0033'
        email = 'learner@example.test'
    class Auth:
        def get_user(self, token):
            assert token == 'access-token'
            return type('Result', (), {'user': User()})()
    class Client:
        auth = Auth()
    monkeypatch.setattr(service.settings, 'SUPABASE_URL', 'https://project.supabase.co')
    monkeypatch.setattr(service.settings, 'SUPABASE_PUBLISHABLE_KEY', 'sb_publishable_test')
    monkeypatch.setattr(service, 'create_client', lambda *_: Client())
    assert service.authenticate_bearer('access-token') == {'id': User.id, 'email': User.email}


def test_production_migration_has_private_storage_rls_and_no_privileged_rpc():
    migration = next((Path(__file__).parents[2] / 'supabase' / 'migrations').glob('*_learnova_production_schema.sql')).read_text(encoding='utf-8').lower()
    for table in ('profiles', 'sessions', 'files', 'chunks', 'embeddings', 'concepts', 'conversations', 'messages', 'quizzes', 'questions', 'attempts', 'mastery_records', 'voice_sessions'):
        assert f'alter table public.{table} enable row level security' in migration
    assert "'learning-materials', 'learning-materials', false" in migration
    assert 'storage.foldername(name)' in migration
    assert 'security invoker' in migration
    assert 'security definer' not in migration
    assert 'match_chunks' in migration and 'auth.uid()' in migration
