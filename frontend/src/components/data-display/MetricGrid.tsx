type Metric = {
  label: string
  value: string | number
  detail?: string
}

type Props = {
  metrics: Metric[]
  label: string
}

export function MetricGrid({ metrics, label }: Props) {
  return (
    <dl className="metric-grid" aria-label={label}>
      {metrics.map((metric) => (
        <div key={metric.label}>
          <dt>{metric.label}</dt>
          <dd>{metric.value}</dd>
          {metric.detail ? <p>{metric.detail}</p> : null}
        </div>
      ))}
    </dl>
  )
}
