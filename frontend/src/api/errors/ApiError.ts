export type ApiErrorKind =
  | 'aborted'
  | 'network'
  | 'timeout'
  | 'validation'
  | 'server'
  | 'unknown'

type ApiErrorOptions = {
  kind: ApiErrorKind
  status?: number
  retryable?: boolean
  details?: unknown
  cause?: unknown
}

export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status?: number
  readonly retryable: boolean
  readonly details?: unknown

  constructor(message: string, options: ApiErrorOptions) {
    super(message, { cause: options.cause })
    this.name = 'ApiError'
    this.kind = options.kind
    this.status = options.status
    this.retryable = options.retryable ?? false
    this.details = options.details
  }
}
