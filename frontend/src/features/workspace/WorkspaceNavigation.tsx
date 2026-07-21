import { Link } from '@tanstack/react-router'

import { workspaceNavigation } from './workspaceRoutes'

export function WorkspaceNavigation() {
  return (
    <nav className="workspace-navigation" aria-label="Founder workspace">
      <p>Research workspace</p>
      <ul>
        {workspaceNavigation.map((item) => (
          <li key={item.to}>
            <Link
              to={item.to}
              activeProps={{ 'aria-current': 'page', className: 'is-active' }}
            >
              <span aria-hidden="true">{item.marker}</span>
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}
