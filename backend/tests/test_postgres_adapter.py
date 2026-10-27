from backend.app.learning import router, service


class RawCursor:
    def __init__(self, rows=()): self.rows = list(rows)
    def fetchone(self): return self.rows[0] if self.rows else None
    def fetchall(self): return list(self.rows)


class RawConnection:
    def __init__(self): self.sessions = {}
    def execute(self, query, params=()):
        if query.startswith('INSERT INTO sessions'):
            self.sessions[params[0]] = {'id': params[0], 'user_id': params[1], 'title': params[2], 'status': 'EMPTY', 'error': None, 'created_at': params[3], 'revision': 0}
            return RawCursor()
        if 'SELECT id FROM sessions' in query:
            return RawCursor([{'id': row['id']} for row in self.sessions.values() if row['user_id'] == params[0]])
        if 'SELECT * FROM sessions' in query:
            row = self.sessions.get(params[0])
            return RawCursor([row] if row and row['user_id'] == params[1] else [])
        return RawCursor()
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass


def test_postgres_adapter_supports_session_creation_listing_and_detail(monkeypatch):
    raw = RawConnection()
    monkeypatch.setattr(service.settings, 'SUPABASE_DATABASE_URL', 'postgresql://contract')
    monkeypatch.setattr(service, 'psycopg', type('Psycopg', (), {'connect': staticmethod(lambda *_args, **_kwargs: raw)}))
    monkeypatch.setattr(service, 'dict_row', object())
    created = router.new_session(router.SessionInput(title='Adapter contract'), {'id': 'owner', 'email': 'owner@example.test'})
    listed = router.sessions({'id': 'owner', 'email': 'owner@example.test'})
    detail = router.session(created['id'], {'id': 'owner', 'email': 'owner@example.test'})
    assert [entry['id'] for entry in listed] == [created['id']]
    assert detail['title'] == 'Adapter contract'


def test_postgres_cursor_is_iterable():
    cursor = service.PostgresCursor(RawCursor([{'id': 'one'}]))
    assert [row['id'] for row in cursor] == ['one']
