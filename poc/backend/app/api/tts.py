from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.schemas import TtsIn
from app.services.iris_tts import synthesize_iris
from app.services.tts import SpeechSynthesisError, synthesize_elevenlabs

router = APIRouter(prefix="/tts", tags=["speech"])

_UNAVAILABLE = "AI 음성을 만들 수 없어요. 브라우저 음성으로 전환합니다."


@router.post("")
def create_speech(body: TtsIn) -> Response:
    """여자 화자는 아이리스 목소리 wav, 그 외 기존 경로는 MP3."""
    if body.voice == "male":
        raise HTTPException(status_code=503, detail=_UNAVAILABLE)
    if body.voice == "female":
        try:
            audio = synthesize_iris(body.text)
        except SpeechSynthesisError as error:
            raise HTTPException(status_code=503, detail=_UNAVAILABLE) from error
        return Response(content=audio, media_type="audio/wav")
    try:
        audio = synthesize_elevenlabs(body.text)
    except SpeechSynthesisError as error:
        raise HTTPException(status_code=503, detail=_UNAVAILABLE) from error
    return Response(content=audio, media_type="audio/mpeg")
