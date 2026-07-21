import type { InvestmentMemoModel } from '../decision/decision.models'
import type { EvidencePageModel } from '../evidence/evidence.models'
import type { FounderIntelligenceModel } from '../intelligence/intelligence.models'
import type { ResearchModel } from '../research/research.models'
import type {
  CareerModel,
  FounderContext,
  FounderOverviewModel,
  FounderProfileModel,
  ProjectsModel,
  StartupsModel,
} from './founder.models'

export type FounderAnalysisModel = {
  context: FounderContext
  overview: FounderOverviewModel
  founder: FounderProfileModel
  career: CareerModel
  startups: StartupsModel
  projects: ProjectsModel
  research: ResearchModel
  evidence: EvidencePageModel
  intelligence: FounderIntelligenceModel
  investmentMemo: InvestmentMemoModel
}
