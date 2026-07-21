import type { FounderAnalysisModel } from '../../entities/founder/founderAnalysis.models'

type Props = {
  analysis: FounderAnalysisModel
}

function initials(name: string): string {
  return name.split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase()
}

function recommendationLabel(value: string): string {
  return value.replaceAll('_', ' ')
}

export function ResearchResultCard({ analysis }: Props) {
  const { context } = analysis
  const metrics = [
    ['Profile completeness', `${Math.round(context.completenessScore)}%`],
    ['Evidence sources', analysis.overview.counts.evidence.toLocaleString()],
    ['Career records', analysis.overview.counts.experience.toLocaleString()],
    ['Research records', analysis.overview.counts.research.toLocaleString()],
  ] as const

  return (
    <article className="result-card">
      <div className="result-card__identity">
        {context.profileImageUrl ? (
          <img src={context.profileImageUrl} alt="" />
        ) : (
          <div className="result-card__avatar" aria-hidden="true">{initials(context.name)}</div>
        )}
        <div>
          <p className="eyebrow">Analysis complete</p>
          <h2>{context.name}</h2>
          <p>{[context.headline, context.currentCompany, context.location].filter(Boolean).join(' · ')}</p>
        </div>
        <span className="recommendation-badge">{recommendationLabel(context.recommendation)}</span>
      </div>

      <dl className="result-card__metrics">
        {metrics.map(([label, value]) => (
          <div key={label}><dt>{label}</dt><dd>{value}</dd></div>
        ))}
      </dl>

      <div className="result-card__summary">
        <div>
          <h3>Research snapshot</h3>
          <p>{context.bio ?? 'No founder biography was found in the available evidence.'}</p>
        </div>
        <div>
          <h3>Initial intelligence</h3>
          <p>{analysis.intelligence.strengths[0] ?? analysis.intelligence.missingInformation[0] ?? 'Open the workspace to inspect the available evidence.'}</p>
        </div>
      </div>
    </article>
  )
}
