import { requestJson } from '../client/restClient'
import { memoService } from './memo.service'

vi.mock('../client/restClient', () => ({ requestJson: vi.fn() }))

describe('memoService', () => {
  it('uploads a pitch deck as multipart data', async () => {
    vi.mocked(requestJson).mockResolvedValue({ storage_path: 'decks/deck.pdf' })
    const file = new File(['deck'], 'deck.pdf', { type: 'application/pdf' })

    await expect(memoService.uploadPitchDeck(file)).resolves.toBe('decks/deck.pdf')
    const [path, options] = vi.mocked(requestJson).mock.calls[0] ?? []
    expect(path).toBe('/v1/memos/pitch-deck')
    expect(options?.method).toBe('POST')
    expect(options?.body).toBeInstanceOf(FormData)
  })

  it('encodes the memo reference and submits narration text', async () => {
    vi.mocked(requestJson).mockResolvedValue({ storage_path: 'audio/memo.mp3' })

    await expect(memoService.generateAudio('founder/1', 'Investment brief')).resolves.toBe('audio/memo.mp3')
    expect(requestJson).toHaveBeenCalledWith('/v1/memos/founder%2F1/audio', expect.objectContaining({
      method: 'POST', body: { text: 'Investment brief' },
    }))
  })
})
