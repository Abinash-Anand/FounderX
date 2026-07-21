import { formatPeriod, formatResearchDate } from './date'

describe('research date formatting', () => {
  it('preserves partial date precision', () => {
    expect(formatResearchDate('2024')).toBe('2024')
    expect(formatResearchDate('2024-05')).toBe('May 2024')
    expect(formatResearchDate('not dated')).toBe('not dated')
  })

  it('uses an honest fallback when dates are absent', () => {
    expect(formatPeriod(null, null)).toBe('Date unavailable')
    expect(formatPeriod('2024', null, true)).toBe('2024 – Present')
  })
})
