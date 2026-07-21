import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 15 * 60_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        const status = error instanceof Error && 'status' in error ? Number(error.status) : 0
        return status >= 400 && status < 500 ? false : failureCount < 2
      },
    },
    mutations: {
      retry: false,
    },
  },
})
