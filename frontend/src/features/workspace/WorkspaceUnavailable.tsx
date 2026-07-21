import { Link } from '@tanstack/react-router'

export function WorkspaceUnavailable() {
  return (
    <main className="workspace-unavailable" id="main-content" aria-labelledby="workspace-unavailable-title">
      <p className="eyebrow">Workspace unavailable</p>
      <h1 id="workspace-unavailable-title">This analysis is no longer in this browser session.</h1>
      <p>
        FounderX cannot retrieve a completed analysis by ID because the backend currently provides no
        profile retrieval endpoint. Start a new search to rebuild the workspace.
      </p>
      <Link className="button button--primary" to="/">Start founder research</Link>
    </main>
  )
}
