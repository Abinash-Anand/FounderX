import { Link } from '@tanstack/react-router'
import { useQueryClient } from '@tanstack/react-query'

import type { FounderAnalysisModel } from '../../entities/founder/founderAnalysis.models'
import { founderAnalysisKeys } from '../../features/founder-search/founderAnalysis.keys'
import { ResearchResultCard } from '../../features/results/ResearchResultCard'

export function ResultsPage() {
  const queryClient = useQueryClient()
  const analysis = queryClient.getQueryData<FounderAnalysisModel>(founderAnalysisKeys.active())

  if (!analysis) {
    return (
      <main className="results-empty" id="main-content" aria-labelledby="results-empty-title">
        <p className="eyebrow">Research unavailable</p>
        <h1 id="results-empty-title">Start with a founder search.</h1>
        <p>This browser session does not contain an active founder analysis.</p>
        <Link className="button button--primary" to="/">Return to search</Link>
      </main>
    )
  }

  return (
    <main className="results-page" id="main-content" aria-labelledby="results-title">
      <header className="results-page__header">
        <div>
          <p className="eyebrow">Founder research</p>
          <h1 id="results-title">Your analysis is ready.</h1>
          <p>Review the research snapshot before entering the detailed workspace.</p>
        </div>
        <Link className="button button--secondary" to="/">New research</Link>
      </header>
      <ResearchResultCard analysis={analysis} />
      <div className="results-page__actions">
        <Link className="button button--primary" to="/workspace/overview">Open founder workspace</Link>
      </div>
    </main>
  )
}
