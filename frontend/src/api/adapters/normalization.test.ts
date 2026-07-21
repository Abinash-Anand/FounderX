import { optionalText, safeUrl, titleCase, uniqueText } from './normalization'

describe('adapter normalization', () => {
  it('normalizes text collections without inventing content', () => {
    expect(optionalText('   ')).toBeNull()
    expect(uniqueText(['AI', ' AI ', '', 'Product'])).toEqual(['AI', 'Product'])
    expect(titleCase('idea_market')).toBe('Idea Market')
  })

  it('allows only public HTTP links', () => {
    expect(safeUrl('https://example.com')).toBe('https://example.com/')
    expect(safeUrl('javascript:alert(1)')).toBeNull()
    expect(safeUrl('not a url')).toBeNull()
  })
})
