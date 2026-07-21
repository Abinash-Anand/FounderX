export type DecisionSignalModel = {
  sourceUrl: string | null
  summary: string
  confidence: number
}

export type InvestmentMemoModel = {
  companyName: string
  recommendation: string
  thesis: string | null
  sourceUrls: string[]
  scores: Array<{ dimension: string; score: number }>
  signals: DecisionSignalModel[]
  diligenceNotes: string[]
  errors: string[]
}
