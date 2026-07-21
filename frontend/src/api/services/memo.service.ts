import { z } from 'zod'

import { requestJson } from '../client/restClient'
import { ApiError } from '../errors/ApiError'

const storageResponseSchema = z.object({ storage_path: z.string().min(1) })

function parseStoragePath(value: unknown): string {
  const result = storageResponseSchema.safeParse(value)
  if (!result.success) {
    throw new ApiError('The backend returned an invalid storage response.', {
      kind: 'validation',
      details: result.error.flatten(),
    })
  }
  return result.data.storage_path
}

export const memoService = {
  async uploadPitchDeck(file: File, signal?: AbortSignal): Promise<string> {
    const body = new FormData()
    body.append('file', file)
    const response = await requestJson<unknown>('/v1/memos/pitch-deck', {
      method: 'POST',
      body,
      signal,
      timeoutMs: 2 * 60_000,
    })
    return parseStoragePath(response)
  },

  async generateAudio(memoId: string, text: string, signal?: AbortSignal): Promise<string> {
    const response = await requestJson<unknown>(`/v1/memos/${encodeURIComponent(memoId)}/audio`, {
      method: 'POST',
      body: { text },
      signal,
      timeoutMs: 5 * 60_000,
    })
    return parseStoragePath(response)
  },
}
