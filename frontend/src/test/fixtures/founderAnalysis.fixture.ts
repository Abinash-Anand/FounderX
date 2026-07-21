import type { FounderAnalysisDto } from '../../api/dto/founderAnalysis.dto'

export function createFounderAnalysisFixture(): FounderAnalysisDto {
  const intelligence = {
    strengths: ['Technical execution'],
    weaknesses: [],
    executionRisks: ['Limited commercial evidence'],
    leadershipAssessment: 'Evidence indicates hands-on leadership.',
    technicalDepthAssessment: 'Strong technical depth.',
    marketCredibility: 'Early market credibility.',
    founderQualitySignals: ['Built and shipped products'],
    confidenceScores: [{ dimension: 'technical depth', score: 0.82 }],
    missingInformation: ['Customer retention'],
    evidenceReferences: [{ insight: 'Technical execution', evidenceIds: ['ev-1', 'missing'] }],
    reasoning: [{ insight: 'Technical execution', reasoning: 'Supported by public work.' }],
  }

  return {
    metadata: { researchRunId: 'run-1', founderId: 'founder-1', profileVersion: 3 },
    research: {
      github: {},
      resume: {},
      website: {},
      tavily: {
        searches: [{
          query: 'Ada Founder Acme',
          answer: 'Ada founded Acme.',
          sources: [{ title: 'Acme profile', url: 'https://example.com/acme', content: 'Profile', score: 0.91 }],
        }],
      },
      metadata: { founderId: 'founder-1', collectedAt: '2026-07-21T10:00:00Z', dataSources: ['Tavily'] },
      researchRunId: 'run-1',
    },
    founderProfile: {
      metadata: {
        profileId: 'profile-1', generatedAt: '2026-07-21T10:01:00Z',
        lastUpdated: '2026-07-21T10:02:00Z', schemaVersion: '1.0.0',
        dataSources: ['Tavily', 'GitHub'], completenessScore: 78,
      },
      founder: {
        id: 'founder-1', name: ' Ada Founder ', headline: 'Builder', email: 'ada@example.com',
        location: 'Berlin', currentCompany: 'Acme', website: 'https://acme.example',
        github: 'https://github.com/ada', linkedin: '', twitter: '', huggingface: '',
        googleScholar: '', profileImage: 'javascript:alert(1)', bio: 'Builds useful systems.',
      },
      education: [],
      experience: [{
        id: 'exp-1', company: 'Acme', role: 'Founder', employmentType: 'Full-time',
        industry: 'Software', startDate: '2024', endDate: '', isCurrent: true,
        location: 'Berlin', description: 'Company builder.', skillsUsed: ['Leadership'], evidenceIds: ['ev-1'],
      }],
      skills: {
        programmingLanguages: ['TypeScript'], frameworks: [], aiMl: ['LLMs'], cloud: [],
        databases: [], devops: [], leadership: ['Hiring'], product: [], business: [], other: [],
      },
      projects: [], repositories: [], startupHistory: [], productLaunches: [], research: [],
      publicSpeaking: [], awards: [], grants: [], patents: [],
      opensource: { totalRepositories: 0, totalStars: 0, totalForks: 0, organizations: [], majorProjects: [] },
      community: { blogs: [], newsMentions: [], podcasts: [], interviews: [], newsletters: [] },
      socialPresence: { githubFollowers: 12, linkedinFollowers: 0, twitterFollowers: 0, huggingfaceFollowers: 0 },
      timeline: [],
      entities: { companies: ['Acme'], projects: [], products: [], people: [], technologies: ['TypeScript'], researchAreas: [] },
      evidence: [{
        id: 'ev-1', type: 'profile', title: 'Founder profile', source: 'Example',
        url: 'https://example.com/founder', retrievedAt: '2026-07-21', publishedAt: '2026-07-20',
        confidence: 'high', supports: ['experience'], content: 'Ada founded Acme.', excerpt: 'Founded Acme',
        quote: '', sourceCategory: 'Primary', publisherType: 'Company', contentType: 'Profile', claimCategory: 'Career',
      }],
      unknowns: [{
        category: 'traction', field: 'retention', reason: 'Not publicly available', importance: 'high',
        priority: 'high', recommendedAction: 'Request cohort data', entityType: 'company', entityId: 'Acme',
      }],
      founderIntelligence: { ...intelligence, strengths: ['Nested value must not win'] },
      profileVersion: 3,
    },
    founderIntelligence: intelligence,
    investmentDecision: {
      company_name: 'Acme', recommendation: 'hold_for_evidence',
      state: {
        company_name: 'Acme', thesis: 'Evaluate Ada and Acme.',
        source_urls: ['https://example.com/founder', 'javascript:alert(1)'],
        mapped_signals: [{ source_url: null, summary: 'Research Acme', confidence: 0.1 }],
        signals: [{ source_url: 'https://example.com/founder', summary: 'Founder profile', confidence: 0.7 }],
        scores: { founder: 62.5, market: 60, idea_market: 60 },
        diligence_notes: ['Validate customer claims.'], recommendation: 'hold_for_evidence', errors: [],
      },
    },
  }
}
