export const founderAnalysisKeys = {
  all: ['founder-analysis'] as const,
  active: () => [...founderAnalysisKeys.all, 'active'] as const,
  query: (query: string) => [...founderAnalysisKeys.all, 'query', query.trim().toLocaleLowerCase()] as const,
}
