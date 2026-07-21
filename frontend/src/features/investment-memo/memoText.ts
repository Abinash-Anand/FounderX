import type { FounderAnalysisModel } from '../../entities/founder/founderAnalysis.models'

export function buildMemoNarrationText(analysis: FounderAnalysisModel): string {
  const { context, intelligence, investmentMemo } = analysis
  const sections = [
    `Investment brief for ${investmentMemo.companyName}.`,
    `Founder: ${context.name}${context.headline ? `, ${context.headline}` : ''}.`,
    investmentMemo.thesis ? `Research thesis: ${investmentMemo.thesis}` : '',
    `Recommendation: ${investmentMemo.recommendation.replaceAll('_', ' ')}.`,
    intelligence.strengths.length > 0 ? `Strengths: ${intelligence.strengths.join('; ')}.` : '',
    intelligence.executionRisks.length > 0 ? `Execution risks: ${intelligence.executionRisks.join('; ')}.` : '',
    investmentMemo.diligenceNotes.length > 0 ? `Diligence notes: ${investmentMemo.diligenceNotes.join('; ')}.` : '',
    intelligence.missingInformation.length > 0 ? `Missing information: ${intelligence.missingInformation.join('; ')}.` : '',
  ]
  return sections.filter(Boolean).join('\n\n')
}
