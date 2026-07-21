import { useMemo, useState } from 'react'

import { EmptySection } from '../../components/feedback/EmptySection'
import type { EvidenceModel } from '../../entities/evidence/evidence.models'
import { useWorkspaceAnalysis } from '../../features/workspace/workspaceContextValue'
import { formatResearchDate } from '../../utils/date'

const ALL = 'all'

function EvidenceCard({ item }: { item: EvidenceModel }) {
  return (
    <article className="evidence-card" id={item.id}>
      <header>
        <div>
          <div className="evidence-card__badges">
            {item.type ? <span>{item.type}</span> : null}
            {item.confidence ? <span>{item.confidence} confidence</span> : null}
            {item.claimCategory ? <span>{item.claimCategory}</span> : null}
          </div>
          <h2>{item.title}</h2>
          <p>{item.source ?? 'Unknown source'}</p>
        </div>
        {item.url ? <a href={item.url} target="_blank" rel="noreferrer">Open source ↗</a> : null}
      </header>
      {item.quote ? <blockquote>“{item.quote}”</blockquote> : null}
      {item.excerpt ? <p className="evidence-card__excerpt">{item.excerpt}</p> : null}
      {!item.quote && !item.excerpt && item.content ? <p className="evidence-card__excerpt">{item.content}</p> : null}
      <dl>
        <div><dt>Published</dt><dd>{formatResearchDate(item.publishedAt) ?? 'Unknown'}</dd></div>
        <div><dt>Retrieved</dt><dd>{formatResearchDate(item.retrievedAt) ?? 'Unknown'}</dd></div>
        <div><dt>Publisher</dt><dd>{item.publisherType ?? 'Unknown'}</dd></div>
        <div><dt>Content type</dt><dd>{item.contentType ?? 'Unknown'}</dd></div>
      </dl>
      {item.supports.length > 0 ? <p className="evidence-card__supports"><strong>Supports:</strong> {item.supports.join(', ')}</p> : null}
    </article>
  )
}

export function EvidencePage() {
  const { evidence } = useWorkspaceAnalysis()
  const [type, setType] = useState(ALL)
  const [confidence, setConfidence] = useState(ALL)
  const [category, setCategory] = useState(ALL)

  const filtered = useMemo(() => evidence.items.filter((item) =>
    (type === ALL || item.type === type) &&
    (confidence === ALL || item.confidence === confidence) &&
    (category === ALL || item.claimCategory === category),
  ), [category, confidence, evidence.items, type])

  return (
    <div className="workspace-page">
      <header className="workspace-page__header">
        <p className="eyebrow">Evidence</p>
        <h1>Evidence registry</h1>
        <p>Inspect the normalized sources supporting founder claims, intelligence, and research gaps.</p>
      </header>

      <div className="evidence-toolbar">
        <label>Type<select value={type} onChange={(event) => setType(event.target.value)}><option value={ALL}>All types</option>{evidence.filters.types.map((value) => <option key={value}>{value}</option>)}</select></label>
        <label>Confidence<select value={confidence} onChange={(event) => setConfidence(event.target.value)}><option value={ALL}>All confidence</option>{evidence.filters.confidenceLevels.map((value) => <option key={value}>{value}</option>)}</select></label>
        <label>Claim category<select value={category} onChange={(event) => setCategory(event.target.value)}><option value={ALL}>All categories</option>{evidence.filters.claimCategories.map((value) => <option key={value}>{value}</option>)}</select></label>
        <p aria-live="polite">Showing {filtered.length} of {evidence.items.length}</p>
      </div>

      {filtered.length > 0 ? <div className="evidence-grid">{filtered.map((item) => <EvidenceCard key={item.id} item={item} />)}</div> : (
        <EmptySection title="No evidence matches these filters" description="Change or clear one of the evidence filters." />
      )}

      <section className="research-gaps" aria-labelledby="research-gaps-title">
        <header><div><p className="eyebrow">Unknown information</p><h2 id="research-gaps-title">Research gaps</h2></div><span>{evidence.unknowns.length}</span></header>
        {evidence.unknowns.length > 0 ? (
          <div className="research-gaps__list">{evidence.unknowns.map((item, index) => (
            <article key={`${item.field}-${index}`}>
              <div><span>{item.priority ?? 'Unprioritized'}</span><h3>{item.field}</h3></div>
              <p>{item.reason ?? 'No reason was supplied.'}</p>
              {item.recommendedAction ? <p><strong>Recommended action:</strong> {item.recommendedAction}</p> : null}
            </article>
          ))}</div>
        ) : <EmptySection title="No structured research gaps" description="The profile did not return unknown-information records." />}
      </section>
    </div>
  )
}
