import type { DisplayLink } from '../../entities/founder/founder.models'

export function optionalText(value: string): string | null {
  const normalized = value.trim()
  return normalized.length > 0 ? normalized : null
}

export function uniqueText(values: string[]): string[] {
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))]
}

export function safeUrl(value: string): string | null {
  const normalized = optionalText(value)
  if (!normalized) return null

  try {
    const url = new URL(normalized)
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.toString() : null
  } catch {
    return null
  }
}

export function createLink(label: string, value: string): DisplayLink | null {
  const href = safeUrl(value)
  return href ? { label, href } : null
}

export function definedItems<T>(values: Array<T | null>): T[] {
  return values.filter((value): value is T => value !== null)
}

export function titleCase(value: string): string {
  return value
    .replaceAll('_', ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

export function distinctSorted(values: Array<string | null>): string[] {
  return [...new Set(values.filter((value): value is string => Boolean(value)))].sort((a, b) =>
    a.localeCompare(b),
  )
}
