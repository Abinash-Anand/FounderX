import { fireEvent, render, screen } from '@testing-library/react'

import { ResearchLoadingPanel } from './ResearchLoadingPanel'

describe('ResearchLoadingPanel', () => {
  it('explains the staged workflow and supports cancellation', () => {
    const cancel = vi.fn()
    render(<ResearchLoadingPanel query="Research Ada" onCancel={cancel} />)

    expect(screen.getByRole('heading', { name: 'Researching public sources' })).toBeVisible()
    expect(screen.getByText('“Research Ada”')).toBeVisible()
    expect(screen.getByText(/does not report live stage progress/i)).toBeVisible()

    fireEvent.click(screen.getByRole('button', { name: 'Cancel analysis' }))
    expect(cancel).toHaveBeenCalledOnce()
  })
})
