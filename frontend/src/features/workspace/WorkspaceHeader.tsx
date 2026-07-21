import { Link } from '@tanstack/react-router'

import type { FounderContext } from '../../entities/founder/founder.models'

type Props = {
  context: FounderContext
}

function initials(name: string): string {
  return name.split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase()
}

function recommendationLabel(value: string): string {
  return value.replaceAll('_', ' ')
}

export function WorkspaceHeader({ context }: Props) {
  return (
    <header className="workspace-header">
      <div className="workspace-header__identity">
        {context.profileImageUrl ? (
          <img src={context.profileImageUrl} alt="" />
        ) : (
          <span className="workspace-header__avatar" aria-hidden="true">{initials(context.name)}</span>
        )}
        <div>
          <p className="workspace-header__name">{context.name}</p>
          <p>{[context.currentCompany, context.location].filter(Boolean).join(' · ') || 'Founder profile'}</p>
        </div>
      </div>
      <div className="workspace-header__status">
        <span className="workspace-header__recommendation">{recommendationLabel(context.recommendation)}</span>
        <span>{Math.round(context.completenessScore)}% complete</span>
      </div>
      <Link className="button button--secondary" to="/">New research</Link>
    </header>
  )
}
