import { ApiError } from '../errors/ApiError'
import { requestJson } from './restClient'

describe('requestJson', () => {
  it('serializes JSON requests and returns parsed responses', async () => {
    const fetchMock = vi.spyOn(window, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await expect(requestJson('/health', { method: 'POST', body: { query: 'Ada' } })).resolves.toEqual({
      status: 'ok',
    })

    expect(fetchMock).toHaveBeenCalledOnce()
    const [url, init] = fetchMock.mock.calls[0] ?? []
    expect(url).toBe('https://founderx-wwmi.onrender.com/health')
    expect(init?.method).toBe('POST')
    expect(init?.body).toBe(JSON.stringify({ query: 'Ada' }))
    expect(new Headers(init?.headers).get('Content-Type')).toBe('application/json')
  })

  it('normalizes backend errors', async () => {
    vi.spyOn(window, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Integration unavailable' }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await expect(requestJson('/health')).rejects.toEqual(
      expect.objectContaining<Partial<ApiError>>({
        message: 'Integration unavailable',
        kind: 'server',
        status: 503,
        retryable: true,
      }),
    )
  })

  it('preserves multipart bodies without setting a JSON content type', async () => {
    const fetchMock = vi.spyOn(window, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ storage_path: 'deck.pdf' }), { status: 200 }),
    )
    const body = new FormData()
    body.append('file', new File(['deck'], 'deck.pdf'))

    await requestJson('/v1/memos/pitch-deck', { method: 'POST', body })

    const init = fetchMock.mock.calls[0]?.[1]
    expect(init?.body).toBe(body)
    expect(new Headers(init?.headers).has('Content-Type')).toBe(false)
  })
})
