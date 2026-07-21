import { MetricGrid } from '../../components/data-display/MetricGrid'
import { SectionCard } from '../../components/data-display/SectionCard'
import { TagList } from '../../components/data-display/TagList'
import { EmptySection } from '../../components/feedback/EmptySection'
import { useWorkspaceAnalysis } from '../../features/workspace/workspaceContextValue'

export function FounderPage() {
  const { founder } = useWorkspaceAnalysis()
  const { context } = founder

  return (
    <div className="workspace-page">
      <header className="workspace-page__header">
        <p className="eyebrow">Founder profile</p>
        <h1>Identity and capabilities</h1>
        <p>Normalized founder information from the research and structuring pipeline.</p>
      </header>

      <SectionCard title={context.name} description={context.headline ?? 'Professional headline unavailable'} className="identity-panel">
        <div className="identity-panel__content">
          <div>
            <dl className="definition-list">
              <div><dt>Current company</dt><dd>{context.currentCompany ?? 'Unknown'}</dd></div>
              <div><dt>Location</dt><dd>{context.location ?? 'Unknown'}</dd></div>
              <div><dt>Email</dt><dd>{founder.email ?? 'Not available'}</dd></div>
              <div><dt>Profile version</dt><dd>{context.profileVersion}</dd></div>
            </dl>
            {context.bio ? <p className="identity-panel__bio">{context.bio}</p> : null}
          </div>
          <div>
            <h3>Public profiles</h3>
            {context.links.length > 0 ? (
              <ul className="profile-links">
                {context.links.map((link) => <li key={link.href}><a href={link.href} target="_blank" rel="noreferrer">{link.label}<span aria-hidden="true">↗</span></a></li>)}
              </ul>
            ) : <EmptySection title="No public links" description="No valid public profile URLs were returned." />}
          </div>
        </div>
      </SectionCard>

      <MetricGrid
        label="Social presence"
        metrics={founder.socialFollowers.map((item) => ({
          label: `${item.label} followers`, value: item.value.toLocaleString(),
        }))}
      />

      <SectionCard title="Skills" description="Capabilities grouped exactly by the backend profile schema.">
        {founder.skills.length > 0 ? (
          <div className="skill-groups">
            {founder.skills.map((group) => (
              <div key={group.key}><h3>{group.label}</h3><TagList items={group.values} label={group.label} /></div>
            ))}
          </div>
        ) : <EmptySection title="No structured skills" description="No skill categories were populated by the analysis." />}
      </SectionCard>

      <SectionCard title="Known entities" description="Companies, products, people, and technologies connected to the profile.">
        {founder.entities.length > 0 ? (
          <div className="entity-groups">
            {founder.entities.map((group) => (
              <div key={group.label}><h3>{group.label}</h3><TagList items={group.values} label={group.label} /></div>
            ))}
          </div>
        ) : <EmptySection title="No entities extracted" description="The normalized profile did not contain related entities." />}
      </SectionCard>
    </div>
  )
}
