import asyncio

from elevenlabs.client import ElevenLabs

from app.core.errors import IntegrationNotConfigured
from app.core.settings import Settings, get_settings
from app.integrations.mongodb import MongoDBGateway, build_mongodb_gateway


class MemoNarrator:
    """Turns a memo into audio and persists it without exposing SDK details."""

    def __init__(
        self,
        *,
        elevenlabs: ElevenLabs,
        storage: MongoDBGateway,
        voice_id: str,
        model_id: str,
        bucket: str,
    ):
        self._elevenlabs = elevenlabs
        self._storage = storage
        self._voice_id = voice_id
        self._model_id = model_id
        self._bucket = bucket

    async def narrate_and_store(self, memo_id: str, text: str) -> str:
        audio = await asyncio.to_thread(self._render_audio, text)
        path = f"{memo_id}/investment-memo.mp3"
        return await asyncio.to_thread(
            self._storage.upload_private_file,
            bucket=self._bucket,
            path=path,
            content=audio,
            content_type="audio/mpeg",
        )

    def _render_audio(self, text: str) -> bytes:
        audio_chunks = self._elevenlabs.text_to_speech.convert(
            voice_id=self._voice_id,
            model_id=self._model_id,
            output_format="mp3_44100_128",
            text=text,
        )
        return b"".join(audio_chunks)


def build_memo_narrator(settings: Settings | None = None) -> MemoNarrator:
    settings = settings or get_settings()
    if not settings.elevenlabs_api_key or not settings.elevenlabs_voice_id:
        raise IntegrationNotConfigured(
            "Memo narration requires ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID."
        )
    return MemoNarrator(
        elevenlabs=ElevenLabs(api_key=settings.elevenlabs_api_key.get_secret_value()),
        storage=build_mongodb_gateway(settings),
        voice_id=settings.elevenlabs_voice_id,
        model_id=settings.elevenlabs_model_id,
        bucket=settings.mongodb_memo_audio_bucket,
    )
