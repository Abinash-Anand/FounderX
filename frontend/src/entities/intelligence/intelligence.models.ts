import type { EvidenceReference } from '../founder/founder.models'

export type IntelligenceInsightModel = {
  insight: string
  reasoning: string | null
  evidence: EvidenceReference[]
  unresolvedEvidenceIds: string[]
}

export type FounderIntelligenceModel = {
  strengths: string[]
  weaknesses: string[]
  executionRisks: string[]
  assessments: Array<{ label: string; value: string }>
  qualitySignals: string[]
  confidenceScores: Array<{ dimension: string; score: number }>
  missingInformation: string[]
  insights: IntelligenceInsightModel[]
}
