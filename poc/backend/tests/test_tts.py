from pydantic import SecretStr
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def test_elevenlabs_tts_returns_mp3_bytes_when_configured(monkeypatch):
    from app.services.tts import synthesize_elevenlabs

    class FakeResponse:
        content = b"fake-mp3"

        def raise_for_status(self):
            return None

    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(settings, "elevenlabs_api_key", SecretStr("test-key"))
    monkeypatch.setattr(settings, "elevenlabs_voice_id", "voice-123")
    monkeypatch.setattr("app.services.tts.httpx.post", fake_post)

    audio = synthesize_elevenlabs("안녕하세요.")

    assert audio == b"fake-mp3"
    assert captured["url"].endswith("/v1/text-to-speech/voice-123")
    assert captured["headers"]["xi-api-key"] == "test-key"
    assert captured["json"]["text"] == "안녕하세요."
    assert captured["json"]["model_id"] == settings.elevenlabs_model


def test_tts_endpoint_returns_audio_mpeg_when_synthesis_succeeds(monkeypatch):
    monkeypatch.setattr("app.api.tts.synthesize_elevenlabs", lambda _text: b"fake-mp3")

    response = TestClient(app).post("/api/tts", json={"text": "안녕하세요."})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"fake-mp3"


def test_female_tts_returns_iris_wav(monkeypatch):
    monkeypatch.setattr("app.api.tts.synthesize_iris", lambda _text: b"RIFFiris")

    response = TestClient(app).post("/api/tts", json={"text": "안녕하세요.", "voice": "female"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == b"RIFFiris"


def test_male_tts_is_not_ready():
    response = TestClient(app).post("/api/tts", json={"text": "안녕하세요.", "voice": "male"})

    assert response.status_code == 503


def test_iris_synthesis_reads_only_iris_home_wav(monkeypatch, tmp_path):
    from app.services.iris_tts import synthesize_iris
    from app.services.tts import SpeechSynthesisError

    wav = tmp_path / "generated.wav"
    wav.write_bytes(b"wav-bytes")
    outside = tmp_path.parent / "not-iris.wav"
    monkeypatch.setattr("app.services.iris_tts._audio_root", lambda: tmp_path.resolve())

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"audio_path": str(wav)}

    monkeypatch.setattr("app.services.iris_tts.httpx.post", lambda *args, **kwargs: FakeResponse())
    assert synthesize_iris("안녕하세요.") == b"wav-bytes"

    class OutsideResponse(FakeResponse):
        def json(self):
            return {"audio_path": str(outside)}

    monkeypatch.setattr("app.services.iris_tts.httpx.post", lambda *args, **kwargs: OutsideResponse())
    try:
        synthesize_iris("다른 경로.")
    except SpeechSynthesisError:
        return
    raise AssertionError("아이리스 홈 밖의 wav는 읽으면 안 된다")
