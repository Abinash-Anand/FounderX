import type { ReactNode } from 'react'

type Metric = {
  label: string
  value: number | string
}

type Props = {
  eyebrow: string
  title: string
  description: string
  metrics: Metric[]
  children?: ReactNode
}

export function WorkspaceSectionSummary({ eyebrow, title, description, metrics, children }: Props) {
  return (
    <section className="workspace-section" aria-labelledby="workspace-section-title">
      <header className="workspace-section__header">
        <p className="eyebrow">{eyebrow}</p>
        <h1 id="workspace-section-title">{title}</h1>
        <p>{description}</p>
      </header>
      {metrics.length > 0 ? (
        <dl className="workspace-section__metrics">
          {metrics.map((metric) => (
            <div key={metric.label}>
              <dt>{metric.label}</dt>
              <dd>{metric.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      {children}
    </section>
  )
}
