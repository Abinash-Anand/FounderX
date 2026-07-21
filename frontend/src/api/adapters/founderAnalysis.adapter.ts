import { ApiError } from '../errors/ApiError'
import {
  founderAnalysisDtoSchema,
  type FounderAnalysisDto,
  type FounderIntelligenceDto,
} from '../dto/founderAnalysis.dto'
import type { FounderAnalysisModel } from '../../entities/founder/founderAnalysis.models'
import type {
  CareerModel,
  DisplayLink,
  FounderContext,
  ProjectsModel,
  SkillGroup,
  StartupsModel,
} from '../../entities/founder/founder.models'
import type { ResearchItemModel, ResearchModel, ResearchQueryModel } from '../../entities/research/research.models'
import type { FounderIntelligenceModel } from '../../entities/intelligence/intelligence.models'
import type { InvestmentMemoModel } from '../../entities/decision/decision.models'
import { adaptEvidence, createEvidenceIndex, resolveEvidence, type EvidenceIndex } from './evidence.adapter'
import { createLink, definedItems, optionalText, safeUrl, titleCase, uniqueText } from './normalization'

type Profile = FounderAnalysisDto['founderProfile']

function adaptSkills(skills: Profile['skills']): SkillGroup[] {
  return Object.entries(skills)
    .map(([key, values]) => ({ key, label: titleCase(key), values: uniqueText(values) }))
    .filter((group) => group.values.length > 0)
}

function founderLinks(founder: Profile['founder']): DisplayLink[] {
  return definedItems([
    createLink('Website', founder.website),
    createLink('GitHub', founder.github),
    createLink('LinkedIn', founder.linkedin),
    createLink('X / Twitter', founder.twitter),
    createLink('Hugging Face', founder.huggingface),
    createLink('Google Scholar', founder.googleScholar),
  ])
}

function adaptContext(dto: FounderAnalysisDto): FounderContext {
  const { founder, metadata } = dto.founderProfile
  return {
    id: founder.id || dto.metadata.founderId,
    researchRunId: dto.metadata.researchRunId,
    profileVersion: dto.metadata.profileVersion,
    name: optionalText(founder.name) ?? 'Unknown founder',
    headline: optionalText(founder.headline),
    currentCompany: optionalText(founder.currentCompany),
    location: optionalText(founder.location),
    bio: optionalText(founder.bio),
    profileImageUrl: safeUrl(founder.profileImage),
    links: founderLinks(founder),
    completenessScore: Math.min(100, Math.max(0, metadata.completenessScore)),
    generatedAt: optionalText(metadata.generatedAt),
    lastUpdated: optionalText(metadata.lastUpdated),
    dataSources: uniqueText(metadata.dataSources),
    recommendation: dto.investmentDecision.recommendation,
  }
}

function adaptCareer(profile: Profile, evidence: EvidenceIndex): CareerModel {
  return {
    experience: profile.experience.map((item) => ({
      id: item.id,
      organization: optionalText(item.company) ?? 'Unknown organization',
      title: optionalText(item.role),
      startDate: optionalText(item.startDate),
      endDate: optionalText(item.endDate),
      isCurrent: item.isCurrent,
      location: optionalText(item.location),
      description: optionalText(item.description),
      tags: uniqueText([item.employmentType, item.industry, ...item.skillsUsed]),
      ...resolveEvidence(item.evidenceIds, evidence),
    })),
    education: profile.education.map((item) => ({
      id: item.id,
      organization: optionalText(item.institution) ?? 'Unknown institution',
      title: optionalText([item.degree, item.field].filter(Boolean).join(' · ')),
      startDate: optionalText(item.startDate),
      endDate: optionalText(item.endDate),
      isCurrent: false,
      location: optionalText(item.location),
      description: optionalText(item.description),
      tags: uniqueText([item.grade]),
      ...resolveEvidence(item.evidenceIds, evidence),
    })),
    timeline: profile.timeline.map((item) => ({
      id: item.id,
      date: optionalText(item.date),
      type: optionalText(item.type),
      title: optionalText(item.title) ?? 'Untitled event',
      description: optionalText(item.description),
      relatedEntity: optionalText(item.relatedEntity),
      ...resolveEvidence(item.evidenceIds, evidence),
    })),
  }
}

function adaptStartups(profile: Profile, evidence: EvidenceIndex): StartupsModel {
  return {
    startups: profile.startupHistory.map((item) => ({
      id: item.id,
      company: optionalText(item.company) ?? 'Unknown company',
      role: optionalText(item.role),
      industry: optionalText(item.industry),
      stage: optionalText(item.stage),
      period: { start: optionalText(item.startDate), end: optionalText(item.endDate) },
      status: optionalText(item.status),
      description: optionalText(item.description),
      website: safeUrl(item.website),
      funding: {
        raised: optionalText(item.funding.raised),
        currency: optionalText(item.funding.currency),
        round: optionalText(item.funding.round),
        investors: uniqueText(item.funding.investors),
      },
      ...resolveEvidence(item.evidenceIds, evidence),
    })),
    productLaunches: profile.productLaunches.map((item) => ({
      id: item.id,
      name: optionalText(item.productName) ?? 'Unnamed product',
      launchDate: optionalText(item.launchDate),
      description: optionalText(item.description),
      status: optionalText(item.status),
      links: definedItems([
        createLink('Website', item.website),
        createLink('Product Hunt', item.productHunt),
        createLink('GitHub', item.github),
      ]),
      ...resolveEvidence(item.evidenceIds, evidence),
    })),
  }
}

function adaptProjects(profile: Profile, evidence: EvidenceIndex): ProjectsModel {
  return {
    projects: profile.projects.map((item) => ({
      id: item.id,
      name: optionalText(item.name) ?? 'Unnamed project',
      description: optionalText(item.description),
      category: optionalText(item.category),
      technologies: uniqueText(item.technologies),
      status: optionalText(item.status),
      teamSize: item.teamSize > 0 ? item.teamSize : null,
      links: definedItems([
        createLink('GitHub', item.githubRepo),
        createLink('Demo', item.demoUrl),
        createLink('Website', item.website),
      ]),
      ...resolveEvidence(item.evidenceIds, evidence),
    })),
    repositories: profile.repositories.map((item) => ({
      id: item.id,
      name: optionalText(item.name) ?? 'Unnamed repository',
      description: optionalText(item.description),
      url: safeUrl(item.url),
      primaryLanguage: optionalText(item.primaryLanguage),
      stars: item.stars,
      forks: item.forks,
      watchers: item.watchers,
      openIssues: item.openIssues,
      topics: uniqueText(item.topics),
      license: optionalText(item.license),
      isFork: item.isFork,
    })),
    openSource: profile.opensource,
  }
}

function adaptSearches(tavily: Record<string, unknown>): ResearchQueryModel[] {
  const searches = tavily.searches
  if (!Array.isArray(searches)) return []

  return searches.flatMap((value) => {
    if (!value || typeof value !== 'object') return []
    const item = value as Record<string, unknown>
    if (typeof item.query !== 'string') return []
    const sources = Array.isArray(item.sources) ? item.sources : []
    return [{
      query: item.query,
      answer: typeof item.answer === 'string' ? optionalText(item.answer) : null,
      sources: sources.flatMap((source) => {
        if (!source || typeof source !== 'object') return []
        const record = source as Record<string, unknown>
        return [{
          title: typeof record.title === 'string' && record.title.trim() ? record.title : 'Untitled source',
          url: typeof record.url === 'string' ? safeUrl(record.url) : null,
          content: typeof record.content === 'string' ? optionalText(record.content) : null,
          score: typeof record.score === 'number' ? record.score : null,
        }]
      }),
    }]
  })
}

function researchItem(
  kind: ResearchItemModel['kind'],
  item: { id: string; evidenceIds: string[] },
  evidence: EvidenceIndex,
  values: Omit<ResearchItemModel, 'id' | 'kind' | 'evidence' | 'unresolvedEvidenceIds'>,
): ResearchItemModel {
  return { id: item.id, kind, ...values, ...resolveEvidence(item.evidenceIds, evidence) }
}

function adaptResearch(dto: FounderAnalysisDto, evidence: EvidenceIndex): ResearchModel {
  const profile = dto.founderProfile
  const recognition: ResearchItemModel[] = [
    ...profile.awards.map((item) => researchItem('award', item, evidence, {
      title: optionalText(item.title) ?? 'Untitled award', subtitle: optionalText(item.organization),
      date: optionalText(item.date), description: optionalText(item.description), links: [], tags: [],
    })),
    ...profile.grants.map((item) => researchItem('grant', item, evidence, {
      title: optionalText(item.program) ?? 'Untitled grant', subtitle: optionalText(item.organization),
      date: optionalText(item.date), description: optionalText(item.description), links: [], tags: uniqueText([item.amount]),
    })),
    ...profile.patents.map((item) => researchItem('patent', item, evidence, {
      title: optionalText(item.title) ?? 'Untitled patent', subtitle: optionalText(item.patentNumber),
      date: optionalText(item.date), description: null, links: definedItems([createLink('Patent', item.url)]), tags: uniqueText([item.status]),
    })),
  ]
  const communityGroups = Object.entries(profile.community)
  const community = communityGroups.flatMap(([group, items]) => items.map((item) => researchItem('community', item, evidence, {
    title: optionalText(item.title) ?? optionalText(item.name) ?? 'Untitled mention',
    subtitle: optionalText(item.source) ?? optionalText(item.publication),
    date: optionalText(item.publishedAt) ?? optionalText(item.date),
    description: optionalText(item.summary) ?? optionalText(item.description),
    links: definedItems([createLink('Source', item.url)]), tags: [titleCase(group)],
  })))

  return {
    collectedAt: optionalText(dto.research.metadata.collectedAt),
    dataSources: uniqueText(dto.research.metadata.dataSources),
    searches: adaptSearches(dto.research.tavily),
    publications: profile.research.map((item) => researchItem('publication', item, evidence, {
      title: optionalText(item.title) ?? 'Untitled publication', subtitle: optionalText(item.publication),
      date: optionalText(item.year), description: null, links: definedItems([createLink('Publication', item.url)]), tags: item.keywords,
    })),
    speaking: profile.publicSpeaking.map((item) => researchItem('speaking', item, evidence, {
      title: optionalText(item.title) ?? 'Untitled appearance', subtitle: optionalText(item.event),
      date: optionalText(item.date), description: optionalText(item.topic),
      links: definedItems([createLink('Video', item.video), createLink('Slides', item.slides)]), tags: [],
    })),
    recognition,
    community,
  }
}

function adaptIntelligence(value: FounderIntelligenceDto, evidence: EvidenceIndex): FounderIntelligenceModel {
  const reasoning = new Map(value.reasoning.map((item) => [item.insight, optionalText(item.reasoning)]))
  return {
    strengths: uniqueText(value.strengths),
    weaknesses: uniqueText(value.weaknesses),
    executionRisks: uniqueText(value.executionRisks),
    assessments: [
      ['Leadership', value.leadershipAssessment],
      ['Technical depth', value.technicalDepthAssessment],
      ['Market credibility', value.marketCredibility],
    ].flatMap(([label, assessment]) => {
      const normalized = optionalText(assessment ?? '')
      return normalized ? [{ label: label ?? '', value: normalized }] : []
    }),
    qualitySignals: uniqueText(value.founderQualitySignals),
    confidenceScores: value.confidenceScores.map((item) => ({
      dimension: item.dimension,
      score: item.score,
    })),
    missingInformation: uniqueText(value.missingInformation),
    insights: value.evidenceReferences.map((item) => ({
      insight: item.insight,
      reasoning: reasoning.get(item.insight) ?? null,
      ...resolveEvidence(item.evidenceIds, evidence),
    })),
  }
}

function adaptDecision(dto: FounderAnalysisDto): InvestmentMemoModel {
  const decision = dto.investmentDecision
  return {
    companyName: optionalText(decision.company_name) ?? 'Unknown company',
    recommendation: decision.recommendation,
    thesis: optionalText(decision.state.thesis),
    sourceUrls: decision.state.source_urls.map(safeUrl).filter((url): url is string => url !== null),
    scores: Object.entries(decision.state.scores).map(([dimension, score]) => ({ dimension, score })),
    signals: decision.state.signals.map((signal) => ({
      sourceUrl: signal.source_url ? safeUrl(signal.source_url) : null,
      summary: signal.summary,
      confidence: signal.confidence,
    })),
    diligenceNotes: uniqueText(decision.state.diligence_notes),
    errors: uniqueText(decision.state.errors),
  }
}

export function adaptFounderAnalysis(input: unknown): FounderAnalysisModel {
  const result = founderAnalysisDtoSchema.safeParse(input)
  if (!result.success) {
    throw new ApiError('The backend returned an unsupported founder analysis response.', {
      kind: 'validation',
      details: result.error.flatten(),
    })
  }

  const dto = result.data
  const evidenceIndex = createEvidenceIndex(dto.founderProfile.evidence)
  const context = adaptContext(dto)
  const skills = adaptSkills(dto.founderProfile.skills)
  const intelligence = adaptIntelligence(dto.founderIntelligence, evidenceIndex)

  return {
    context,
    overview: {
      context,
      skills,
      counts: {
        experience: dto.founderProfile.experience.length,
        startups: dto.founderProfile.startupHistory.length,
        projects: dto.founderProfile.projects.length,
        research: dto.founderProfile.research.length,
        evidence: dto.founderProfile.evidence.length,
      },
      strengths: intelligence.strengths,
      risks: intelligence.executionRisks,
      missingInformation: intelligence.missingInformation,
    },
    founder: {
      context,
      email: optionalText(dto.founderProfile.founder.email),
      socialFollowers: [
        ['GitHub', dto.founderProfile.socialPresence.githubFollowers],
        ['LinkedIn', dto.founderProfile.socialPresence.linkedinFollowers],
        ['X / Twitter', dto.founderProfile.socialPresence.twitterFollowers],
        ['Hugging Face', dto.founderProfile.socialPresence.huggingfaceFollowers],
      ].map(([label, value]) => ({ label: String(label), value: Number(value) })),
      skills,
      entities: Object.entries(dto.founderProfile.entities)
        .map(([key, values]) => ({ label: titleCase(key), values: uniqueText(values) }))
        .filter((group) => group.values.length > 0),
    },
    career: adaptCareer(dto.founderProfile, evidenceIndex),
    startups: adaptStartups(dto.founderProfile, evidenceIndex),
    projects: adaptProjects(dto.founderProfile, evidenceIndex),
    research: adaptResearch(dto, evidenceIndex),
    evidence: adaptEvidence(dto.founderProfile.evidence, dto.founderProfile.unknowns),
    intelligence,
    investmentMemo: adaptDecision(dto),
  }
}
