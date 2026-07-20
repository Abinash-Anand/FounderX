"""Deterministic source and claim classification for registered evidence."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

from app.intelligence.profile_models import Evidence, FounderProfile

OFFICIAL_WEBSITE = "Official Website"
GOVERNMENT = "Government"
UNIVERSITY = "University"
RESEARCH_PAPER = "Research Paper"
PATENT = "Patent"
GITHUB = "GitHub"
LINKEDIN = "LinkedIn"
INVESTOR = "Investor"
COMPANY_BLOG = "Company Blog"
NEWS = "News"
PODCAST = "Podcast"
CONFERENCE = "Conference"
SOCIAL_MEDIA = "Social Media"
PERSONAL_WEBSITE = "Personal Website"
COMMUNITY = "Community"
FORUM = "Forum"
_UNKNOWN = "Unknown"

SOURCE_CATEGORIES = (
    OFFICIAL_WEBSITE,
    GOVERNMENT,
    UNIVERSITY,
    RESEARCH_PAPER,
    PATENT,
    GITHUB,
    LINKEDIN,
    INVESTOR,
    COMPANY_BLOG,
    NEWS,
    PODCAST,
    CONFERENCE,
    SOCIAL_MEDIA,
    PERSONAL_WEBSITE,
    COMMUNITY,
    FORUM,
    _UNKNOWN,
)
_NEWS_DOMAINS = {
    "bbc.com",
    "bloomberg.com",
    "businessinsider.com",
    "cnn.com",
    "forbes.com",
    "ft.com",
    "nytimes.com",
    "reuters.com",
    "techcrunch.com",
    "theguardian.com",
    "venturebeat.com",
    "wired.com",
    "wsj.com",
}
_PODCAST_DOMAINS = {
    "anchor.fm",
    "buzzsprout.com",
    "podbean.com",
    "podcasts.apple.com",
    "spotify.com",
}
_FORUM_DOMAINS = {"news.ycombinator.com", "reddit.com", "stackoverflow.com"}
_SOCIAL_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "threads.net",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "youtube.com",
}

_PUBLISHER_TYPES = {
    OFFICIAL_WEBSITE: "official_organization",
    GOVERNMENT: "government",
    UNIVERSITY: "university",
    RESEARCH_PAPER: "research_institution",
    PATENT: "patent_authority",
    GITHUB: "code_host",
    LINKEDIN: "professional_network",
    INVESTOR: "investor",
    COMPANY_BLOG: "company",
    NEWS: "media",
    PODCAST: "media",
    CONFERENCE: "conference_organizer",
    SOCIAL_MEDIA: "social_platform",
    PERSONAL_WEBSITE: "individual",
    COMMUNITY: "community",
    FORUM: "community",
    _UNKNOWN: "unknown",
}

_TEXT_SOURCE_RULES = (
    (("official website", "company website", "corporate website"), OFFICIAL_WEBSITE),
    (("personal website", "portfolio website"), PERSONAL_WEBSITE),
    (("government", "ministry", "public agency"), GOVERNMENT),
    (("university", "college"), UNIVERSITY),
    (("research paper", "academic paper", "journal article", "preprint"), RESEARCH_PAPER),
    (("patent",), PATENT),
    (("github",), GITHUB),
    (("linkedin",), LINKEDIN),
    (("investor", "venture capital", "crunchbase", "pitchbook"), INVESTOR),
    (("company blog",), COMPANY_BLOG),
    (("news", "journalism", "press coverage"), NEWS),
    (("podcast", "podcast episode"), PODCAST),
    (("conference", "summit", "keynote"), CONFERENCE),
    (("social media", "social post", "tweet"), SOCIAL_MEDIA),
    (("community",), COMMUNITY),
    (("forum", "discussion thread"), FORUM),
)

_CONTENT_TYPE_MARKERS = (
    (("research paper", "academic paper", "journal article", "preprint"), "research_paper"),
    (("patent",), "patent"),
    (("repository", "repo", "code", "github"), "code_repository"),
    (("profile", "linkedin"), "professional_profile"),
    (("blog post", "blog"), "blog_post"),
    (("news article", "article", "press"), "article"),
    (("podcast", "episode"), "podcast_episode"),
    (("conference", "keynote", "talk"), "conference_talk"),
    (("social post", "tweet", "social"), "social_post"),
    (("forum", "thread", "discussion"), "forum_post"),
    (("website",), "website"),
)

_CLAIM_MARKERS = (
    (("education", "degree", "university", "school"), "education"),
    (("experience", "employment", "previous company", "previous startup", "role"), "experience"),
    (("startup", "current company", "company description"), "startup"),
    (("funding", "raised", "investor", "round"), "funding"),
    (("research", "paper", "publication", "citation"), "research"),
    (("technical", "skill", "repository", "github", "project"), "technical"),
    (("award", "grant", "patent"), "recognition"),
    (("conference talk", "public speaking", "speaking"), "public_speaking"),
    (("social", "follower", "linkedin", "twitter"), "social_presence"),
    (("founder", "name", "location", "bio", "identity"), "identity"),
)


def classify_evidence_registry(
    profile: FounderProfile | Mapping[str, Any],
) -> FounderProfile:
    """Return a new profile with every registry evidence item classified."""
    canonical_profile = FounderProfile.model_validate(profile)
    output = canonical_profile.model_dump(mode="python")
    output["evidence"] = [
        classify_evidence(item).model_dump(mode="python")
        for item in canonical_profile.evidence
    ]
    return FounderProfile.model_validate(output)


def classify_evidence(evidence: Evidence | Mapping[str, Any]) -> Evidence:
    """Classify one evidence item using only its declared metadata."""
    current = Evidence.model_validate(evidence)
    source_category = _source_category(current)
    output = current.model_dump(mode="python")
    output.update(
        sourceCategory=source_category,
        publisherType=_PUBLISHER_TYPES[source_category],
        contentType=_content_type(current, source_category),
        claimCategory=_claim_category(current.supports),
    )
    return Evidence.model_validate(output)


def _source_category(evidence: Evidence) -> str:
    host = _host(evidence.url)
    url_category = _url_source_category(host)
    if url_category != _UNKNOWN:
        return url_category

    text = _metadata_text(evidence)
    for markers, category in _TEXT_SOURCE_RULES:
        if any(marker in text for marker in markers):
            return category
    return _UNKNOWN


def _url_source_category(host: str) -> str:
    if _is_host(host, "github.com"):
        return GITHUB
    if _is_host(host, "linkedin.com"):
        return LINKEDIN
    if host.endswith(".gov") or ".gov." in host:
        return GOVERNMENT
    if host.endswith(".edu") or ".edu." in host:
        return UNIVERSITY
    if _is_host(host, "patents.google.com") or _is_host(host, "uspto.gov"):
        return PATENT
    if _is_host(host, "doi.org") or _is_host(host, "arxiv.org"):
        return RESEARCH_PAPER
    if _is_host(host, "podcasts.apple.com") or _matches_domain(host, _PODCAST_DOMAINS):
        return PODCAST
    if _matches_domain(host, _FORUM_DOMAINS):
        return FORUM
    if _matches_domain(host, _SOCIAL_DOMAINS):
        return SOCIAL_MEDIA
    if _matches_domain(host, _NEWS_DOMAINS):
        return NEWS
    return _UNKNOWN


def _content_type(evidence: Evidence, source_category: str) -> str:
    text = _metadata_text(evidence)
    for markers, content_type in _CONTENT_TYPE_MARKERS:
        if any(marker in text for marker in markers):
            return content_type
    return {
        OFFICIAL_WEBSITE: "website",
        PERSONAL_WEBSITE: "website",
        RESEARCH_PAPER: "research_paper",
        PATENT: "patent",
        GITHUB: "code_repository",
        LINKEDIN: "professional_profile",
        PODCAST: "podcast_episode",
        CONFERENCE: "conference_talk",
        SOCIAL_MEDIA: "social_post",
        FORUM: "forum_post",
    }.get(source_category, _UNKNOWN)


def _claim_category(supports: list[str]) -> str:
    categories: set[str] = set()
    for support in supports:
        normalized_support = _normalize_text(support)
        matches = {
            category
            for markers, category in _CLAIM_MARKERS
            if any(_contains_marker(normalized_support, marker) for marker in markers)
        }
        categories.update(matches)
    return categories.pop() if len(categories) == 1 else _UNKNOWN


def _metadata_text(evidence: Evidence) -> str:
    return _normalize_text(" ".join((evidence.type, evidence.source, evidence.title)))


def _normalize_text(value: str) -> str:
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value)
    return re.sub(r"[_\-/]+", " ", spaced).casefold()


def _contains_marker(text: str, marker: str) -> bool:
    return re.search(rf"\b{re.escape(marker)}\b", text) is not None


def _host(url: str) -> str:
    return urlparse(url).hostname.casefold() if urlparse(url).hostname else ""


def _is_host(host: str, domain: str) -> bool:
    return host == domain or host.endswith(f".{domain}")


def _matches_domain(host: str, domains: set[str]) -> bool:
    return any(_is_host(host, domain) for domain in domains)