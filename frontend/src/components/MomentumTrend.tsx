const points = [22, 29, 27, 41, 48, 62, 67, 81, 86]
const chartPoints = points
  .map((point, index) => `${index * 50},${100 - point}`)
  .join(' ')

export function MomentumTrend() {
  return (
    <article className="panel momentum-panel">
      <div className="panel__heading">
        <div>
          <p className="eyebrow">Momentum</p>
          <h2>Signal acceleration</h2>
        </div>
        <span className="trend-pill">+31% / 30d</span>
      </div>
      <svg
        className="momentum-chart"
        viewBox="0 0 400 110"
        role="img"
        aria-label="Momentum trend rising over the last thirty days"
      >
        <defs>
          <linearGradient id="momentum-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#d6ff5f" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#d6ff5f" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={`0,110 ${chartPoints} 400,110`} fill="url(#momentum-fill)" />
        <polyline points={chartPoints} fill="none" stroke="#d6ff5f" strokeWidth="3" />
      </svg>
      <div className="chart-labels" aria-hidden="true">
        <span>30 days ago</span>
        <span>Today</span>
      </div>
    </article>
  )
}

