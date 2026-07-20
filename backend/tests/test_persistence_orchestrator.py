from types import SimpleNamespace
from uuid import uuid4

from app.domain.investment_memos import InvestmentMemoArtifact
from app.domain.memos import MemoCreate
from app.intelligence.evidence_intelligence import EvidenceIntelligence
from app.intelligence.investment_intelligence import InvestmentIntelligence
from app.intelligence.profile_models import FounderProfile, Layer1Input
from app.persistence.orchestrator import PersistenceOrchestrator


class FakeGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def create_research_run(self, payload, metadata):
        self.calls.append(("create_research_run", payload, metadata))
        return SimpleNamespace(researchRunId="run-123", payload=payload.model_dump(mode="json"))

    def create_founder_profile(self, profile, research_run_id=None):
        self.calls.append(("create_founder_profile", profile, research_run_id))
        return SimpleNamespace(
            founderId="founder-123",
            researchRunId="run-123",
            profile=profile,
            version=1,
        )

    def update_founder_profile(self, founder_id, profile, research_run_id=None):
        self.calls.append(("update_founder_profile", founder_id, profile, research_run_id))
        return SimpleNamespace(
            founderId=founder_id,
            researchRunId=research_run_id,
            profile=profile,
            version=2,
        )

    def enrich_founder_with_evidence_intelligence(
        self, founder_id, intelligence, audit_metadata=None
    ):
        self.calls.append(
            ("enrich_founder_with_evidence_intelligence", founder_id, intelligence, audit_metadata)
        )
        return SimpleNamespace(founderId=founder_id, version=2)

    def enrich_founder_with_investment_intelligence(self, founder_id, intelligence):
        self.calls.append(
            ("enrich_founder_with_investment_intelligence", founder_id, intelligence)
        )
        return SimpleNamespace(founderId=founder_id, version=3)

    def create_investment_memo_artifact(self, founder_id, artifact):
        self.calls.append(("create_investment_memo_artifact", founder_id, artifact))
        return SimpleNamespace(memoId="memo-123", founderId=founder_id, version=1)

    def create_memo(self, memo):
        self.calls.append(("create_memo", memo))
        return memo


def test_save_research_run_delegates_to_gateway() -> None:
    gateway = FakeGateway()
    payload = Layer1Input.model_validate({"tavily": {"claims": []}})

    result = PersistenceOrchestrator(gateway).save_research_run(payload, {"query": "Ada"})

    assert result.researchRunId == "run-123"
    assert gateway.calls == [("create_research_run", payload, {"query": "Ada"})]


def test_profile_and_memo_operations_delegate_to_gateway() -> None:
    gateway = FakeGateway()
    orchestrator = PersistenceOrchestrator(gateway)
    profile = FounderProfile.model_validate({"metadata": {"profileId": "profile-123"}})
    memo = MemoCreate(
        founder_id=uuid4(),
        title="Ada investment memo",
    )

    saved = orchestrator.save_founder_profile(profile, "run-123")
    updated = orchestrator.update_founder_profile("founder-123", profile, "run-456")
    assert orchestrator.save_investment_memo(memo) is memo
    assert saved.founderId == "founder-123"
    assert updated.founderId == "founder-123"
    assert gateway.calls == [
        ("create_founder_profile", profile, "run-123"),
        ("update_founder_profile", "founder-123", profile, "run-456"),
        ("create_memo", memo),
    ]


def test_save_evidence_intelligence_delegates_to_gateway() -> None:
    gateway = FakeGateway()
    intelligence = EvidenceIntelligence.model_validate(
        {"evidence": [{"id": "evidence-1", "title": "Founder website"}]}
    )

    result = PersistenceOrchestrator(gateway).save_evidence_intelligence(
        "founder-123", intelligence, {"jobId": "layer-3-job"}
    )

    assert result.founderId == "founder-123"
    assert result.version == 2
    assert gateway.calls == [
        (
            "enrich_founder_with_evidence_intelligence",
            "founder-123",
            intelligence,
            {"jobId": "layer-3-job"},
        )
    ]


def test_save_investment_intelligence_delegates_to_gateway() -> None:
    gateway = FakeGateway()
    intelligence = InvestmentIntelligence(
        founderScores={"execution": 82.0},
        categoryScores={"founder": 82.0},
        strengths=["Technical depth"],
        recommendation="advance_to_partner_review",
        confidence=0.82,
    )

    result = PersistenceOrchestrator(gateway).save_investment_intelligence(
        "founder-123", intelligence
    )

    assert result.founderId == "founder-123"
    assert result.version == 3
    assert gateway.calls == [
        ("enrich_founder_with_investment_intelligence", "founder-123", intelligence)
    ]


def test_save_final_investment_memo_delegates_to_gateway() -> None:
    gateway = FakeGateway()
    artifact = InvestmentMemoArtifact(
        memo="Invest in the company.",
        executiveSummary="Strong technical founder.",
        narration="This is the narrated investment case.",
        audioUrl="https://cdn.example.com/memos/memo-123.mp3",
        generatedCharts=[{"type": "radar", "url": "https://cdn.example.com/chart.png"}],
        presentationMetadata={"deckUrl": "https://cdn.example.com/deck.pdf"},
    )

    result = PersistenceOrchestrator(gateway).save_final_investment_memo(
        "founder-123", artifact
    )

    assert result.memoId == "memo-123"
    assert result.founderId == "founder-123"
    assert result.version == 1
    assert gateway.calls == [("create_investment_memo_artifact", "founder-123", artifact)]