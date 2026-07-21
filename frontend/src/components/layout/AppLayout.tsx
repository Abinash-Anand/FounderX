import { Link } from '@tanstack/react-router'
import type { PropsWithChildren } from 'react'

export function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className="app-layout">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className="app-header">
        <Link className="brand" to="/" aria-label="FounderX home">
          <span className="brand__mark" aria-hidden="true">F</span>
          FounderX
        </Link>
        <p>AI research workspace for venture investors</p>
      </header>
      {children}
    </div>
  )
}
