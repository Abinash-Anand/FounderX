import { EvidenceLinks } from '../../components/data-display/EvidenceLinks'
import { SectionCard } from '../../components/data-display/SectionCard'
import { TagList } from '../../components/data-display/TagList'
import { EmptySection } from '../../components/feedback/EmptySection'
import { useWorkspaceAnalysis } from '../../features/workspace/workspaceContextValue'
import { formatPeriod, formatResearchDate } from '../../utils/date'

export function StartupsPage() {
  const { startups } = useWorkspaceAnalysis()
  return (
    <div className="workspace-page">
      <header className="workspace-page__header">
        <p className="eyebrow">Startups</p>
        <h1>Companies and launches</h1>
        <p>Startup roles, funding context, and product launches found in the founder profile.</p>
      </header>

      <SectionCard title="Startup history" description="A company record does not imply founder status unless the returned role says so.">
        {startups.startups.length > 0 ? (
          <div className="card-grid">
            {startups.startups.map((item) => (
              <article className="domain-card" key={item.id}>
                <header>
                  <div><p>{item.stage ?? item.industry ?? 'Company'}</p><h3>{item.company}</h3></div>
                  {item.status ? <span className="status-badge">{item.status}</span> : null}
                </header>
                <dl className="definition-list definition-list--compact">
                  <div><dt>Role</dt><dd>{item.role ?? 'Unknown'}</dd></div>
                  <div><dt>Period</dt><dd>{formatPeriod(item.period.start, item.period.end)}</dd></div>
                  <div><dt>Funding</dt><dd>{[item.funding.raised, item.funding.currency, item.funding.round].filter(Boolean).join(' · ') || 'Not available'}</dd></div>
                </dl>
                {item.description ? <p>{item.description}</p> : null}
                <TagList items={item.funding.investors} label={`${item.company} investors`} />
                <div className="domain-card__footer">
                  {item.website ? <a href={item.website} target="_blank" rel="noreferrer">Company website ↗</a> : <span />}
                  <EvidenceLinks evidence={item.evidence} unresolvedEvidenceIds={item.unresolvedEvidenceIds} />
                </div>
              </article>
            ))}
          </div>
        ) : <EmptySection title="No startup history" description="The analysis did not return structured startup records." />}
      </SectionCard>

      <SectionCard title="Product launches" description="Products explicitly returned by the profile-generation stage.">
        {startups.productLaunches.length > 0 ? (
          <div className="card-grid">
            {startups.productLaunches.map((item) => (
              <article className="domain-card" key={item.id}>
                <header><div><p>{formatResearchDate(item.launchDate) ?? 'Launch date unavailable'}</p><h3>{item.name}</h3></div>{item.status ? <span className="status-badge">{item.status}</span> : null}</header>
                {item.description ? <p>{item.description}</p> : null}
                <ul className="inline-links">{item.links.map((link) => <li key={link.href}><a href={link.href} target="_blank" rel="noreferrer">{link.label} ↗</a></li>)}</ul>
                <EvidenceLinks evidence={item.evidence} unresolvedEvidenceIds={item.unresolvedEvidenceIds} />
              </article>
            ))}
          </div>
        ) : <EmptySection title="No product launches" description="No launch records were identified in the available evidence." />}
      </SectionCard>
    </div>
  )
}
