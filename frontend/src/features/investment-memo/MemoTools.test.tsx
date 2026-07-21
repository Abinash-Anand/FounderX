import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'

import { memoService } from '../../api/services/memo.service'
import { AudioMemoGenerator } from './AudioMemoGenerator'
import { PitchDeckUploader } from './PitchDeckUploader'

function renderWithQuery(ui: ReactNode) {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

describe('memo tools', () => {
  it('uploads a selected pitch deck and labels the returned storage path', async () => {
    vi.spyOn(memoService, 'uploadPitchDeck').mockResolvedValue('decks/deck.pdf')
    renderWithQuery(<PitchDeckUploader />)
    const file = new File(['deck'], 'deck.pdf', { type: 'application/pdf' })

    fireEvent.change(screen.getByLabelText(/choose a pitch deck/i), { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Upload deck' }))

    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('decks/deck.pdf'))
    expect(screen.getByText(/not a public download link/i)).toBeVisible()
  })

  it('submits editable narration text and does not promise playback', async () => {
    const generateAudio = vi.spyOn(memoService, 'generateAudio').mockResolvedValue('audio/memo.mp3')
    renderWithQuery(<AudioMemoGenerator memoId="founder-1-v3" initialText="Initial brief" />)

    fireEvent.change(screen.getByLabelText('Narration text'), { target: { value: 'Updated brief' } })
    fireEvent.click(screen.getByRole('button', { name: 'Generate audio' }))

    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('audio/memo.mp3'))
    expect(generateAudio).toHaveBeenCalledWith('founder-1-v3', 'Updated brief', expect.any(AbortSignal))
    expect(screen.getByText(/does not provide a playback URL/i)).toBeVisible()
  })
})
