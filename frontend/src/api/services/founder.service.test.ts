import { vi } from 'vitest'

import { requestJson } from '../client/restClient'
import { createFounderAnalysisFixture } from '../../test/fixtures/founderAnalysis.fixture'
import { founderService } from './founder.service'

vi.mock('../client/restClient', () => ({ requestJson: vi.fn() }))

describe('founderService', () => {
  it('calls the analyze endpoint and returns an adapted model', async () => {
    vi.mocked(requestJson).mockResolvedValue(createFounderAnalysisFixture())

    const result = await founderService.analyze('Research Ada')

    expect(requestJson).toHaveBeenCalledWith('/v1/founders/analyze', expect.objectContaining({
      method: 'POST',
      body: { query: 'Research Ada' },
    }))
    expect(result.context.name).toBe('Ada Founder')
  })
})
