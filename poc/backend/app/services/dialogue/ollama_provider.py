"""로컬 Ollama 대화. 직장 대사는 Gemma 4 26B를 쓴다."""
import logging

import httpx

from app.core.config import settings
from app.services.dialogue.gemini_provider import GeminiDialogueProvider
from app.services.dialogue.openai_provider import DialogueGenerationError

logger = logging.getLogger(__name__)

# 하루 JSON이 3막까지 끝나도록 출력 한도를 둔다. 한 줄 대사는 짧게 자른다.
_LINE_PREDICT = 180
_PLAN_PREDICT = 2048
_LINE_TIMEOUT_SEC = 90.0
_PLAN_TIMEOUT_SEC = 180.0


class OllamaDialogueProvider(GeminiDialogueProvider):
    """Gemini와 같은 직장대화 흐름을 로컬 /api/chat으로 수행한다."""

    def _complete(self, system: str, user: str, *, max_tokens: int, temperature: float, json_mode: bool = False) -> str:
        predict = min(max_tokens, _PLAN_PREDICT if json_mode else _LINE_PREDICT)
        timeout = _PLAN_TIMEOUT_SEC if json_mode else _LINE_TIMEOUT_SEC
        body = {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "think": False,
            "keep_alive": settings.ollama_keep_alive,
            "options": {
                "temperature": temperature,
                "num_predict": predict,
                "num_ctx": 4096,
            },
        }
        if json_mode:
            body["format"] = "json"
        try:
            response = httpx.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json=body,
                timeout=timeout,
            )
            if response.status_code >= 400:
                logger.warning("Ollama HTTP %s: %s", response.status_code, (response.text or "")[:240])
                raise DialogueGenerationError(f"Ollama HTTP {response.status_code}")
            content = ((response.json().get("message") or {}).get("content") or "").strip()
        except DialogueGenerationError:
            raise
        except (httpx.HTTPError, TypeError, ValueError) as error:
            logger.warning("Ollama 호출 실패: %s", error)
            raise DialogueGenerationError("Ollama 역할극 응답을 만들지 못했습니다") from error
        if not content:
            raise DialogueGenerationError("Ollama 응답이 비어 있습니다")
        return content
