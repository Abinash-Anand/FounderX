interface ScoreDisplayProps {
  label: string
  score: number
  description: string
  accent: string
}

export function ScoreDisplay({
  label,
  score,
  description,
  accent,
}: ScoreDisplayProps) {
  const boundedScore = Math.max(0, Math.min(100, score))

  return (
    <article className="score-card">
      <div className="score-card__heading">
        <div>
          <p className="eyebrow">{label}</p>
          <p className="score-card__description">{description}</p>
        </div>
        <strong>{boundedScore}</strong>
      </div>
      <div className="score-track" aria-label={`${label}: ${boundedScore} out of 100`}>
        <span
          className="score-track__fill"
          style={{ width: `${boundedScore}%`, backgroundColor: accent }}
        />
      </div>
    </article>
  )
}

