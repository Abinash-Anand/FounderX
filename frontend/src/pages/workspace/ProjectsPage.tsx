import { EvidenceLinks } from '../../components/data-display/EvidenceLinks'
import { MetricGrid } from '../../components/data-display/MetricGrid'
import { SectionCard } from '../../components/data-display/SectionCard'
import { TagList } from '../../components/data-display/TagList'
import { EmptySection } from '../../components/feedback/EmptySection'
import { useWorkspaceAnalysis } from '../../features/workspace/workspaceContextValue'

export function ProjectsPage() {
  const { projects } = useWorkspaceAnalysis()
  return (
    <div className="workspace-page">
      <header className="workspace-page__header">
        <p className="eyebrow">Projects</p>
        <h1>Projects and open source</h1>
        <p>Public work, repositories, and factual open-source activity associated with the founder.</p>
      </header>

      <MetricGrid label="Open-source activity" metrics={[
        { label: 'Repositories', value: projects.openSource.totalRepositories },
        { label: 'Total stars', value: projects.openSource.totalStars.toLocaleString() },
        { label: 'Total forks', value: projects.openSource.totalForks.toLocaleString() },
        { label: 'Organizations', value: projects.openSource.organizations.length },
      ]} />

      <SectionCard title="Featured projects" description="Structured projects returned by the founder profile.">
        {projects.projects.length > 0 ? (
          <div className="card-grid">
            {projects.projects.map((item) => (
              <article className="domain-card" key={item.id}>
                <header><div><p>{item.category ?? 'Project'}</p><h3>{item.name}</h3></div>{item.status ? <span className="status-badge">{item.status}</span> : null}</header>
                {item.description ? <p>{item.description}</p> : null}
                <TagList items={item.technologies} label={`${item.name} technologies`} />
                <ul className="inline-links">{item.links.map((link) => <li key={link.href}><a href={link.href} target="_blank" rel="noreferrer">{link.label} ↗</a></li>)}</ul>
                <EvidenceLinks evidence={item.evidence} unresolvedEvidenceIds={item.unresolvedEvidenceIds} />
              </article>
            ))}
          </div>
        ) : <EmptySection title="No structured projects" description="No project records were returned by the analysis." />}
      </SectionCard>

      <SectionCard title="Repositories" description="Repository counts are factual activity metrics, not investment scores.">
        {projects.repositories.length > 0 ? (
          <div className="table-scroll">
            <table className="data-table">
              <thead><tr><th scope="col">Repository</th><th scope="col">Language</th><th scope="col">Stars</th><th scope="col">Forks</th><th scope="col">Open issues</th></tr></thead>
              <tbody>{projects.repositories.map((item) => (
                <tr key={item.id}>
                  <th scope="row">{item.url ? <a href={item.url} target="_blank" rel="noreferrer">{item.name} ↗</a> : item.name}<span>{item.description}</span></th>
                  <td>{item.primaryLanguage ?? 'Unknown'}</td><td>{item.stars.toLocaleString()}</td><td>{item.forks.toLocaleString()}</td><td>{item.openIssues.toLocaleString()}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : <EmptySection title="No repositories" description="The founder profile contains no repository records." />}
      </SectionCard>
    </div>
  )
}
