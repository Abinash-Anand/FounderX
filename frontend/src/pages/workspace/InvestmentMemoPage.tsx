import { MetricGrid } from '../../components/data-display/MetricGrid'
import { SectionCard } from '../../components/data-display/SectionCard'
import { EmptySection } from '../../components/feedback/EmptySection'
import { AudioMemoGenerator } from '../../features/investment-memo/AudioMemoGenerator'
import { buildMemoNarrationText } from '../../features/investment-memo/memoText'
import { PitchDeckUploader } from '../../features/investment-memo/PitchDeckUploader'
import { useWorkspaceAnalysis } from '../../features/workspace/workspaceContextValue'

function scoreLabel(value: string): string {
  return value.replaceAll('_', ' ')
}

export function InvestmentMemoPage() {
  const analysis = useWorkspaceAnalysis()
  const { investmentMemo, intelligence, context } = analysis
  const memoReference = `${context.id}-v${context.profileVersion}`

  return (
    <div className="workspace-page">
      <header className="memo-hero">
        <div>
          <p className="eyebrow">Investment memo</p>
          <h1>{investmentMemo.companyName}</h1>
          <p>{investmentMemo.thesis ?? 'No investment thesis was returned by the decision workflow.'}</p>
        </div>
        <div className="memo-recommendation"><span>Recommendation</span><strong>{scoreLabel(investmentMemo.recommendation)}</strong><small>Backend decision</small></div>
      </header>

      {investmentMemo.scores.length > 0 ? (
        <MetricGrid label="Decision scores" metrics={investmentMemo.scores.map((item) => ({ label: scoreLabel(item.dimension), value: item.score }))} />
      ) : <EmptySection title="No decision scores" description="The decision workflow did not return scoring dimensions." />}

      <div className="workspace-page__two-column">
        <SectionCard title="Investment strengths" description="Founder strengths included from the intelligence result.">
          {intelligence.strengths.length > 0 ? <ul className="insight-list insight-list--positive">{intelligence.strengths.map((item) => <li key={item}>{item}</li>)}</ul> : <EmptySection title="No strengths returned" description="No supported strengths were returned." />}
        </SectionCard>
        <SectionCard title="Risks and weaknesses" description="Execution risks and weaknesses requiring review.">
          {[...intelligence.executionRisks, ...intelligence.weaknesses].length > 0 ? <ul className="insight-list insight-list--risk">{[...intelligence.executionRisks, ...intelligence.weaknesses].map((item) => <li key={item}>{item}</li>)}</ul> : <EmptySection title="No risks returned" description="No structured risks or weaknesses were returned." />}
        </SectionCard>
      </div>

      <SectionCard title="Diligence notes" description="Actions defined by the backend decision workflow.">
        {investmentMemo.diligenceNotes.length > 0 ? <ol className="diligence-list">{investmentMemo.diligenceNotes.map((item, index) => <li key={`${item}-${index}`}><span>{String(index + 1).padStart(2, '0')}</span><p>{item}</p></li>)}</ol> : <EmptySection title="No diligence notes" description="The decision state did not include diligence notes." />}
      </SectionCard>

      <SectionCard title="Decision signals" description="Deduplicated signals passed into the backend scoring workflow.">
        {investmentMemo.signals.length > 0 ? <div className="decision-signals">{investmentMemo.signals.map((signal, index) => <article key={`${signal.sourceUrl ?? signal.summary}-${index}`}><div><span>{Math.round(signal.confidence * 100)}% confidence</span><p>{signal.summary}</p></div>{signal.sourceUrl ? <a href={signal.sourceUrl} target="_blank" rel="noreferrer">Source ↗</a> : null}</article>)}</div> : <EmptySection title="No decision signals" description="The decision state contains no reduced sourcing signals." />}
      </SectionCard>

      {investmentMemo.errors.length > 0 ? <SectionCard title="Decision workflow errors"><ul className="plain-list">{investmentMemo.errors.map((item) => <li key={item}>{item}</li>)}</ul></SectionCard> : null}

      <SectionCard title="Memo tools" description="Current backend-supported media operations. Stored files cannot be retrieved through the existing API.">
        <div className="memo-tools">
          <PitchDeckUploader />
          <AudioMemoGenerator memoId={memoReference} initialText={buildMemoNarrationText(analysis)} />
        </div>
      </SectionCard>
    </div>
  )
}
