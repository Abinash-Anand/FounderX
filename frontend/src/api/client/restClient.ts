import { ApiError } from '../errors/ApiError'
import { apiConfig } from './config'

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
  timeoutMs?: number
}

type ErrorPayload = {
  detail?: unknown
}

function errorMessage(payload: ErrorPayload | null, fallback: string): string {
  return typeof payload?.detail === 'string' ? payload.detail : fallback
}

export async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const timeoutController = new AbortController()
  const timeoutId = window.setTimeout(
    () => timeoutController.abort(),
    options.timeoutMs ?? apiConfig.timeoutMs,
  )

  const signal = options.signal
    ? AbortSignal.any([options.signal, timeoutController.signal])
    : timeoutController.signal

  try {
    const isFormData = options.body instanceof FormData
    const requestBody: BodyInit | undefined = options.body === undefined
      ? undefined
      : isFormData
        ? options.body as FormData
        : JSON.stringify(options.body)
    const response = await fetch(`${apiConfig.baseUrl}${path}`, {
      ...options,
      body: requestBody,
      headers: {
        Accept: 'application/json',
        ...(options.body === undefined || isFormData ? {} : { 'Content-Type': 'application/json' }),
        ...options.headers,
      },
      signal,
    })

    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as ErrorPayload | null
      throw new ApiError(errorMessage(payload, `Request failed with status ${response.status}`), {
        kind: response.status === 422 ? 'validation' : response.status >= 500 ? 'server' : 'unknown',
        status: response.status,
        retryable: response.status >= 500,
        details: payload,
      })
    }

    if (response.status === 204) {
      return undefined as T
    }

    return (await response.json()) as T
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      const timedOut = timeoutController.signal.aborted && !options.signal?.aborted
      throw new ApiError(timedOut ? 'The request timed out.' : 'The request was cancelled.', {
        kind: timedOut ? 'timeout' : 'aborted',
        retryable: timedOut,
        cause: error,
      })
    }
    throw new ApiError('FounderX could not reach the backend.', {
      kind: 'network',
      retryable: true,
      cause: error,
    })
  } finally {
    window.clearTimeout(timeoutId)
  }
}
