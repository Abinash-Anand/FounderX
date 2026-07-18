from typing import Any

from supabase import Client, create_client

from app.core.errors import IntegrationNotConfigured
from app.core.settings import Settings, get_settings
from app.domain.founders import Founder, FounderCreate
from app.domain.memos import Memo, MemoCreate
from app.domain.signals import Signal, SignalCreate


class SupabaseGateway:
    """Database, authentication, and private storage behind one small interface."""

    def __init__(self, client: Client):
        self._client = client

    def get_user(self, access_token: str) -> Any:
        return self._client.auth.get_user(access_token).user

    def create_founder(self, founder: FounderCreate) -> Founder:
        response = self._client.table("founders").insert(founder.model_dump(mode="json")).execute()
        return Founder.model_validate(response.data[0])

    def create_memo(self, memo: MemoCreate) -> Memo:
        response = self._client.table("memos").insert(memo.model_dump(mode="json")).execute()
        return Memo.model_validate(response.data[0])

    def create_signal(self, signal: SignalCreate) -> Signal:
        response = self._client.table("signals").insert(signal.model_dump(mode="json")).execute()
        return Signal.model_validate(response.data[0])

    def upload_private_file(
        self,
        *,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str,
    ) -> str:
        self._client.storage.from_(bucket).upload(
            path,
            content,
            {"content-type": content_type, "upsert": "true"},
        )
        return path


def build_supabase_gateway(settings: Settings | None = None) -> SupabaseGateway:
    settings = settings or get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise IntegrationNotConfigured(
            "Supabase requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )
    client = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key.get_secret_value(),
    )
    return SupabaseGateway(client)

