import type { PropsWithChildren } from 'react'

import type { FounderAnalysisModel } from '../../entities/founder/founderAnalysis.models'
import { WorkspaceContext } from './workspaceContextValue'

type Props = PropsWithChildren<{
  analysis: FounderAnalysisModel
}>

export function WorkspaceProvider({ analysis, children }: Props) {
  return <WorkspaceContext.Provider value={analysis}>{children}</WorkspaceContext.Provider>
}
