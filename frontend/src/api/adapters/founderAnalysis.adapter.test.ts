import { ApiError } from '../errors/ApiError'
import { createFounderAnalysisFixture } from '../../test/fixtures/founderAnalysis.fixture'
import { adaptFounderAnalysis } from './founderAnalysis.adapter'

describe('adaptFounderAnalysis', () => {
  it('creates page models and normalizes unsafe or empty values', () => {
    const result = adaptFounderAnalysis(createFounderAnalysisFixture())

    expect(result.context.name).toBe('Ada Founder')
    expect(result.context.profileImageUrl).toBeNull()
    expect(result.context.links.map((link) => link.label)).toEqual(['Website', 'GitHub'])
    expect(result.overview.counts).toEqual({
      experience: 1,
      startups: 0,
      projects: 0,
      research: 0,
      evidence: 1,
    })
    expect(result.investmentMemo.sourceUrls).toEqual(['https://example.com/founder'])
  })

  it('uses root intelligence and resolves evidence references', () => {
    const result = adaptFounderAnalysis(createFounderAnalysisFixture())

    expect(result.intelligence.strengths).toEqual(['Technical execution'])
    expect(result.intelligence.insights[0]).toEqual(
      expect.objectContaining({
        insight: 'Technical execution',
        reasoning: 'Supported by public work.',
        unresolvedEvidenceIds: ['missing'],
      }),
    )
    expect(result.intelligence.insights[0]?.evidence[0]?.id).toBe('ev-1')
    expect(result.career.experience[0]?.evidence[0]?.title).toBe('Founder profile')
  })

  it('extracts safe raw research searches without exposing arbitrary data', () => {
    const result = adaptFounderAnalysis(createFounderAnalysisFixture())

    expect(result.research.searches).toEqual([
      {
        query: 'Ada Founder Acme',
        answer: 'Ada founded Acme.',
        sources: [{
          title: 'Acme profile',
          url: 'https://example.com/acme',
          content: 'Profile',
          score: 0.91,
        }],
      },
    ])
  })

  it('rejects an unsupported backend response at the boundary', () => {
    expect(() => adaptFounderAnalysis({ metadata: {} })).toThrow(ApiError)
  })
})
