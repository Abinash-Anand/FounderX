import type { EvidenceDto } from '../dto/founderAnalysis.dto'
import type { EvidencePageModel } from '../../entities/evidence/evidence.models'
import type { EvidenceLinked, EvidenceReference } from '../../entities/founder/founder.models'
import { distinctSorted, optionalText, safeUrl } from './normalization'

export type EvidenceIndex = Map<string, EvidenceReference>

function toReference(evidence: EvidenceDto): EvidenceReference {
  return {
    id: evidence.id,
    title: optionalText(evidence.title) ?? optionalText(evidence.source) ?? 'Untitled evidence',
    source: optionalText(evidence.source),
    url: safeUrl(evidence.url),
    confidence: optionalText(evidence.confidence),
    claimCategory: optionalText(evidence.claimCategory),
    excerpt: optionalText(evidence.excerpt) ?? optionalText(evidence.quote),
  }
}

export function createEvidenceIndex(items: EvidenceDto[]): EvidenceIndex {
  return new Map(items.filter((item) => item.id).map((item) => [item.id, toReference(item)]))
}

export function resolveEvidence(ids: string[], index: EvidenceIndex): EvidenceLinked {
  const evidence: EvidenceReference[] = []
  const unresolvedEvidenceIds: string[] = []

  for (const id of [...new Set(ids.filter(Boolean))]) {
    const item = index.get(id)
    if (item) evidence.push(item)
    else unresolvedEvidenceIds.push(id)
  }

  return { evidence, unresolvedEvidenceIds }
}

export function adaptEvidence(items: EvidenceDto[], unknowns: Array<{
  category: string
  field: string
  reason: string
  importance: string
  priority: string
  recommendedAction: string
  entityType: string
  entityId: string
}>): EvidencePageModel {
  const mapped = items.map((item) => ({
    ...toReference(item),
    type: optionalText(item.type),
    retrievedAt: optionalText(item.retrievedAt),
    publishedAt: optionalText(item.publishedAt),
    supports: item.supports,
    content: optionalText(item.content),
    quote: optionalText(item.quote),
    sourceCategory: optionalText(item.sourceCategory),
    publisherType: optionalText(item.publisherType),
    contentType: optionalText(item.contentType),
  }))

  return {
    items: mapped,
    unknowns: unknowns.map((item) => ({
      category: optionalText(item.category),
      field: optionalText(item.field) ?? 'Unknown field',
      reason: optionalText(item.reason),
      importance: optionalText(item.importance),
      priority: optionalText(item.priority),
      recommendedAction: optionalText(item.recommendedAction),
      entityType: optionalText(item.entityType),
      entityId: optionalText(item.entityId),
    })),
    filters: {
      types: distinctSorted(mapped.map((item) => item.type)),
      confidenceLevels: distinctSorted(mapped.map((item) => item.confidence)),
      claimCategories: distinctSorted(mapped.map((item) => item.claimCategory)),
    },
  }
}
