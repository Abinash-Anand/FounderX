// Deterministic trust-score weighting layer.
// Shared between server (to compute scores) and client (to explain them).
//
// A claim's final trust_score is derived from:
//   1. The credibility weight of its cited source domain
//   2. The verification status the analyst assigned (verified / plausible / unverifiable / flagged)
// The model's raw score is NOT used — this keeps scoring transparent and reproducible.

export type SourceTier = {
  tier: string;
  weight: number; // 0-1, applied when a claim cites a domain in this tier
  description: string;
  examples: string[];
};

// Ordered from highest to lowest authority. Matching is substring-based on the
// claim's `source` field (which may be a domain like "crunchbase.com", a URL,
// or a free-text label).
export const SOURCE_TIERS: SourceTier[] = [
  {
    tier: "Regulatory & filings",
    weight: 0.98,
    description: "Primary-source public filings — highest trust.",
    examples: ["sec.gov", "companieshouse.gov.uk", "uspto.gov", "eur-lex.europa.eu"],
  },
  {
    tier: "Funding & company registries",
    weight: 0.9,
    description: "Structured funding databases with editorial review.",
    examples: ["crunchbase.com", "pitchbook.com", "dealroom.co", "cbinsights.com"],
  },
  {
    tier: "Tier-1 business press",
    weight: 0.85,
    description: "Established outlets with fact-checking desks.",
    examples: ["ft.com", "wsj.com", "bloomberg.com", "reuters.com", "economist.com", "nytimes.com"],
  },
  {
    tier: "Tech press",
    weight: 0.75,
    description: "Reputable tech journalism — good for launches, rounds, traction.",
    examples: ["techcrunch.com", "theinformation.com", "wired.com", "arstechnica.com", "theverge.com"],
  },
  {
    tier: "Developer signal",
    weight: 0.8,
    description: "Verifiable engineering activity — commits, releases, stars.",
    examples: ["github.com", "gitlab.com", "npmjs.com", "pypi.org"],
  },
  {
    tier: "Product / community traction",
    weight: 0.7,
    description: "Public product launches and community votes.",
    examples: ["producthunt.com", "ycombinator.com", "news.ycombinator.com"],
  },
  {
    tier: "Professional profile",
    weight: 0.65,
    description: "Self-authored but employer-verifiable.",
    examples: ["linkedin.com"],
  },
  {
    tier: "Company-owned site",
    weight: 0.55,
    description: "First-party marketing — accurate on identity, promotional on claims.",
    examples: ["about", "team", "careers", "press-release", "prnewswire.com", "businesswire.com"],
  },
  {
    tier: "Social media",
    weight: 0.35,
    description: "Personal posts — down-weighted; treat as directional only.",
    examples: ["twitter.com", "x.com", "medium.com", "substack.com", "reddit.com"],
  },
  {
    tier: "Unknown / unavailable",
    weight: 0.15,
    description: "No cited source or the source could not be identified.",
    examples: ["Unavailable", "n/a", "(none)"],
  },
];

export function domainWeight(source: string | undefined | null): { tier: SourceTier; matched: string } {
  const fallback = SOURCE_TIERS[SOURCE_TIERS.length - 1];
  if (!source) return { tier: fallback, matched: "unavailable" };
  const s = source.toLowerCase().trim();
  if (!s || s === "unavailable" || s === "n/a" || s === "none") {
    return { tier: fallback, matched: "unavailable" };
  }
  for (const tier of SOURCE_TIERS) {
    for (const ex of tier.examples) {
      if (s.includes(ex.toLowerCase())) return { tier, matched: ex };
    }
  }
  return { tier: fallback, matched: s };
}

export type ClaimStatus = "verified" | "plausible" | "unverifiable" | "flagged";

// Status multipliers applied on top of the domain weight.
export const STATUS_MULTIPLIER: Record<ClaimStatus, number> = {
  verified: 1.0,
  plausible: 0.8,
  unverifiable: 0.45,
  flagged: 0.2,
};

export function computeClaimTrust(source: string | undefined, status: ClaimStatus): number {
  const { tier } = domainWeight(source);
  const raw = tier.weight * STATUS_MULTIPLIER[status];
  return Math.max(0, Math.min(1, Number(raw.toFixed(2))));
}

// Axis weights used by the model when producing the composite score.
// Displayed in the UI tooltip so the VC understands the recipe.
export const AXIS_WEIGHTS = [
  { label: "Founder axis", weight: 0.4, description: "Team depth, prior exits, technical & domain expertise." },
  { label: "Market axis", weight: 0.35, description: "TAM, growth rate, competitive dynamics." },
  { label: "Fit axis", weight: 0.25, description: "Alignment with the VC's thesis and filters." },
];

// Signal weights the sourcing engine uses when evaluating founder quality.
export const SIGNAL_WEIGHTS = [
  { label: "GitHub activity", weight: 0.3 },
  { label: "ProductHunt traction", weight: 0.25 },
  { label: "Credible press / funding rounds", weight: 0.2 },
  { label: "LinkedIn credibility", weight: 0.15 },
  { label: "Hackathon / community", weight: 0.1 },
];
