import type { DisplayLink, EvidenceLinked } from '../founder/founder.models'

export type SearchSourceModel = {
  title: string
  url: string | null
  content: string | null
  score: number | null
}

export type ResearchQueryModel = {
  query: string
  answer: string | null
  sources: SearchSourceModel[]
}

export type ResearchItemModel = EvidenceLinked & {
  id: string
  kind: 'publication' | 'speaking' | 'award' | 'grant' | 'patent' | 'community'
  title: string
  subtitle: string | null
  date: string | null
  description: string | null
  links: DisplayLink[]
  tags: string[]
}

export type ResearchModel = {
  collectedAt: string | null
  dataSources: string[]
  searches: ResearchQueryModel[]
  publications: ResearchItemModel[]
  speaking: ResearchItemModel[]
  recognition: ResearchItemModel[]
  community: ResearchItemModel[]
}
