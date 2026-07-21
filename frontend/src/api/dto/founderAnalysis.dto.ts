import { z } from 'zod'

const stringArray = z.array(z.string())
const unknownRecord = z.record(z.string(), z.unknown())

export const evidenceDtoSchema = z.object({
  id: z.string(),
  type: z.string(),
  title: z.string(),
  source: z.string(),
  url: z.string(),
  retrievedAt: z.string(),
  publishedAt: z.string(),
  confidence: z.string(),
  supports: stringArray,
  content: z.string(),
  excerpt: z.string(),
  quote: z.string(),
  sourceCategory: z.string(),
  publisherType: z.string(),
  contentType: z.string(),
  claimCategory: z.string(),
})

const educationDtoSchema = z.object({
  id: z.string(),
  institution: z.string(),
  degree: z.string(),
  field: z.string(),
  startDate: z.string(),
  endDate: z.string(),
  grade: z.string(),
  location: z.string(),
  description: z.string(),
  evidenceIds: stringArray,
})

const experienceDtoSchema = z.object({
  id: z.string(),
  company: z.string(),
  role: z.string(),
  employmentType: z.string(),
  industry: z.string(),
  startDate: z.string(),
  endDate: z.string(),
  isCurrent: z.boolean(),
  location: z.string(),
  description: z.string(),
  skillsUsed: stringArray,
  evidenceIds: stringArray,
})

const projectDtoSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  category: z.string(),
  technologies: stringArray,
  githubRepo: z.string(),
  demoUrl: z.string(),
  website: z.string(),
  startDate: z.string(),
  endDate: z.string(),
  status: z.string(),
  teamSize: z.number(),
  evidenceIds: stringArray,
})

const repositoryDtoSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  url: z.string(),
  primaryLanguage: z.string(),
  languages: stringArray,
  stars: z.number(),
  forks: z.number(),
  watchers: z.number(),
  openIssues: z.number(),
  createdAt: z.string(),
  updatedAt: z.string(),
  topics: stringArray,
  license: z.string(),
  isFork: z.boolean(),
})

const startupDtoSchema = z.object({
  id: z.string(),
  company: z.string(),
  role: z.string(),
  industry: z.string(),
  stage: z.string(),
  startDate: z.string(),
  endDate: z.string(),
  status: z.string(),
  description: z.string(),
  website: z.string(),
  funding: z.object({
    raised: z.string(),
    currency: z.string(),
    round: z.string(),
    investors: stringArray,
  }),
  evidenceIds: stringArray,
})

const productLaunchDtoSchema = z.object({
  id: z.string(),
  productName: z.string(),
  launchDate: z.string(),
  description: z.string(),
  website: z.string(),
  productHunt: z.string(),
  github: z.string(),
  status: z.string(),
  evidenceIds: stringArray,
})

const researchItemDtoSchema = z.object({
  id: z.string(),
  title: z.string(),
  authors: stringArray,
  publication: z.string(),
  year: z.string(),
  url: z.string(),
  citations: z.number(),
  keywords: stringArray,
  evidenceIds: stringArray,
})

const speakingDtoSchema = z.object({
  id: z.string(),
  title: z.string(),
  event: z.string(),
  date: z.string(),
  location: z.string(),
  video: z.string(),
  slides: z.string(),
  topic: z.string(),
  evidenceIds: stringArray,
})

const awardDtoSchema = z.object({
  id: z.string(),
  title: z.string(),
  organization: z.string(),
  date: z.string(),
  description: z.string(),
  evidenceIds: stringArray,
})

const grantDtoSchema = z.object({
  id: z.string(),
  organization: z.string(),
  program: z.string(),
  amount: z.string(),
  date: z.string(),
  description: z.string(),
  evidenceIds: stringArray,
})

const patentDtoSchema = z.object({
  id: z.string(),
  title: z.string(),
  patentNumber: z.string(),
  status: z.string(),
  date: z.string(),
  url: z.string(),
  evidenceIds: stringArray,
})

const communityItemDtoSchema = z.object({
  id: z.string(),
  title: z.string(),
  name: z.string(),
  url: z.string(),
  source: z.string(),
  author: z.string(),
  publishedAt: z.string(),
  date: z.string(),
  description: z.string(),
  summary: z.string(),
  content: z.string(),
  event: z.string(),
  location: z.string(),
  video: z.string(),
  slides: z.string(),
  topic: z.string(),
  episode: z.string(),
  publication: z.string(),
  guests: stringArray,
  evidenceIds: stringArray,
})

const timelineDtoSchema = z.object({
  id: z.string(),
  date: z.string(),
  type: z.string(),
  title: z.string(),
  description: z.string(),
  relatedEntity: z.string(),
  evidenceIds: stringArray,
})

const unknownDtoSchema = z.object({
  category: z.string(),
  field: z.string(),
  reason: z.string(),
  importance: z.string(),
  priority: z.string(),
  recommendedAction: z.string(),
  entityType: z.string(),
  entityId: z.string(),
})

export const founderIntelligenceDtoSchema = z.object({
  strengths: stringArray,
  weaknesses: stringArray,
  executionRisks: stringArray,
  leadershipAssessment: z.string(),
  technicalDepthAssessment: z.string(),
  marketCredibility: z.string(),
  founderQualitySignals: stringArray,
  confidenceScores: z.array(
    z.object({
      dimension: z.string(),
      score: z.number(),
    }),
  ),
  missingInformation: stringArray,
  evidenceReferences: z.array(
    z.object({
      insight: z.string(),
      evidenceIds: stringArray,
    }),
  ),
  reasoning: z.array(
    z.object({
      insight: z.string(),
      reasoning: z.string(),
    }),
  ),
})

export const founderProfileDtoSchema = z.object({
  metadata: z.object({
    profileId: z.string(),
    generatedAt: z.string(),
    lastUpdated: z.string(),
    schemaVersion: z.string(),
    dataSources: stringArray,
    completenessScore: z.number(),
  }),
  founder: z.object({
    id: z.string(),
    name: z.string(),
    headline: z.string(),
    email: z.string(),
    location: z.string(),
    currentCompany: z.string(),
    website: z.string(),
    github: z.string(),
    linkedin: z.string(),
    twitter: z.string(),
    huggingface: z.string(),
    googleScholar: z.string(),
    profileImage: z.string(),
    bio: z.string(),
  }),
  education: z.array(educationDtoSchema),
  experience: z.array(experienceDtoSchema),
  skills: z.object({
    programmingLanguages: stringArray,
    frameworks: stringArray,
    aiMl: stringArray,
    cloud: stringArray,
    databases: stringArray,
    devops: stringArray,
    leadership: stringArray,
    product: stringArray,
    business: stringArray,
    other: stringArray,
  }),
  projects: z.array(projectDtoSchema),
  repositories: z.array(repositoryDtoSchema),
  startupHistory: z.array(startupDtoSchema),
  productLaunches: z.array(productLaunchDtoSchema),
  research: z.array(researchItemDtoSchema),
  publicSpeaking: z.array(speakingDtoSchema),
  awards: z.array(awardDtoSchema),
  grants: z.array(grantDtoSchema),
  patents: z.array(patentDtoSchema),
  opensource: z.object({
    totalRepositories: z.number(),
    totalStars: z.number(),
    totalForks: z.number(),
    organizations: stringArray,
    majorProjects: stringArray,
  }),
  community: z.object({
    blogs: z.array(communityItemDtoSchema),
    newsMentions: z.array(communityItemDtoSchema),
    podcasts: z.array(communityItemDtoSchema),
    interviews: z.array(communityItemDtoSchema),
    newsletters: z.array(communityItemDtoSchema),
  }),
  socialPresence: z.object({
    githubFollowers: z.number(),
    linkedinFollowers: z.number(),
    twitterFollowers: z.number(),
    huggingfaceFollowers: z.number(),
  }),
  timeline: z.array(timelineDtoSchema),
  entities: z.object({
    companies: stringArray,
    projects: stringArray,
    products: stringArray,
    people: stringArray,
    technologies: stringArray,
    researchAreas: stringArray,
  }),
  evidence: z.array(evidenceDtoSchema),
  unknowns: z.array(unknownDtoSchema),
  founderIntelligence: founderIntelligenceDtoSchema.nullable(),
  profileVersion: z.number(),
})

const decisionSignalDtoSchema = z.object({
  source_url: z.string().nullable(),
  summary: z.string(),
  confidence: z.number(),
})

export const founderAnalysisDtoSchema = z.object({
  metadata: z.object({
    researchRunId: z.string(),
    founderId: z.string(),
    profileVersion: z.number(),
  }),
  research: z
    .object({
      github: unknownRecord,
      resume: unknownRecord,
      website: unknownRecord,
      tavily: unknownRecord,
      metadata: z
        .object({
          founderId: z.string(),
          collectedAt: z.string(),
          dataSources: stringArray,
        })
        .passthrough(),
      researchRunId: z.string(),
    })
    .passthrough(),
  founderProfile: founderProfileDtoSchema,
  founderIntelligence: founderIntelligenceDtoSchema,
  investmentDecision: z.object({
    company_name: z.string(),
    recommendation: z.string(),
    state: z.object({
      company_name: z.string(),
      thesis: z.string(),
      source_urls: stringArray,
      mapped_signals: z.array(decisionSignalDtoSchema),
      signals: z.array(decisionSignalDtoSchema),
      scores: z.record(z.string(), z.number()),
      diligence_notes: stringArray,
      recommendation: z.string(),
      errors: stringArray,
    }),
  }),
})

export type FounderAnalysisDto = z.infer<typeof founderAnalysisDtoSchema>
export type FounderProfileDto = z.infer<typeof founderProfileDtoSchema>
export type FounderIntelligenceDto = z.infer<typeof founderIntelligenceDtoSchema>
export type EvidenceDto = z.infer<typeof evidenceDtoSchema>
