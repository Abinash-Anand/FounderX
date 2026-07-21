import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'

import { adaptFounderAnalysis } from '../api/adapters/founderAnalysis.adapter'
import { founderService } from '../api/services/founder.service'
import { createFounderAnalysisFixture } from '../test/fixtures/founderAnalysis.fixture'
import { App } from './App'
import { queryClient } from './query-client/queryClient'
import { founderAnalysisKeys } from '../features/founder-search/founderAnalysis.keys'
import type { FounderAnalysisModel } from '../entities/founder/founderAnalysis.models'

describe('App', () => {
  beforeEach(async () => {
    queryClient.clear()
    window.history.pushState({}, '', '/')
    await import('./router/router').then(({ router }) => router.navigate({ to: '/' }))
  })

  it('renders the founder research landing route', async () => {
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Know the founder behind the company.' })).toBeVisible()
    expect(screen.getByRole('link', { name: 'FounderX home' })).toHaveAttribute('href', '/')
  })

  it('validates an empty founder query', async () => {
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: /analyze founder/i }))

    expect(screen.getByRole('alert')).toHaveTextContent('Enter a founder')
  })

  it('analyzes a founder and navigates to results', async () => {
    vi.spyOn(founderService, 'analyze').mockResolvedValue(
      adaptFounderAnalysis(createFounderAnalysisFixture()),
    )
    render(<App />)

    fireEvent.change(await screen.findByLabelText('Who would you like to understand?'), {
      target: { value: 'Research Ada Founder at Acme' },
    })
    fireEvent.click(screen.getByRole('button', { name: /analyze founder/i }))

    await waitFor(() => expect(screen.getByRole('heading', { name: 'Your analysis is ready.' })).toBeVisible())
    expect(screen.getByRole('heading', { name: 'Ada Founder' })).toBeVisible()
  })

  it('renders a guarded workspace and navigates between sections', async () => {
    queryClient.setQueryData<FounderAnalysisModel>(
      founderAnalysisKeys.active(),
      adaptFounderAnalysis(createFounderAnalysisFixture()),
    )
    await import('./router/router').then(({ router }) => router.navigate({ to: '/workspace/overview' }))
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Ada Founder' })).toBeVisible()
    const careerLinks = screen.getAllByRole('link', { name: 'Career' })
    fireEvent.click(careerLinks[0]!)
    expect(await screen.findByRole('heading', { name: 'Experience and education' })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Founder' })).toBeVisible()
    expect(screen.getByRole('link', { name: 'Founder profile' })).toHaveAttribute('href', '/workspace/evidence#ev-1')
    expect(screen.getAllByRole('link', { name: 'Career' })[0]).toHaveAttribute('aria-current', 'page')
  })

  it('renders explicit empty states for absent startup data', async () => {
    queryClient.setQueryData<FounderAnalysisModel>(
      founderAnalysisKeys.active(),
      adaptFounderAnalysis(createFounderAnalysisFixture()),
    )
    await import('./router/router').then(({ router }) => router.navigate({ to: '/workspace/startups' }))
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Companies and launches' })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'No startup history' })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'No product launches' })).toBeVisible()
  })

  it('renders research, filters evidence, and links intelligence reasoning', async () => {
    const fixture = createFounderAnalysisFixture()
    fixture.founderProfile.evidence.push({
      ...fixture.founderProfile.evidence[0]!,
      id: 'ev-2',
      type: 'article',
      title: 'Independent article',
      confidence: 'medium',
      claimCategory: 'Market',
    })
    queryClient.setQueryData<FounderAnalysisModel>(
      founderAnalysisKeys.active(),
      adaptFounderAnalysis(fixture),
    )
    const { router } = await import('./router/router')
    await router.navigate({ to: '/workspace/research' })
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Sources and public activity' })).toBeVisible()
    expect(screen.getByText('Ada founded Acme.')).toBeVisible()

    await act(async () => router.navigate({ to: '/workspace/evidence' }))
    expect(await screen.findByRole('heading', { name: 'Evidence registry' })).toBeVisible()
    expect(screen.getByText('Showing 2 of 2')).toBeVisible()
    fireEvent.change(screen.getByLabelText('Type'), { target: { value: 'profile' } })
    expect(screen.getByText('Showing 1 of 2')).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Research gaps' })).toBeVisible()

    await act(async () => router.navigate({ to: '/workspace/intelligence' }))
    expect(await screen.findByRole('heading', { name: 'Evidence-grounded assessment' })).toBeVisible()
    expect(screen.getByRole('progressbar')).toHaveAttribute('value', '82')
    expect(screen.getByText('Supported by public work.')).toBeVisible()
    expect(screen.getByRole('link', { name: 'Founder profile' })).toHaveAttribute('href', '/workspace/evidence#ev-1')

    await act(async () => router.navigate({ to: '/workspace/memo' }))
    expect(await screen.findByRole('heading', { name: 'Acme', level: 1 })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Diligence notes' })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Attach pitch deck' })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Generate audio memo' })).toBeVisible()
  })

  it('shows recovery when a workspace analysis is unavailable', async () => {
    await import('./router/router').then(({ router }) => router.navigate({ to: '/workspace/evidence' }))
    render(<App />)

    expect(await screen.findByRole('heading', {
      name: 'This analysis is no longer in this browser session.',
    })).toBeVisible()
    expect(screen.getByRole('link', { name: 'Start founder research' })).toHaveAttribute('href', '/')
  })
})
