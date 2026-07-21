import { Outlet } from '@tanstack/react-router'

import type { FounderAnalysisModel } from '../../entities/founder/founderAnalysis.models'
import { WorkspaceHeader } from './WorkspaceHeader'
import { WorkspaceMobileNavigation } from './WorkspaceMobileNavigation'
import { WorkspaceNavigation } from './WorkspaceNavigation'
import { WorkspaceProvider } from './WorkspaceContext'

type Props = {
  analysis: FounderAnalysisModel
}

export function WorkspaceShell({ analysis }: Props) {
  return (
    <WorkspaceProvider analysis={analysis}>
      <div className="workspace-shell" id="main-content">
        <WorkspaceHeader context={analysis.context} />
        <WorkspaceMobileNavigation />
        <div className="workspace-shell__body">
          <aside className="workspace-shell__sidebar">
            <WorkspaceNavigation />
          </aside>
          <main className="workspace-content">
            <Outlet />
          </main>
        </div>
      </div>
    </WorkspaceProvider>
  )
}
