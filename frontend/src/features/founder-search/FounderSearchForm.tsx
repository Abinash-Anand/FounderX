import { useNavigate } from '@tanstack/react-router'
import { useState, type FormEvent } from 'react'

import { ApiError } from '../../api/errors/ApiError'
import { ResearchLoadingPanel } from './ResearchLoadingPanel'
import { useAnalyzeFounder } from './useAnalyzeFounder'

const QUERY_LIMIT = 5_000

function errorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) return 'Founder analysis failed unexpectedly. Please try again.'
  if (error.kind === 'aborted') return 'The analysis was cancelled.'
  if (error.kind === 'timeout') return 'The analysis took too long. Please try again.'
  return error.message
}

export function FounderSearchForm() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [validationError, setValidationError] = useState<string | null>(null)
  const analysis = useAnalyzeFounder()

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const normalized = query.trim()
    if (!normalized) {
      setValidationError('Enter a founder, company, or research question.')
      return
    }
    if (normalized.length > QUERY_LIMIT) {
      setValidationError(`Keep the research request under ${QUERY_LIMIT.toLocaleString()} characters.`)
      return
    }

    setValidationError(null)
    try {
      await analysis.mutateAsync({ query: normalized })
      await navigate({ to: '/results' })
    } catch {
      // Mutation state renders the normalized error without losing the query.
    }
  }

  if (analysis.isPending) {
    return <ResearchLoadingPanel query={query.trim()} onCancel={analysis.cancel} />
  }

  return (
    <form className="founder-search" onSubmit={(event) => void submit(event)} noValidate>
      <label htmlFor="founder-query">Who would you like to understand?</label>
      <div className="founder-search__control">
        <textarea
          id="founder-query"
          name="query"
          value={query}
          maxLength={QUERY_LIMIT}
          rows={3}
          placeholder="e.g. Research the founder of Acme AI and assess their execution history"
          aria-describedby="founder-query-help founder-query-error"
          aria-invalid={Boolean(validationError)}
          onChange={(event) => {
            setQuery(event.target.value)
            if (validationError) setValidationError(null)
            if (analysis.error) analysis.reset()
          }}
        />
        <button className="button button--primary founder-search__submit" type="submit">
          Analyze founder
          <span aria-hidden="true">→</span>
        </button>
      </div>
      <div className="founder-search__meta">
        <p id="founder-query-help">Include the founder, company, and the questions you want investigated.</p>
        <span>{query.length.toLocaleString()} / {QUERY_LIMIT.toLocaleString()}</span>
      </div>
      <p className="form-error" id="founder-query-error" role="alert">
        {validationError ?? (analysis.error ? errorMessage(analysis.error) : '')}
      </p>
      {analysis.error ? (
        <button className="button button--text" type="submit">Try again</button>
      ) : null}
    </form>
  )
}
