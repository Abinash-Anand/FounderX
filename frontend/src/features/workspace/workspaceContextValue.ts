import { createContext, useContext } from 'react'

import type { FounderAnalysisModel } from '../../entities/founder/founderAnalysis.models'

export const WorkspaceContext = createContext<FounderAnalysisModel | null>(null)

export function useWorkspaceAnalysis(): FounderAnalysisModel {
  const analysis = useContext(WorkspaceContext)
  if (!analysis) throw new Error('Workspace content must render inside WorkspaceProvider.')
  return analysis
}
