export type DisplayLink = {
  label: string
  href: string
}

export type EvidenceReference = {
  id: string
  title: string
  source: string | null
  url: string | null
  confidence: string | null
  claimCategory: string | null
  excerpt: string | null
}

export type EvidenceLinked = {
  evidence: EvidenceReference[]
  unresolvedEvidenceIds: string[]
}

export type FounderContext = {
  id: string
  researchRunId: string
  profileVersion: number
  name: string
  headline: string | null
  currentCompany: string | null
  location: string | null
  bio: string | null
  profileImageUrl: string | null
  links: DisplayLink[]
  completenessScore: number
  generatedAt: string | null
  lastUpdated: string | null
  dataSources: string[]
  recommendation: string
}

export type SkillGroup = {
  key: string
  label: string
  values: string[]
}

export type FounderOverviewModel = {
  context: FounderContext
  skills: SkillGroup[]
  counts: {
    experience: number
    startups: number
    projects: number
    research: number
    evidence: number
  }
  strengths: string[]
  risks: string[]
  missingInformation: string[]
}

export type FounderProfileModel = {
  context: FounderContext
  email: string | null
  socialFollowers: Array<{ label: string; value: number }>
  skills: SkillGroup[]
  entities: Array<{ label: string; values: string[] }>
}

export type CareerItem = EvidenceLinked & {
  id: string
  organization: string
  title: string | null
  startDate: string | null
  endDate: string | null
  isCurrent: boolean
  location: string | null
  description: string | null
  tags: string[]
}

export type TimelineItem = EvidenceLinked & {
  id: string
  date: string | null
  type: string | null
  title: string
  description: string | null
  relatedEntity: string | null
}

export type CareerModel = {
  experience: CareerItem[]
  education: CareerItem[]
  timeline: TimelineItem[]
}

export type StartupItem = EvidenceLinked & {
  id: string
  company: string
  role: string | null
  industry: string | null
  stage: string | null
  period: { start: string | null; end: string | null }
  status: string | null
  description: string | null
  website: string | null
  funding: {
    raised: string | null
    currency: string | null
    round: string | null
    investors: string[]
  }
}

export type ProductLaunchItem = EvidenceLinked & {
  id: string
  name: string
  launchDate: string | null
  description: string | null
  status: string | null
  links: DisplayLink[]
}

export type StartupsModel = {
  startups: StartupItem[]
  productLaunches: ProductLaunchItem[]
}

export type ProjectItem = EvidenceLinked & {
  id: string
  name: string
  description: string | null
  category: string | null
  technologies: string[]
  status: string | null
  teamSize: number | null
  links: DisplayLink[]
}

export type RepositoryItem = {
  id: string
  name: string
  description: string | null
  url: string | null
  primaryLanguage: string | null
  stars: number
  forks: number
  watchers: number
  openIssues: number
  topics: string[]
  license: string | null
  isFork: boolean
}

export type ProjectsModel = {
  projects: ProjectItem[]
  repositories: RepositoryItem[]
  openSource: {
    totalRepositories: number
    totalStars: number
    totalForks: number
    organizations: string[]
    majorProjects: string[]
  }
}
