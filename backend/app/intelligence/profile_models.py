"""Contracts for collected founder data and the Layer 2 FounderProfile output."""

from __future__ import annotations

from typing import Any, cast

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic import Field as PydanticField


def field(*args: Any, **kwargs: Any) -> Any:
    """Wrap Pydantic Field so empty list/dict defaults stay type-safe for analysis."""
    default_factory = kwargs.get("default_factory")
    if default_factory is list:
        kwargs["default_factory"] = lambda: cast(list[Any], [])
    elif default_factory is dict:
        kwargs["default_factory"] = lambda: cast(dict[str, Any], {})
    return PydanticField(*args, **kwargs)


Field = field


class Layer1Metadata(BaseModel):
    """Metadata supplied by the data-collection layer."""

    model_config = ConfigDict(extra="allow")

    founderId: str = ""
    collectedAt: str = ""
    dataSources: list[str] = field(default_factory=list)


class Layer1Input(BaseModel):
    """Stable hand-off contract between Layer 1 collectors and Layer 2."""

    model_config = ConfigDict(extra="allow")

    github: dict[str, Any] = field(default_factory=dict)
    resume: dict[str, Any] = field(default_factory=dict)
    website: dict[str, Any] = field(default_factory=dict)
    tavily: dict[str, Any] = field(default_factory=dict)
    metadata: Layer1Metadata = field(default_factory=Layer1Metadata)


class ProfileModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evidence(ProfileModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = ""
    type: str = ""
    title: str = ""
    source: str = ""
    url: str = ""
    retrievedAt: str = ""
    publishedAt: str = ""
    confidence: str = ""
    supports: list[str] = field(default_factory=list)
    content: str = ""
    excerpt: str = ""
    quote: str = ""
    sourceCategory: str = "Unknown"
    publisherType: str = "Unknown"
    contentType: str = "Unknown"
    claimCategory: str = "Unknown"


class ProfileMetadata(ProfileModel):
    profileId: str = ""
    generatedAt: str = ""
    lastUpdated: str = ""
    schemaVersion: str = "1.0.0"
    dataSources: list[str] = field(default_factory=list)
    completenessScore: float = 0


class Founder(ProfileModel):
    id: str = ""
    name: str = ""
    headline: str = ""
    email: str = ""
    location: str = ""
    currentCompany: str = ""
    website: str = ""
    github: str = ""
    linkedin: str = ""
    twitter: str = ""
    huggingface: str = ""
    googleScholar: str = ""
    profileImage: str = ""
    bio: str = ""


class Education(ProfileModel):
    id: str = ""
    institution: str = ""
    degree: str = ""
    field: str = ""
    startDate: str = ""
    endDate: str = ""
    grade: str = ""
    location: str = ""
    description: str = ""
    evidenceIds: list[str] = Field(default_factory=list)


class Experience(ProfileModel):
    id: str = ""
    company: str = ""
    role: str = ""
    employmentType: str = ""
    industry: str = ""
    startDate: str = ""
    endDate: str = ""
    isCurrent: bool = False
    location: str = ""
    description: str = ""
    skillsUsed: list[str] = Field(default_factory=list)
    evidenceIds: list[str] = Field(default_factory=list)


class Skills(ProfileModel):
    programmingLanguages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    aiMl: list[str] = Field(default_factory=list)
    cloud: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    devops: list[str] = Field(default_factory=list)
    leadership: list[str] = Field(default_factory=list)
    product: list[str] = Field(default_factory=list)
    business: list[str] = Field(default_factory=list)
    other: list[str] = Field(default_factory=list)


class Project(ProfileModel):
    id: str = ""
    name: str = ""
    description: str = ""
    category: str = ""
    technologies: list[str] = Field(default_factory=list)
    githubRepo: str = ""
    demoUrl: str = ""
    website: str = ""
    startDate: str = ""
    endDate: str = ""
    status: str = ""
    teamSize: int = 0
    evidenceIds: list[str] = Field(default_factory=list)


class Repository(ProfileModel):
    id: str = ""
    name: str = ""
    description: str = ""
    url: str = ""
    primaryLanguage: str = ""
    languages: list[str] = Field(default_factory=list)
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    openIssues: int = 0
    createdAt: str = ""
    updatedAt: str = ""
    topics: list[str] = Field(default_factory=list)
    license: str = ""
    isFork: bool = False


class Funding(ProfileModel):
    raised: str = ""
    currency: str = ""
    round: str = ""
    investors: list[str] = Field(default_factory=list)


class StartupHistory(ProfileModel):
    id: str = ""
    company: str = ""
    role: str = ""
    industry: str = ""
    stage: str = ""
    startDate: str = ""
    endDate: str = ""
    status: str = ""
    description: str = ""
    website: str = ""
    funding: Funding = Field(default_factory=Funding)
    evidenceIds: list[str] = Field(default_factory=list)


class ProductLaunch(ProfileModel):
    id: str = ""
    productName: str = ""
    launchDate: str = ""
    description: str = ""
    website: str = ""
    productHunt: str = ""
    github: str = ""
    status: str = ""
    evidenceIds: list[str] = Field(default_factory=list)


class Research(ProfileModel):
    id: str = ""
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    publication: str = ""
    year: str = ""
    url: str = ""
    citations: int = 0
    keywords: list[str] = Field(default_factory=list)
    evidenceIds: list[str] = Field(default_factory=list)


class PublicSpeaking(ProfileModel):
    id: str = ""
    title: str = ""
    event: str = ""
    date: str = ""
    location: str = ""
    video: str = ""
    slides: str = ""
    topic: str = ""
    evidenceIds: list[str] = Field(default_factory=list)


class Award(ProfileModel):
    id: str = ""
    title: str = ""
    organization: str = ""
    date: str = ""
    description: str = ""
    evidenceIds: list[str] = Field(default_factory=list)


class Grant(ProfileModel):
    id: str = ""
    organization: str = ""
    program: str = ""
    amount: str = ""
    date: str = ""
    description: str = ""
    evidenceIds: list[str] = Field(default_factory=list)


class Patent(ProfileModel):
    id: str = ""
    title: str = ""
    patentNumber: str = ""
    status: str = ""
    date: str = ""
    url: str = ""
    evidenceIds: list[str] = Field(default_factory=list)


class OpenSource(ProfileModel):
    totalRepositories: int = 0
    totalStars: int = 0
    totalForks: int = 0
    organizations: list[str] = Field(default_factory=list)
    majorProjects: list[str] = Field(default_factory=list)


class CommunityItem(ProfileModel):
    """Common strict shape for blogs, mentions, podcasts, and newsletters."""

    id: str = ""
    title: str = ""
    name: str = ""
    url: str = ""
    source: str = ""
    author: str = ""
    publishedAt: str = ""
    date: str = ""
    description: str = ""
    summary: str = ""
    content: str = ""
    event: str = ""
    location: str = ""
    video: str = ""
    slides: str = ""
    topic: str = ""
    episode: str = ""
    publication: str = ""
    guests: list[str] = Field(default_factory=list)
    evidenceIds: list[str] = Field(default_factory=list)


class Community(ProfileModel):
    blogs: list[CommunityItem] = Field(default_factory=list)
    newsMentions: list[CommunityItem] = Field(default_factory=list)
    podcasts: list[CommunityItem] = Field(default_factory=list)
    interviews: list[CommunityItem] = Field(default_factory=list)
    newsletters: list[CommunityItem] = Field(default_factory=list)


class SocialPresence(ProfileModel):
    githubFollowers: int = 0
    linkedinFollowers: int = 0
    twitterFollowers: int = 0
    huggingfaceFollowers: int = 0


class TimelineEvent(ProfileModel):
    id: str = ""
    date: str = ""
    type: str = ""
    title: str = ""
    description: str = ""
    relatedEntity: str = ""
    evidenceIds: list[str] = Field(default_factory=list)


class Entities(ProfileModel):
    companies: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    researchAreas: list[str] = Field(default_factory=list)


class Unknown(ProfileModel):
    category: str = ""
    field: str = ""
    reason: str = ""
    importance: str = ""
    priority: str = ""
    recommendedAction: str = ""
    entityType: str = ""
    entityId: str = ""


class FounderProfile(ProfileModel):
    """Schema-compliant output of the Layer 2 profile-generation stage."""

    metadata: ProfileMetadata = Field(default_factory=ProfileMetadata)
    founder: Founder = Field(default_factory=Founder)
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    projects: list[Project] = Field(default_factory=list)
    repositories: list[Repository] = Field(default_factory=list)
    startupHistory: list[StartupHistory] = Field(default_factory=list)
    productLaunches: list[ProductLaunch] = Field(default_factory=list)
    research: list[Research] = Field(default_factory=list)
    publicSpeaking: list[PublicSpeaking] = Field(default_factory=list)
    awards: list[Award] = Field(default_factory=list)
    grants: list[Grant] = Field(default_factory=list)
    patents: list[Patent] = Field(default_factory=list)
    opensource: OpenSource = Field(default_factory=OpenSource)
    community: Community = Field(default_factory=Community)
    socialPresence: SocialPresence = Field(default_factory=SocialPresence)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    entities: Entities = Field(default_factory=Entities)
    evidence: list[Evidence] = Field(default_factory=list)
    unknowns: list[Unknown] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_evidence_registry(cls, value: Any) -> Any:
        if isinstance(value, dict):
            from app.intelligence.evidence_registry import normalize_evidence_registry_payload

            return normalize_evidence_registry_payload(value)
        return value

    @model_validator(mode="after")
    def validate_evidence_registry(self) -> FounderProfile:
        from app.intelligence.evidence_registry import validate_evidence_references

        validate_evidence_references(self.model_dump(mode="python"))
        return self