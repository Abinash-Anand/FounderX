import { Link } from '@tanstack/react-router'

import { workspaceNavigation } from './workspaceRoutes'

export function WorkspaceMobileNavigation() {
  return (
    <nav className="workspace-mobile-navigation" aria-label="Founder workspace sections">
      {workspaceNavigation.map((item) => (
        <Link
          key={item.to}
          to={item.to}
          activeProps={{ 'aria-current': 'page', className: 'is-active' }}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  )
}
