import { MetricGrid } from '../../components/data-display/MetricGrid'
import { SectionCard } from '../../components/data-display/SectionCard'
import { TagList } from '../../components/data-display/TagList'
import { EmptySection } from '../../components/feedback/EmptySection'
import { useWorkspaceAnalysis } from '../../features/workspace/workspaceContextValue'

export function OverviewPage() {
  const { overview, context, investmentMemo } = useWorkspaceAnalysis()

  return (
    <div className="workspace-page">
      <header className="workspace-page__hero">
        <div>
          <p className="eyebrow">Workspace overview</p>
          <h1>{context.name}</h1>
          <p>{context.bio ?? 'No founder biography was available in the collected evidence.'}</p>
        </div>
        <div className="decision-summary">
          <span>Investment recommendation</span>
          <strong>{investmentMemo.recommendation.replaceAll('_', ' ')}</strong>
          <p>{investmentMemo.companyName}</p>
        </div>
      </header>

      <MetricGrid
        label="Founder research summary"
        metrics={[
          { label: 'Profile completeness', value: `${Math.round(context.completenessScore)}%` },
          { label: 'Evidence sources', value: overview.counts.evidence },
          { label: 'Career records', value: overview.counts.experience },
          { label: 'Startup records', value: overview.counts.startups },
          { label: 'Projects', value: overview.counts.projects },
          { label: 'Research records', value: overview.counts.research },
        ]}
      />

      <div className="workspace-page__two-column">
        <SectionCard title="Founder strengths" description="Evidence-grounded signals returned by the intelligence pipeline.">
          {overview.strengths.length > 0 ? (
            <ul className="insight-list insight-list--positive">
              {overview.strengths.map((item) => <li key={item}>{item}</li>)}
            </ul>
          ) : <EmptySection title="No strengths returned" description="The analysis did not identify supported strength signals." />}
        </SectionCard>
        <SectionCard title="Execution risks" description="Risks requiring investor review or additional diligence.">
          {overview.risks.length > 0 ? (
            <ul className="insight-list insight-list--risk">
              {overview.risks.map((item) => <li key={item}>{item}</li>)}
            </ul>
          ) : <EmptySection title="No execution risks returned" description="The analysis did not return an execution-risk assessment." />}
        </SectionCard>
      </div>

      <SectionCard title="Capability map" description="Non-empty skill categories extracted from the founder profile.">
        {overview.skills.length > 0 ? (
          <div className="skill-groups">
            {overview.skills.map((group) => (
              <div key={group.key}>
                <h3>{group.label}</h3>
                <TagList items={group.values} label={`${group.label} skills`} />
              </div>
            ))}
          </div>
        ) : <EmptySection title="No skills available" description="The available sources did not provide structured skills." />}
      </SectionCard>

      {overview.missingInformation.length > 0 ? (
        <SectionCard title="Information gaps" description="Unknown information that may affect confidence in the assessment.">
          <ul className="plain-list">
            {overview.missingInformation.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </SectionCard>
      ) : null}
    </div>
  )
}
