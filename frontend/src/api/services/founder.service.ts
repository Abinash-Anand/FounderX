import { adaptFounderAnalysis } from '../adapters/founderAnalysis.adapter'
import { requestJson } from '../client/restClient'
import type { FounderAnalysisModel } from '../../entities/founder/founderAnalysis.models'

const ANALYSIS_TIMEOUT_MS = 5 * 60_000

export const founderService = {
  async analyze(query: string, signal?: AbortSignal): Promise<FounderAnalysisModel> {
    const response = await requestJson<unknown>('/v1/founders/analyze', {
      method: 'POST',
      body: { query },
      signal,
      timeoutMs: ANALYSIS_TIMEOUT_MS,
    })

    return adaptFounderAnalysis(response)
  },
}
