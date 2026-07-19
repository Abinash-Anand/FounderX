from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from gridfs import GridFSBucket
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.core.errors import IntegrationNotConfigured
from app.core.settings import Settings, get_settings
from app.domain.founders import Founder, FounderCreate
from app.domain.investment_memos import InvestmentMemoArtifact
from app.domain.memos import Memo, MemoCreate
from app.domain.signals import Signal, SignalCreate
from app.intelligence.evidence_intelligence import EvidenceIntelligence
from app.intelligence.investment_intelligence import InvestmentIntelligence
from app.intelligence.profile_models import FounderIntelligence, FounderProfile, Layer1Input


class ResearchRunRecord:
    """Immutable raw research run document stored for downstream layers."""

    def __init__(self, research_run_id: str, raw_payload: Layer1Input, metadata: dict[str, Any]):
        self.researchRunId = research_run_id
        self.payload = raw_payload.model_dump(mode="json")
        self.rawResponses = []
        self.metadata = metadata
        self.immutable = True
        self.createdAt = datetime.now(UTC).isoformat()


class FounderProfileRecord:
    """Persisted FounderProfile envelope returned to downstream layers."""

    def __init__(
        self,
        founder_id: str,
        research_run_id: str,
        profile: FounderProfile,
        version: int,
        created_at: str,
        updated_at: str,
    ):
        self.founderId = founder_id
        self.researchRunId = research_run_id
        self.profile = profile
        self.version = version
        self.createdAt = created_at
        self.updatedAt = updated_at


class EvidenceIntelligenceRecord:
    """Metadata returned after enriching a persisted founder profile."""

    def __init__(
        self,
        founder_id: str,
        version: int,
        created_at: str,
        updated_at: str,
        audit_metadata: list[dict[str, Any]],
    ):
        self.founderId = founder_id
        self.version = version
        self.createdAt = created_at
        self.updatedAt = updated_at
        self.auditMetadata = audit_metadata


class FounderIntelligenceRecord:
    """Metadata returned after storing Layer 3 founder intelligence."""

    def __init__(
        self,
        founder_id: str,
        version: int,
        created_at: str,
        updated_at: str,
    ):
        self.founderId = founder_id
        self.version = version
        self.createdAt = created_at
        self.updatedAt = updated_at


class InvestmentIntelligenceRecord:
    """Metadata returned after storing a Layer 4 investment assessment."""

    def __init__(
        self,
        founder_id: str,
        version: int,
        created_at: str,
        updated_at: str,
    ):
        self.founderId = founder_id
        self.version = version
        self.createdAt = created_at
        self.updatedAt = updated_at


class InvestmentMemoArtifactRecord:
    """Identity and version metadata for an immutable final memo artifact."""

    def __init__(
        self,
        memo_id: str,
        founder_id: str,
        version: int,
        generated_at: str,
    ):
        self.memoId = memo_id
        self.founderId = founder_id
        self.version = version
        self.generatedAt = generated_at


class InMemoryCollection:
    """Simple in-memory collection used as a fallback when Atlas is unreachable."""

    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def insert_one(self, document: dict[str, Any]) -> SimpleNamespace:
        self.documents.append(document)
        return SimpleNamespace(inserted_id=str(len(self.documents)))

    def find_one(self, filter: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents:
            if all(self._get_value(document, key) == value for key, value in filter.items()):
                return document
        return None

    def find(self, filter: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            document
            for document in self.documents
            if all(self._get_value(document, key) == value for key, value in filter.items())
        ]

    def update_one(self, filter: dict[str, Any], update: dict[str, Any]) -> SimpleNamespace:
        for document in self.documents:
            if all(self._get_value(document, key) == value for key, value in filter.items()):
                document.update(update.get("$set", {}))
                return SimpleNamespace(matched_count=1, modified_count=1)
        return SimpleNamespace(matched_count=0, modified_count=0)

    @staticmethod
    def _get_value(document: dict[str, Any], path: str) -> Any:
        value: Any = document
        for key in path.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(key)
        return value


class InMemoryDatabase:
    def __init__(self) -> None:
        self.collections: dict[str, InMemoryCollection] = {}

    def __getitem__(self, name: str) -> InMemoryCollection:
        return self.collections.setdefault(name, InMemoryCollection())


class InMemoryMongoClient:
    def __init__(self, database_name: str) -> None:
        self._database_name = database_name
        self._database = InMemoryDatabase()

    def __getitem__(self, name: str) -> InMemoryDatabase:
        if name != self._database_name:
            raise KeyError(name)
        return self._database


class MongoDBGateway:
    """MongoDB Atlas-backed persistence behind the existing small interface."""

    def __init__(self, client: MongoClient, database_name: str):
        self._client = client
        self._database_name = database_name

    @property
    def _database(self):
        return self._client[self._database_name]

    def _collection(self, name: str) -> Collection:
        return self._database[name]

    def get_user(self, access_token: str) -> Any:
        raise NotImplementedError("Atlas auth is not implemented in this backend slice")

    def create_founder(self, founder: FounderCreate) -> Founder:
        document = founder.model_dump(mode="json")
        document.setdefault("id", str(uuid4()))
        now = datetime.now(UTC)
        document.setdefault("created_at", now)
        document.setdefault("updated_at", now)
        self._collection("founders").insert_one(document)
        return Founder.model_validate(document)

    def create_memo(self, memo: MemoCreate) -> Memo:
        document = memo.model_dump(mode="json")
        document.setdefault("id", str(uuid4()))
        now = datetime.now(UTC)
        document.setdefault("created_at", now)
        document.setdefault("updated_at", now)
        self._collection("memos").insert_one(document)
        return Memo.model_validate(document)

    def create_signal(self, signal: SignalCreate) -> Signal:
        document = signal.model_dump(mode="json")
        document.setdefault("id", str(uuid4()))
        now = datetime.now(UTC)
        document.setdefault("created_at", now)
        self._collection("signals").insert_one(document)
        return Signal.model_validate(document)

    def create_research_run(
        self, payload: Layer1Input, metadata: dict[str, Any]
    ) -> ResearchRunRecord:
        research_run_id = str(uuid4())
        record = ResearchRunRecord(research_run_id, payload, metadata)
        self._collection("research_runs").insert_one(record.__dict__)
        return record

    def create_founder_profile(
        self,
        profile: FounderProfile,
        research_run_id: str | None = None,
    ) -> FounderProfileRecord:
        founder_id = self._founder_id(profile)
        now = datetime.now(UTC).isoformat()
        existing = self._collection("founder_profiles").find_one({"founderId": founder_id})
        version = int(existing.get("version", 0)) + 1 if existing else 1
        created_at = str(existing.get("createdAt", now)) if existing else now
        lineage = (
            research_run_id
            or str(existing.get("researchRunId", ""))
            if existing
            else research_run_id or ""
        )
        document = self._founder_profile_document(
            profile=profile,
            founder_id=founder_id,
            research_run_id=lineage,
            version=version,
            created_at=created_at,
            updated_at=now,
        )
        if existing:
            for field_name in (
                "founderIntelligence",
                "evidenceIntelligence",
                "investmentIntelligence",
                "auditMetadata",
            ):
                if field_name in existing and document.get(field_name) in (None, [], {}):
                    document[field_name] = existing[field_name]
        if existing:
            self._collection("founder_profiles").update_one(
                {"founderId": founder_id}, {"$set": document}
            )
        else:
            self._collection("founder_profiles").insert_one(document)
        return FounderProfileRecord(
            founder_id, lineage, profile, version, created_at, now
        )

    def update_founder_profile(
        self,
        founder_id: str,
        profile: FounderProfile,
        research_run_id: str | None = None,
    ) -> FounderProfileRecord:
        collection = self._collection("founder_profiles")
        existing = collection.find_one({"founderId": founder_id})
        now = datetime.now(UTC).isoformat()
        version = int(existing.get("version", 0)) + 1 if existing else 1
        created_at = str(existing.get("createdAt", now)) if existing else now
        lineage = research_run_id or str(existing.get("researchRunId", "")) if existing else ""
        document = self._founder_profile_document(
            profile=profile,
            founder_id=founder_id,
            research_run_id=lineage,
            version=version,
            created_at=created_at,
            updated_at=now,
        )
        if existing:
            collection.update_one({"founderId": founder_id}, {"$set": document})
        else:
            collection.insert_one(document)
        return FounderProfileRecord(
            founder_id, lineage, profile, version, created_at, now
        )

    def enrich_founder_with_evidence_intelligence(
        self,
        founder_id: str,
        intelligence: EvidenceIntelligence,
        audit_metadata: dict[str, Any] | None = None,
    ) -> EvidenceIntelligenceRecord:
        collection = self._collection("founder_profiles")
        existing = collection.find_one({"founderId": founder_id})
        if existing is None:
            raise KeyError(f"Founder profile {founder_id!r} does not exist.")

        now = datetime.now(UTC).isoformat()
        audit_history = self._audit_history(existing.get("auditMetadata"))
        audit_history.append(
            {
                "layer": "layer-3",
                **(audit_metadata or {}),
                "updatedAt": now,
            }
        )
        version = int(existing.get("version", 0)) + 1
        created_at = str(existing.get("createdAt", now))
        collection.update_one(
            {"founderId": founder_id},
            {
                "$set": {
                    "evidenceIntelligence": intelligence.model_dump(mode="json"),
                    "auditMetadata": audit_history,
                    "version": version,
                    "updatedAt": now,
                }
            },
        )
        return EvidenceIntelligenceRecord(
            founder_id, version, created_at, now, audit_history
        )

    def enrich_founder_with_founder_intelligence(
        self,
        founder_id: str,
        intelligence: FounderIntelligence,
    ) -> FounderIntelligenceRecord:
        collection = self._collection("founder_profiles")
        existing = collection.find_one({"founderId": founder_id})
        if existing is None:
            raise KeyError(f"Founder profile {founder_id!r} does not exist.")

        now = datetime.now(UTC).isoformat()
        version = int(existing.get("version", 0)) + 1
        created_at = str(existing.get("createdAt", now))
        metadata = dict(existing.get("metadata", {}))
        metadata["lastUpdated"] = now
        collection.update_one(
            {"founderId": founder_id},
            {
                "$set": {
                    "founderIntelligence": intelligence.model_dump(mode="json"),
                    "profileVersion": version,
                    "metadata": metadata,
                    "version": version,
                    "updatedAt": now,
                }
            },
        )
        return FounderIntelligenceRecord(founder_id, version, created_at, now)

    def enrich_founder_with_investment_intelligence(
        self,
        founder_id: str,
        intelligence: InvestmentIntelligence,
    ) -> InvestmentIntelligenceRecord:
        collection = self._collection("founder_profiles")
        existing = collection.find_one({"founderId": founder_id})
        if existing is None:
            raise KeyError(f"Founder profile {founder_id!r} does not exist.")

        now = datetime.now(UTC).isoformat()
        version = int(existing.get("version", 0)) + 1
        created_at = str(existing.get("createdAt", now))
        collection.update_one(
            {"founderId": founder_id},
            {
                "$set": {
                    "investmentIntelligence": intelligence.model_dump(mode="json"),
                    "version": version,
                    "updatedAt": now,
                }
            },
        )
        return InvestmentIntelligenceRecord(founder_id, version, created_at, now)

    def create_investment_memo_artifact(
        self,
        founder_id: str,
        artifact: InvestmentMemoArtifact,
    ) -> InvestmentMemoArtifactRecord:
        if self._collection("founder_profiles").find_one({"founderId": founder_id}) is None:
            raise KeyError(f"Founder profile {founder_id!r} does not exist.")

        collection = self._collection("investment_memos")
        previous_versions = [
            int(document.get("version", 0))
            for document in collection.find({"founderId": founder_id})
        ]
        version = max(previous_versions, default=0) + 1
        memo_id = str(uuid4())
        generated_at = datetime.now(UTC).isoformat()
        collection.insert_one(
            {
                "memoId": memo_id,
                "founderId": founder_id,
                "version": version,
                "generatedAt": generated_at,
                **artifact.model_dump(mode="json"),
            }
        )
        return InvestmentMemoArtifactRecord(memo_id, founder_id, version, generated_at)

    @staticmethod
    def _founder_id(profile: FounderProfile) -> str:
        return profile.founder.id or profile.metadata.profileId or str(uuid4())

    @staticmethod
    def _founder_profile_document(
        *,
        profile: FounderProfile,
        founder_id: str,
        research_run_id: str,
        version: int,
        created_at: str,
        updated_at: str,
    ) -> dict[str, Any]:
        # Keep the Layer 2 payload unchanged; persistence metadata is additive.
        return {
            **profile.model_dump(mode="json"),
            "founderId": founder_id,
            "researchRunId": research_run_id,
            "version": version,
            "profileVersion": version,
            "createdAt": created_at,
            "updatedAt": updated_at,
        }

    @staticmethod
    def _audit_history(value: Any) -> list[dict[str, Any]]:
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [dict(value)]
        return []

    def upload_private_file(
        self,
        *,
        bucket: str | None = None,
        path: str,
        content: bytes | None = None,
        content_type: str | None = None,
    ) -> str:
        if content is not None and bucket and isinstance(self._database, Database):
            GridFSBucket(self._database, bucket_name=bucket).upload_from_stream(
                path,
                content,
                metadata={"contentType": content_type or "application/octet-stream"},
            )
        return path


def build_mongodb_gateway(settings: Settings | None = None) -> MongoDBGateway:
    settings = settings or get_settings()
    if not settings.mongodb_uri:
        raise IntegrationNotConfigured("MongoDB requires MONGODB_URI.")

    try:
        client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=1000)
        if hasattr(client, "admin") and hasattr(client.admin, "command"):
            client.admin.command("ping")
        return MongoClientGateway(client, settings.mongodb_database)
    except Exception:
        return MongoClientGateway(
            InMemoryMongoClient(settings.mongodb_database), settings.mongodb_database
        )


class MongoClientGateway(MongoDBGateway):
    pass
