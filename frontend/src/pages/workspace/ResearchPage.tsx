import { EvidenceLinks } from '../../components/data-display/EvidenceLinks'
import { SectionCard } from '../../components/data-display/SectionCard'
import { TagList } from '../../components/data-display/TagList'
import { EmptySection } from '../../components/feedback/EmptySection'
import type { ResearchItemModel } from '../../entities/research/research.models'
import { useWorkspaceAnalysis } from '../../features/workspace/workspaceContextValue'
import { formatResearchDate } from '../../utils/date'

function ResearchRecord({ item }: { item: ResearchItemModel }) {
  return (
    <article className="research-record">
      <header>
        <div>
          <p>{item.kind}</p>
          <h3>{item.title}</h3>
          {item.subtitle ? <span>{item.subtitle}</span> : null}
        </div>
        {item.date ? <time>{formatResearchDate(item.date)}</time> : null}
      </header>
      {item.description ? <p>{item.description}</p> : null}
      <TagList items={item.tags} label={`${item.title} topics`} />
      {item.links.length > 0 ? (
        <ul className="inline-links">
          {item.links.map((link) => <li key={link.href}><a href={link.href} target="_blank" rel="noreferrer">{link.label} ↗</a></li>)}
        </ul>
      ) : null}
      <EvidenceLinks evidence={item.evidence} unresolvedEvidenceIds={item.unresolvedEvidenceIds} />
    </article>
  )
}

function ResearchCollection({ items, emptyTitle, emptyDescription }: {
  items: ResearchItemModel[]
  emptyTitle: string
  emptyDescription: string
}) {
  return items.length > 0 ? (
    <div className="research-record-list">{items.map((item) => <ResearchRecord key={`${item.kind}-${item.id}`} item={item} />)}</div>
  ) : <EmptySection title={emptyTitle} description={emptyDescription} />
}

export function ResearchPage() {
  const { research } = useWorkspaceAnalysis()

  return (
    <div className="workspace-page">
      <header className="workspace-page__header">
        <p className="eyebrow">Research</p>
        <h1>Sources and public activity</h1>
        <p>Raw web-research summaries and normalized public work collected during founder analysis.</p>
      </header>

      <SectionCard title="Research queries" description={`${research.searches.length} web search${research.searches.length === 1 ? '' : 'es'} returned by the research pipeline.`}>
        {research.searches.length > 0 ? (
          <div className="research-queries">
            {research.searches.map((search, index) => (
              <details key={`${search.query}-${index}`} open={index === 0}>
                <summary><span>{search.query}</span><small>{search.sources.length} sources</small></summary>
                <div className="research-query__content">
                  {search.answer ? <p>{search.answer}</p> : null}
                  {search.sources.length > 0 ? (
                    <ol>{search.sources.map((source, sourceIndex) => (
                      <li key={`${source.url ?? source.title}-${sourceIndex}`}>
                        <div>
                          {source.url ? <a href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a> : <strong>{source.title}</strong>}
                          {source.content ? <p>{source.content}</p> : null}
                        </div>
                        {source.score !== null ? <span>{Math.round(source.score * 100)}% relevance</span> : null}
                      </li>
                    ))}</ol>
                  ) : <EmptySection title="No sources returned" description="This query contains no source records." />}
                </div>
              </details>
            ))}
          </div>
        ) : <EmptySection title="No research queries" description="The response did not contain inspectable Tavily searches." />}
      </SectionCard>

      <SectionCard title="Publications" description="Academic and technical publications attributed by the backend profile.">
        <ResearchCollection items={research.publications} emptyTitle="No publications found" emptyDescription="No structured publication records were returned." />
      </SectionCard>

      <SectionCard title="Speaking and appearances" description="Conference talks and public speaking records.">
        <ResearchCollection items={research.speaking} emptyTitle="No speaking records found" emptyDescription="No public-speaking records were identified." />
      </SectionCard>

      <SectionCard title="Recognition" description="Awards, grants, and patents connected to the founder.">
        <ResearchCollection items={research.recognition} emptyTitle="No recognition records found" emptyDescription="The profile contains no awards, grants, or patents." />
      </SectionCard>

      <SectionCard title="Community and media" description="Blogs, interviews, podcasts, newsletters, and news mentions.">
        <ResearchCollection items={research.community} emptyTitle="No community records found" emptyDescription="No community or media records were returned." />
      </SectionCard>
    </div>
  )
}
