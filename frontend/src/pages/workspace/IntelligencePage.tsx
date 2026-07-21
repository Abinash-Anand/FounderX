import { EvidenceLinks } from '../../components/data-display/EvidenceLinks'
import { SectionCard } from '../../components/data-display/SectionCard'
import { EmptySection } from '../../components/feedback/EmptySection'
import { useWorkspaceAnalysis } from '../../features/workspace/workspaceContextValue'

function confidencePercent(score: number): number {
  const normalized = score <= 1 ? score * 100 : score
  return Math.round(Math.min(100, Math.max(0, normalized)))
}

export function IntelligencePage() {
  const { intelligence } = useWorkspaceAnalysis()

  return (
    <div className="workspace-page">
      <header className="workspace-page__header">
        <p className="eyebrow">Founder intelligence</p>
        <h1>Evidence-grounded assessment</h1>
        <p>Backend-generated assessments are presented with their confidence, reasoning, and supporting evidence.</p>
      </header>

      <div className="workspace-page__three-column">
        <SectionCard title="Strengths">
          {intelligence.strengths.length > 0 ? <ul className="insight-list insight-list--positive">{intelligence.strengths.map((item) => <li key={item}>{item}</li>)}</ul> : <EmptySection title="No strengths returned" description="No supported strengths were generated." />}
        </SectionCard>
        <SectionCard title="Weaknesses">
          {intelligence.weaknesses.length > 0 ? <ul className="insight-list insight-list--risk">{intelligence.weaknesses.map((item) => <li key={item}>{item}</li>)}</ul> : <EmptySection title="No weaknesses returned" description="The analysis returned no structured weaknesses." />}
        </SectionCard>
        <SectionCard title="Execution risks">
          {intelligence.executionRisks.length > 0 ? <ul className="insight-list insight-list--risk">{intelligence.executionRisks.map((item) => <li key={item}>{item}</li>)}</ul> : <EmptySection title="No execution risks returned" description="The analysis returned no structured execution risks." />}
        </SectionCard>
      </div>

      <SectionCard title="Assessment narrative" description="Separate qualitative assessments produced by the founder-intelligence layer.">
        {intelligence.assessments.length > 0 ? (
          <div className="assessment-grid">{intelligence.assessments.map((item) => <article key={item.label}><h3>{item.label}</h3><p>{item.value}</p></article>)}</div>
        ) : <EmptySection title="No narrative assessments" description="No leadership, technical-depth, or market-credibility narrative was returned." />}
      </SectionCard>

      <SectionCard title="Confidence" description="Confidence is reported by the backend; it is not recalculated by the frontend.">
        {intelligence.confidenceScores.length > 0 ? (
          <div className="confidence-list">{intelligence.confidenceScores.map((item) => {
            const percent = confidencePercent(item.score)
            return <div key={item.dimension}><div><span>{item.dimension}</span><strong>{percent}%</strong></div><progress max="100" value={percent}>{percent}%</progress></div>
          })}</div>
        ) : <EmptySection title="No confidence scores" description="The backend returned no confidence dimensions." />}
      </SectionCard>

      <SectionCard title="Founder quality signals" description="Signals returned by the intelligence model without frontend scoring.">
        {intelligence.qualitySignals.length > 0 ? <ul className="plain-list">{intelligence.qualitySignals.map((item) => <li key={item}>{item}</li>)}</ul> : <EmptySection title="No quality signals" description="No structured founder-quality signals were returned." />}
      </SectionCard>

      <SectionCard title="Insight reasoning" description="Each insight connects model reasoning to available evidence references.">
        {intelligence.insights.length > 0 ? (
          <div className="reasoning-list">{intelligence.insights.map((item, index) => (
            <article key={`${item.insight}-${index}`}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <div><h3>{item.insight}</h3><p>{item.reasoning ?? 'No reasoning text was returned for this insight.'}</p><EvidenceLinks evidence={item.evidence} unresolvedEvidenceIds={item.unresolvedEvidenceIds} /></div>
            </article>
          ))}</div>
        ) : <EmptySection title="No linked reasoning" description="The intelligence response contains no evidence-reference entries." />}
      </SectionCard>

      <SectionCard title="Missing information" description="Information gaps explicitly identified by the intelligence model.">
        {intelligence.missingInformation.length > 0 ? <ul className="plain-list">{intelligence.missingInformation.map((item) => <li key={item}>{item}</li>)}</ul> : <EmptySection title="No missing information returned" description="The model did not provide a missing-information list." />}
      </SectionCard>
    </div>
  )
}
