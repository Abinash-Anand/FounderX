import type { EvidenceReference } from '../founder/founder.models'

export type EvidenceModel = EvidenceReference & {
  type: string | null
  retrievedAt: string | null
  publishedAt: string | null
  supports: string[]
  content: string | null
  quote: string | null
  sourceCategory: string | null
  publisherType: string | null
  contentType: string | null
}

export type UnknownInformationModel = {
  category: string | null
  field: string
  reason: string | null
  importance: string | null
  priority: string | null
  recommendedAction: string | null
  entityType: string | null
  entityId: string | null
}

export type EvidencePageModel = {
  items: EvidenceModel[]
  unknowns: UnknownInformationModel[]
  filters: {
    types: string[]
    confidenceLevels: string[]
    claimCategories: string[]
  }
}
