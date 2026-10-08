import base64
import pytest

try:
    from backend.app.voice.protocol import OutputGate, decode_audio
except ImportError:
    from app.voice.protocol import OutputGate, decode_audio


def test_pcm_frame_validation():
    assert decode_audio(base64.b64encode(b'\0\0\1\0').decode()) == b'\0\0\1\0'
    for invalid in ('!', '', 'YQ==', 'A' * 44001, None):
        with pytest.raises(ValueError):
            decode_audio(invalid)


def test_interrupt_after_provider_finishes_does_not_poison_next_turn():
    gate = OutputGate()
    gate.retrieved(True)
    gate.finish()
    gate.interrupt()  # Browser is still playing buffered audio from the completed turn.
    assert not gate.interrupted
    assert not gate.allows_audio
    gate.retrieved(True)
    assert gate.allows_audio


def test_interruption_blocks_stale_output_and_requires_new_evidence():
    gate = OutputGate()
    assert not gate.allows_audio
    gate.retrieved(True)
    assert gate.allows_audio
    gate.interrupt()
    assert not gate.allows_audio
    gate.retrieved(True)  # A late tool response cannot revive the cancelled turn.
    assert not gate.allows_audio
    gate.finish()
    assert not gate.allows_audio
    gate.retrieved(False)
    assert not gate.allows_audio
    gate.retrieved(True)
    assert gate.allows_audio


def test_socket_rejects_untrusted_origin_before_auth(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect
    import importlib
    module = importlib.import_module(OutputGate.__module__.rsplit('.', 1)[0] + '.router')
    app = FastAPI()
    app.include_router(module.router)
    monkeypatch.setattr(module.service, 'authenticate_cookie', lambda _: pytest.fail('Untrusted origin reached authentication'))
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect('/api/v2/sessions/unknown/voice', headers={'origin': 'https://attacker.example'}):
                pass
    assert exc.value.code == 1008


def test_socket_rejects_missing_login(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect
    import importlib
    module = importlib.import_module(OutputGate.__module__.rsplit('.', 1)[0] + '.router')
    app = FastAPI()
    app.include_router(module.router)
    monkeypatch.setattr(module.service, 'authenticate_cookie', lambda _: None)
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect('/api/v2/sessions/unknown/voice', headers={'origin': module.settings.CORS_ORIGINS[0]}):
                pass
    assert exc.value.code == 1008


def test_socket_rejects_other_users_session(monkeypatch):
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect
    import importlib
    module = importlib.import_module(OutputGate.__module__.rsplit('.', 1)[0] + '.router')
    app = FastAPI()
    app.include_router(module.router)
    monkeypatch.setattr(module.service, 'authenticate_cookie', lambda _: {'id': 'owner-a'})
    def reject(session_id, user_id):
        assert user_id == 'owner-a'
        raise HTTPException(404)
    monkeypatch.setattr(module.service, 'session_detail', reject)
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect('/api/v2/sessions/owner-b-session/voice', headers={'origin': module.settings.CORS_ORIGINS[0]}):
                pass
    assert exc.value.code == 1008


def test_relay_does_not_forward_ungrounded_audio(monkeypatch):
    import asyncio
    import importlib
    from types import SimpleNamespace as NS
    module = importlib.import_module(OutputGate.__module__.rsplit('.', 1)[0] + '.router')
    messages = []
    class Socket:
        async def receive_text(self):
            await asyncio.Event().wait()
        async def send_json(self, value):
            messages.append(value)
        async def close(self):
            pass
    class Provider:
        async def receive(self):
            content = NS(interrupted=False, input_transcription=None,
                         output_transcription=NS(text='An invented fact'),
                         model_turn=NS(parts=[NS(inline_data=NS(data=b'\0\0'))]), turn_complete=True)
            yield NS(tool_call=None, server_content=content)
    monkeypatch.setattr(module.service, 'add_message', lambda *args: pytest.fail('Ungrounded transcript persisted'))
    asyncio.run(module.relay(Socket(), Provider(), 'session', 'owner', NS()))
    assert not any(message['type'] == 'audio' for message in messages)
    assert any(message['type'] == 'error' for message in messages)
