import { useQueryClient } from '@tanstack/react-query'

import type { FounderAnalysisModel } from '../../entities/founder/founderAnalysis.models'
import { founderAnalysisKeys } from '../../features/founder-search/founderAnalysis.keys'
import { WorkspaceShell } from '../../features/workspace/WorkspaceShell'
import { WorkspaceUnavailable } from '../../features/workspace/WorkspaceUnavailable'

export function WorkspaceRoute() {
  const queryClient = useQueryClient()
  const analysis = queryClient.getQueryData<FounderAnalysisModel>(founderAnalysisKeys.active())

  return analysis ? <WorkspaceShell analysis={analysis} /> : <WorkspaceUnavailable />
}
