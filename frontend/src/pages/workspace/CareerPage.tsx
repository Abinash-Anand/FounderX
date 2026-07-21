import { EvidenceLinks } from '../../components/data-display/EvidenceLinks'
import { SectionCard } from '../../components/data-display/SectionCard'
import { TagList } from '../../components/data-display/TagList'
import { EmptySection } from '../../components/feedback/EmptySection'
import type { CareerItem } from '../../entities/founder/founder.models'
import { useWorkspaceAnalysis } from '../../features/workspace/workspaceContextValue'
import { formatPeriod, formatResearchDate } from '../../utils/date'

function CareerRecord({ item }: { item: CareerItem }) {
  return (
    <article className="career-record">
      <div className="career-record__rail" aria-hidden="true"><span /></div>
      <div className="career-record__content">
        <div className="career-record__heading">
          <div><h3>{item.title ?? item.organization}</h3><p>{item.organization}</p></div>
          <time>{formatPeriod(item.startDate, item.endDate, item.isCurrent)}</time>
        </div>
        {item.location ? <p className="record-meta">{item.location}</p> : null}
        {item.description ? <p>{item.description}</p> : null}
        <TagList items={item.tags} label={`${item.organization} attributes`} />
        <EvidenceLinks evidence={item.evidence} unresolvedEvidenceIds={item.unresolvedEvidenceIds} />
      </div>
    </article>
  )
}

export function CareerPage() {
  const { career } = useWorkspaceAnalysis()
  return (
    <div className="workspace-page">
      <header className="workspace-page__header">
        <p className="eyebrow">Career</p>
        <h1>Experience and education</h1>
        <p>A chronological view of professional roles, education, and notable career events.</p>
      </header>

      <SectionCard title="Professional experience" description={`${career.experience.length} structured record${career.experience.length === 1 ? '' : 's'}`}>
        {career.experience.length > 0 ? (
          <div className="career-timeline">{career.experience.map((item) => <CareerRecord key={item.id} item={item} />)}</div>
        ) : <EmptySection title="No experience records" description="The available sources did not yield structured employment history." />}
      </SectionCard>

      <SectionCard title="Education" description={`${career.education.length} structured record${career.education.length === 1 ? '' : 's'}`}>
        {career.education.length > 0 ? (
          <div className="career-timeline">{career.education.map((item) => <CareerRecord key={item.id} item={item} />)}</div>
        ) : <EmptySection title="No education records" description="No structured education history was returned." />}
      </SectionCard>

      <SectionCard title="Career timeline" description="Additional dated events from the founder profile.">
        {career.timeline.length > 0 ? (
          <ol className="event-timeline">
            {career.timeline.map((item) => (
              <li key={item.id}>
                <time>{formatResearchDate(item.date) ?? 'Date unavailable'}</time>
                <div><h3>{item.title}</h3>{item.relatedEntity ? <p className="record-meta">{item.relatedEntity}</p> : null}{item.description ? <p>{item.description}</p> : null}</div>
                <EvidenceLinks evidence={item.evidence} unresolvedEvidenceIds={item.unresolvedEvidenceIds} />
              </li>
            ))}
          </ol>
        ) : <EmptySection title="No additional timeline events" description="All available career data is represented in the sections above." />}
      </SectionCard>
    </div>
  )
}
