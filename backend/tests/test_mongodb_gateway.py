from types import SimpleNamespace

import pytest

from app.core.errors import IntegrationNotConfigured
from app.core.settings import Settings
from app.domain.founders import FounderCreate
from app.domain.investment_memos import InvestmentMemoArtifact
from app.integrations.mongodb.gateway import build_mongodb_gateway
from app.intelligence.evidence_intelligence import EvidenceIntelligence
from app.intelligence.investment_intelligence import InvestmentIntelligence
from app.intelligence.profile_models import FounderIntelligence, FounderProfile


class FakeCollection:
    def __init__(self):
        self.documents = []

    def insert_one(self, document):
        self.documents.append(document)
        return SimpleNamespace(inserted_id="doc-id")

    def find_one(self, filter):
        for document in self.documents:
            if all(document.get(key) == value for key, value in filter.items()):
                return document
        return None

    def find(self, filter):
        return [
            document
            for document in self.documents
            if all(document.get(key) == value for key, value in filter.items())
        ]

    def update_one(self, filter, update):
        for document in self.documents:
            if all(document.get(key) == value for key, value in filter.items()):
                document.update(update["$set"])
                return SimpleNamespace(matched_count=1, modified_count=1)
        return SimpleNamespace(matched_count=0, modified_count=0)


class FakeDatabase:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        return self.collections.setdefault(name, FakeCollection())


class FakeMongoClient:
    def __init__(self, uri, database_name=None):
        self.uri = uri
        self.database_name = database_name or "vc-brain"
        self.database = FakeDatabase()

    def __getitem__(self, name):
        return self.database


def test_build_mongodb_gateway_requires_uri():
    with pytest.raises(IntegrationNotConfigured):
        build_mongodb_gateway(Settings(mongodb_uri=None, mongodb_database="vc_test"))


def test_create_founder_inserts_document(monkeypatch):
    monkeypatch.setattr("app.integrations.mongodb.gateway.MongoClient", FakeMongoClient)

    gateway = build_mongodb_gateway(
        Settings(mongodb_uri="mongodb://localhost:27017", mongodb_database="vc_test")
    )
    founder = gateway.create_founder(
        FounderCreate(
            full_name="Ada Lovelace",
            email="ada@example.com",
            company_name="Analytical Engine",
        )
    )

    assert founder.full_name == "Ada Lovelace"
    assert founder.id is not None
    assert founder.created_at is not None
    assert founder.updated_at is not None
    assert gateway._database_name == "vc_test"


def test_upload_private_file_accepts_legacy_keywords(monkeypatch):
    monkeypatch.setattr("app.integrations.mongodb.gateway.MongoClient", FakeMongoClient)

    gateway = build_mongodb_gateway(
        Settings(mongodb_uri="mongodb://localhost:27017", mongodb_database="vc_test")
    )

    path = gateway.upload_private_file(
        bucket="investment-memos",
        path="demo/audio.mp3",
        content=b"audio",
        content_type="audio/mpeg",
    )

    assert path == "demo/audio.mp3"


def test_create_and_update_founder_profile(monkeypatch):
    monkeypatch.setattr("app.integrations.mongodb.gateway.MongoClient", FakeMongoClient)

    gateway = build_mongodb_gateway(
        Settings(mongodb_uri="mongodb://localhost:27017", mongodb_database="vc_test")
    )
    original = FounderProfile.model_validate(
        {
            "metadata": {"profileId": "profile-123"},
            "founder": {"name": "Ada Lovelace"},
        }
    )
    updated = FounderProfile.model_validate(
        {
            "metadata": {"profileId": "profile-123"},
            "founder": {"name": "Grace Hopper"},
        }
    )

    saved = gateway.create_founder_profile(original, "run-123")
    result = gateway.update_founder_profile("profile-123", updated, "run-456")
    document = gateway._collection("founder_profiles").documents[0]

    assert saved.founderId == "profile-123"
    assert saved.researchRunId == "run-123"
    assert saved.version == 1
    assert saved.profile is original
    assert result.founderId == "profile-123"
    assert result.researchRunId == "run-456"
    assert result.version == 2
    assert result.createdAt == saved.createdAt
    assert result.updatedAt >= saved.updatedAt
    assert document["founder"]["name"] == "Grace Hopper"
    assert document["researchRunId"] == "run-456"
    assert document["version"] == 2
    assert document["createdAt"] == saved.createdAt
    assert document["updatedAt"] == result.updatedAt


def test_evidence_intelligence_enriches_without_overwriting_layer2(monkeypatch):
    monkeypatch.setattr("app.integrations.mongodb.gateway.MongoClient", FakeMongoClient)
    gateway = build_mongodb_gateway(
        Settings(mongodb_uri="mongodb://localhost:27017", mongodb_database="vc_test")
    )
    profile = FounderProfile.model_validate(
        {
            "metadata": {"profileId": "founder-123", "schemaVersion": "2.0.0"},
            "founder": {"name": "Ada Lovelace", "headline": "Mathematician"},
            "experience": [{"id": "experience-1", "company": "Analytical Engine"}],
            "evidence": [{"id": "layer2-evidence", "title": "Layer 2 source"}],
        }
    )
    saved = gateway.create_founder_profile(profile, "run-123")
    layer2_payload = profile.model_dump(mode="json")
    intelligence = EvidenceIntelligence.model_validate(
        {
            "evidence": [{"id": "layer3-evidence", "title": "Classified source"}],
            "evidenceRegistry": [
                {"id": "layer3-evidence", "title": "Canonical Layer 3 source"}
            ],
            "verification": [
                {
                    "claimId": "claim-1",
                    "evidenceIds": ["layer3-evidence"],
                    "verification": {
                        "supportStrength": "Strong",
                        "supportType": "Primary",
                        "reasoning": "Direct source statement.",
                    },
                }
            ],
            "reliability": [
                {
                    "evidenceId": "layer3-evidence",
                    "reliability": {
                        "sourceReliability": 90,
                        "claimReliability": 85,
                        "overallEvidenceReliability": 88,
                        "overallScore": 88,
                        "factorBreakdown": {
                            "sourceCredibility": 90,
                            "directness": 90,
                            "corroboration": 80,
                            "freshness": 85,
                            "identityMatch": 95,
                            "claimSpecificity": 88,
                        },
                        "explanation": "Primary source with direct support.",
                    },
                }
            ],
            "entityConfidence": [],
            "contradictions": [],
            "unknowns": [{"category": "missing_field", "field": "funding"}],
        }
    )

    result = gateway.enrich_founder_with_evidence_intelligence(
        saved.founderId,
        intelligence,
        {"jobId": "layer-3-job", "modelVersion": "3.0.0"},
    )
    document = gateway._collection("founder_profiles").documents[0]

    assert document["metadata"] == layer2_payload["metadata"]
    assert document["founder"] == layer2_payload["founder"]
    assert document["experience"] == layer2_payload["experience"]
    assert document["evidence"] == layer2_payload["evidence"]
    assert document["evidenceIntelligence"] == intelligence.model_dump(mode="json")
    assert result.founderId == saved.founderId
    assert result.version == saved.version + 1
    assert result.createdAt == saved.createdAt
    assert result.updatedAt >= saved.updatedAt
    assert document["version"] == result.version
    assert document["updatedAt"] == result.updatedAt
    assert document["auditMetadata"] == [
        {
            "layer": "layer-3",
            "jobId": "layer-3-job",
            "modelVersion": "3.0.0",
            "updatedAt": result.updatedAt,
        }
    ]

    second_result = gateway.enrich_founder_with_evidence_intelligence(
        saved.founderId,
        EvidenceIntelligence(),
        {"jobId": "layer-3-job-2"},
    )

    assert second_result.version == result.version + 1
    assert document["auditMetadata"][0]["jobId"] == "layer-3-job"
    assert document["auditMetadata"][1]["jobId"] == "layer-3-job-2"


def test_founder_intelligence_updates_existing_profile(monkeypatch):
    monkeypatch.setattr("app.integrations.mongodb.gateway.MongoClient", FakeMongoClient)
    gateway = build_mongodb_gateway(
        Settings(mongodb_uri="mongodb://localhost:27017", mongodb_database="vc_test")
    )
    profile = FounderProfile.model_validate(
        {"metadata": {"profileId": "founder-123"}, "founder": {"name": "Ada Lovelace"}}
    )
    saved = gateway.create_founder_profile(profile, "run-123")
    intelligence = FounderIntelligence.model_validate(
        {
            "strengths": ["Technical depth"],
            "confidenceScores": [{"dimension": "technicalDepth", "score": 0.9}],
        }
    )

    result = gateway.enrich_founder_with_founder_intelligence(
        saved.founderId,
        intelligence,
    )
    documents = gateway._collection("founder_profiles").documents

    assert len(documents) == 1
    assert documents[0]["founderIntelligence"] == intelligence.model_dump(mode="json")
    assert documents[0]["profileVersion"] == 2
    assert documents[0]["metadata"]["lastUpdated"] == result.updatedAt
    assert result.version == 2


def test_create_founder_profile_upserts_same_identifier(monkeypatch):
    monkeypatch.setattr("app.integrations.mongodb.gateway.MongoClient", FakeMongoClient)
    gateway = build_mongodb_gateway(
        Settings(mongodb_uri="mongodb://localhost:27017", mongodb_database="vc_test")
    )
    first_profile = FounderProfile.model_validate(
        {"metadata": {"profileId": "founder-123"}, "founder": {"name": "Ada Lovelace"}}
    )
    second_profile = FounderProfile.model_validate(
        {"metadata": {"profileId": "founder-123"}, "founder": {"name": "Ada Byron"}}
    )

    first = gateway.create_founder_profile(first_profile, "run-123")
    second = gateway.create_founder_profile(second_profile, "run-456")
    documents = gateway._collection("founder_profiles").documents

    assert len(documents) == 1
    assert documents[0]["founder"]["name"] == "Ada Byron"
    assert first.version == 1
    assert second.version == 2
    assert documents[0]["profileVersion"] == 2


def test_evidence_intelligence_rejects_missing_founder_profile(monkeypatch):
    monkeypatch.setattr("app.integrations.mongodb.gateway.MongoClient", FakeMongoClient)
    gateway = build_mongodb_gateway(
        Settings(mongodb_uri="mongodb://localhost:27017", mongodb_database="vc_test")
    )

    with pytest.raises(KeyError, match="does not exist"):
        gateway.enrich_founder_with_evidence_intelligence(
            "missing-founder", EvidenceIntelligence()
        )


def test_investment_intelligence_preserves_layer2_and_layer3_data(monkeypatch):
    monkeypatch.setattr("app.integrations.mongodb.gateway.MongoClient", FakeMongoClient)
    gateway = build_mongodb_gateway(
        Settings(mongodb_uri="mongodb://localhost:27017", mongodb_database="vc_test")
    )
    profile = FounderProfile.model_validate(
        {
            "metadata": {"profileId": "founder-123"},
            "founder": {"name": "Ada Lovelace"},
            "experience": [{"id": "experience-1", "company": "Analytical Engine"}],
        }
    )
    saved = gateway.create_founder_profile(profile, "run-123")
    evidence_intelligence = EvidenceIntelligence.model_validate(
        {"unknowns": [{"category": "missing_field", "field": "funding"}]}
    )
    evidence_result = gateway.enrich_founder_with_evidence_intelligence(
        saved.founderId, evidence_intelligence, {"jobId": "layer-3-job"}
    )
    document = gateway._collection("founder_profiles").documents[0]
    layer2_payload = profile.model_dump(mode="json")
    layer3_payload = evidence_intelligence.model_dump(mode="json")
    audit_metadata = list(document["auditMetadata"])
    intelligence = InvestmentIntelligence(
        founderScores={"execution": 82.0, "technical": 90.0},
        categoryScores={"founder": 86.0, "market": 72.0},
        strengths=["Technical depth"],
        weaknesses=["No commercial track record"],
        opportunities=["Growing AI tooling demand"],
        risks=["Crowded market"],
        recommendation="advance_to_partner_review",
        confidence=0.82,
    )

    result = gateway.enrich_founder_with_investment_intelligence(saved.founderId, intelligence)

    assert document["metadata"] == layer2_payload["metadata"]
    assert document["founder"] == layer2_payload["founder"]
    assert document["experience"] == layer2_payload["experience"]
    assert document["evidenceIntelligence"] == layer3_payload
    assert document["auditMetadata"] == audit_metadata
    assert document["investmentIntelligence"] == intelligence.model_dump(mode="json")
    assert result.founderId == saved.founderId
    assert result.version == evidence_result.version + 1
    assert result.createdAt == saved.createdAt
    assert result.updatedAt >= evidence_result.updatedAt
    assert document["version"] == result.version
    assert document["updatedAt"] == result.updatedAt


def test_investment_intelligence_rejects_missing_founder_profile(monkeypatch):
    monkeypatch.setattr("app.integrations.mongodb.gateway.MongoClient", FakeMongoClient)
    gateway = build_mongodb_gateway(
        Settings(mongodb_uri="mongodb://localhost:27017", mongodb_database="vc_test")
    )

    with pytest.raises(KeyError, match="does not exist"):
        gateway.enrich_founder_with_investment_intelligence(
            "missing-founder", InvestmentIntelligence()
        )


def test_final_memo_artifacts_are_versioned_and_append_only(monkeypatch):
    monkeypatch.setattr("app.integrations.mongodb.gateway.MongoClient", FakeMongoClient)
    gateway = build_mongodb_gateway(
        Settings(mongodb_uri="mongodb://localhost:27017", mongodb_database="vc_test")
    )
    profile = FounderProfile.model_validate(
        {
            "metadata": {"profileId": "founder-123"},
            "founder": {"name": "Ada Lovelace"},
        }
    )
    gateway.create_founder_profile(profile, "run-123")
    first_artifact = InvestmentMemoArtifact(
        memo="Invest in the company.",
        executiveSummary="Strong technical founder.",
        narration="First narrated investment case.",
        audioUrl="https://cdn.example.com/memos/first.mp3",
        generatedCharts=[{"type": "radar", "url": "https://cdn.example.com/first-chart.png"}],
        presentationMetadata={"deckUrl": "https://cdn.example.com/first-deck.pdf"},
    )
    second_artifact = InvestmentMemoArtifact(
        memo="Hold for additional market evidence.",
        executiveSummary="Technical strength with market uncertainty.",
        narration="Second narrated investment case.",
        audioUrl="https://cdn.example.com/memos/second.mp3",
        generatedCharts=[{"type": "bar", "url": "https://cdn.example.com/second-chart.png"}],
        presentationMetadata={"deckUrl": "https://cdn.example.com/second-deck.pdf"},
    )

    first_result = gateway.create_investment_memo_artifact("founder-123", first_artifact)
    second_result = gateway.create_investment_memo_artifact("founder-123", second_artifact)
    documents = gateway._collection("investment_memos").documents

    assert first_result.founderId == "founder-123"
    assert first_result.version == 1
    assert first_result.generatedAt
    assert second_result.founderId == "founder-123"
    assert second_result.version == 2
    assert second_result.generatedAt
    assert len(documents) == 2
    assert documents[0] == {
        "memoId": first_result.memoId,
        "founderId": "founder-123",
        "version": 1,
        "generatedAt": first_result.generatedAt,
        **first_artifact.model_dump(mode="json"),
    }
    assert documents[1] == {
        "memoId": second_result.memoId,
        "founderId": "founder-123",
        "version": 2,
        "generatedAt": second_result.generatedAt,
        **second_artifact.model_dump(mode="json"),
    }


def test_final_memo_artifact_rejects_missing_founder_profile(monkeypatch):
    monkeypatch.setattr("app.integrations.mongodb.gateway.MongoClient", FakeMongoClient)
    gateway = build_mongodb_gateway(
        Settings(mongodb_uri="mongodb://localhost:27017", mongodb_database="vc_test")
    )

    with pytest.raises(KeyError, match="does not exist"):
        gateway.create_investment_memo_artifact(
            "missing-founder",
            InvestmentMemoArtifact(memo="Memo", executiveSummary="Summary"),
        )
