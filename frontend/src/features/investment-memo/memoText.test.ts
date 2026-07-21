import { adaptFounderAnalysis } from '../../api/adapters/founderAnalysis.adapter'
import { createFounderAnalysisFixture } from '../../test/fixtures/founderAnalysis.fixture'
import { buildMemoNarrationText } from './memoText'

describe('buildMemoNarrationText', () => {
  it('composes only existing analysis fields into narration text', () => {
    const text = buildMemoNarrationText(adaptFounderAnalysis(createFounderAnalysisFixture()))

    expect(text).toContain('Investment brief for Acme.')
    expect(text).toContain('Recommendation: hold for evidence.')
    expect(text).toContain('Strengths: Technical execution.')
    expect(text).toContain('Missing information: Customer retention.')
  })
})
