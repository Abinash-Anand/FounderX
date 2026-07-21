import { useEffect, useState } from 'react'

const stages = [
  { title: 'Researching public sources', detail: 'Reviewing available founder and company evidence.' },
  { title: 'Structuring the founder profile', detail: 'Organizing career, startup and project information.' },
  { title: 'Generating founder intelligence', detail: 'Connecting assessments to supporting evidence.' },
  { title: 'Building the recommendation', detail: 'Preparing the investment decision workspace.' },
] as const

type Props = {
  query: string
  onCancel: () => void
}

export function ResearchLoadingPanel({ query, onCancel }: Props) {
  const [activeStage, setActiveStage] = useState(0)
  const currentStage = stages[activeStage] ?? stages[0]

  useEffect(() => {
    const interval = window.setInterval(() => {
      setActiveStage((current) => Math.min(current + 1, stages.length - 1))
    }, 6_000)
    return () => window.clearInterval(interval)
  }, [])

  return (
    <section className="analysis-loading" aria-live="polite" aria-labelledby="analysis-loading-title">
      <div className="analysis-loading__orb" aria-hidden="true">
        <span />
      </div>
      <p className="eyebrow">Founder analysis in progress</p>
      <h2 id="analysis-loading-title">{currentStage.title}</h2>
      <p>{currentStage.detail}</p>
      <p className="analysis-loading__query">“{query}”</p>
      <ol className="analysis-stages" aria-label="Analysis stages">
        {stages.map((stage, index) => (
          <li
            className={index === activeStage ? 'is-active' : index < activeStage ? 'is-complete' : ''}
            key={stage.title}
          >
            <span aria-hidden="true">{index < activeStage ? '✓' : index + 1}</span>
            {stage.title}
          </li>
        ))}
      </ol>
      <p className="analysis-loading__note">
        These stages explain the workflow; the backend does not report live stage progress.
      </p>
      <button className="button button--secondary" type="button" onClick={onCancel}>
        Cancel analysis
      </button>
    </section>
  )
}
