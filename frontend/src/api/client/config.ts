const DEFAULT_API_URL = 'https://founderx-wwmi.onrender.com'

export const apiConfig = {
  baseUrl: (import.meta.env.VITE_BACKEND_URL || DEFAULT_API_URL).replace(/\/$/, ''),
  timeoutMs: 120_000,
} as const
