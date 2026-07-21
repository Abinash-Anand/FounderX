import { Link } from '@tanstack/react-router'

import type { EvidenceReference } from '../../entities/founder/founder.models'

type Props = {
  evidence: EvidenceReference[]
  unresolvedEvidenceIds?: string[]
}

export function EvidenceLinks({ evidence, unresolvedEvidenceIds = [] }: Props) {
  if (evidence.length === 0 && unresolvedEvidenceIds.length === 0) return null

  return (
    <div className="evidence-links">
      <span>Evidence</span>
      {evidence.map((item) => (
        <Link key={item.id} to="/workspace/evidence" hash={item.id}>{item.title}</Link>
      ))}
      {unresolvedEvidenceIds.length > 0 ? (
        <span className="evidence-links__missing">
          {unresolvedEvidenceIds.length} unresolved reference{unresolvedEvidenceIds.length === 1 ? '' : 's'}
        </span>
      ) : null}
    </div>
  )
}
