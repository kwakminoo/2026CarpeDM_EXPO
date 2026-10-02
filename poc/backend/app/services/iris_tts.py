"""여자 TTS — 아이리스 프로젝트의 보이스 런타임을 그대로 호출한다.

합성은 Qwen3-TTS와 커밋된 iris_voice_profile이 맡는다. 여기는 그 결과 wav만 읽는다.
남자 목소리는 아직 없어서 이 모듈을 타지 않는다.
"""

import time
from pathlib import Path

import httpx

from app.core.config import settings
from app.services.tts import SpeechSynthesisError

_CACHE = {"at": 0.0, "ready": False}
_CACHE_SEC = 15.0


def _audio_root() -> Path:
    return (Path.home() / ".iris-light" / "audio").resolve()


def _is_iris_wav(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    return resolved.suffix.lower() == ".wav" and resolved.is_relative_to(_audio_root())


def iris_female_ready() -> bool:
    """실모드 아이리스 런타임만 준비된 것으로 본다. mock은 무음 wav라 제외한다."""
    now = time.monotonic()
    if now - _CACHE["at"] < _CACHE_SEC:
        return bool(_CACHE["ready"])
    ready = False
    try:
        response = httpx.get(
            f"{settings.iris_voice_base_url.rstrip('/')}/health",
            timeout=1.0,
        )
        response.raise_for_status()
        body = response.json()
        ready = body.get("status") == "ok" and not body.get("mock_mode")
    except (httpx.HTTPError, ValueError):
        ready = False
    _CACHE["at"] = now
    _CACHE["ready"] = ready
    return ready


def synthesize_iris(text: str) -> bytes:
    """빈 voice_prompt_hash로 아이리스 프로필(톤 자동) 합성을 요청하고 wav를 읽는다."""
    spoken = text.strip()
    if not spoken:
        raise SpeechSynthesisError("읽을 문장이 없습니다")
    try:
        response = httpx.post(
            f"{settings.iris_voice_base_url.rstrip('/')}/v1/audio/speech",
            json={"text": spoken, "voice_prompt_hash": ""},
            timeout=settings.iris_voice_timeout_sec,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise SpeechSynthesisError("아이리스 음성을 만들지 못했습니다") from error

    audio_path = Path(str(payload.get("audio_path") or ""))
    if not _is_iris_wav(audio_path) or not audio_path.is_file():
        raise SpeechSynthesisError("아이리스 음성 파일을 찾지 못했습니다")
    data = audio_path.read_bytes()
    if not data:
        raise SpeechSynthesisError("아이리스 음성이 비어 있습니다")
    return data
