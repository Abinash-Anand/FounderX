import { createServerFn } from "@tanstack/react-start";
import { generateText } from "ai";
import { z } from "zod";
import { computeClaimTrust, type ClaimStatus } from "./trust-weights";

const MODEL = "google/gemini-3-flash-preview";

// Post-process a screened result: recompute every claim's trust_score
// deterministically from its cited source domain + status, then set
// overall_trust_score to the average of the recomputed claim trusts.
function applyDeterministicTrust<T extends {
  overall_trust_score: number;
  memo: Record<string, { claims: { source: string; status: ClaimStatus; trust_score: number }[] }>;
}>(result: T): T {
  const all: number[] = [];
  for (const section of Object.values(result.memo)) {
    for (const claim of section.claims) {
      claim.trust_score = computeClaimTrust(claim.source, claim.status);
      all.push(claim.trust_score);
    }
  }
  if (all.length) {
    result.overall_trust_score = Number(
      (all.reduce((a, b) => a + b, 0) / all.length).toFixed(2),
    );
  }
  return result;
}

// ---------- Sourcing schema ----------
const SourceInput = z.object({
  query: z.string().min(2).max(400),
  sector: z.string().optional(),
  stage: z.string().optional(),
  geography: z.string().optional(),
  check_size: z.string().optional(),
  risk: z.string().optional(),
  ownership: z.string().optional(),
  limit: z.number().int().min(1).max(12).optional(),
});

const RawFounderSchema = z.object({
  name: z.string(),
  company: z.string(),
  role: z.string(),
  location: z.string(),
  stage: z.string(),
  sector: z.string(),
  background: z.string(),
  signals: z.array(z.string()),
  source_url: z.string(),
});

const RawSourceOutput = z.object({
  founders: z.array(RawFounderSchema),
  summary: z.string(),
});

// Validation / knowledge-graph resolution — cross-references sources to
// confirm the founder identity and resolve canonical links. Anything
// unresolved must be the string "Unavailable" — never fabricated.
const ResolvedLinksSchema = z.object({
  identity_confirmed: z.boolean(),
  confirmation_reasoning: z.string(),
  cross_references: z.array(z.object({
    source: z.string(),
    url: z.string(),
    supports: z.string(),
  })),
  founder_linkedin_url: z.string(),
  founder_twitter_url: z.string(),
  founder_github_url: z.string(),
  personal_site_url: z.string(),
  company_website_url: z.string(),
  company_linkedin_url: z.string(),
  company_crunchbase_url: z.string(),
});

// ---------- Screening + memo per founder ----------
const AxisSchema = z.object({
  score: z.number(),
  confidence: z.number(),
  reasoning: z.string(),
  key_factors: z.array(z.string()),
});

const ClaimSchema = z.object({
  claim: z.string(),
  trust_score: z.number(), // 0-1
  status: z.enum(["verified", "plausible", "unverifiable", "flagged"]),
  evidence: z.string(),
  source: z.string(),
});

const MemoSectionSchema = z.object({
  title: z.string(),
  summary: z.string(),
  claims: z.array(ClaimSchema),
  trace: z.array(z.string()), // chain-of-thought steps
});

const ScreenedFounderSchema = z.object({
  founder_axis: AxisSchema,
  market_axis: AxisSchema,
  fit_axis: AxisSchema,
  composite_score: z.number(),
  recommendation: z.enum(["strong_pass", "review", "pass"]),
  overall_trust_score: z.number(),
  memo: z.object({
    thesis: MemoSectionSchema,
    founder: MemoSectionSchema,
    market: MemoSectionSchema,
    product: MemoSectionSchema,
    traction: MemoSectionSchema,
    risks: MemoSectionSchema,
  }),
  cold_email_subject: z.string(),
  cold_email_body: z.string(),
});

// ---------- Utilities ----------
async function getModel() {
  const key = process.env.LOVABLE_API_KEY;
  if (!key) throw new Error("Missing LOVABLE_API_KEY");
  const { createLovableAiGatewayProvider } = await import("./ai-gateway.server");
  return createLovableAiGatewayProvider(key)(MODEL);
}

function extractJson(text: string): unknown {
  let s = text.trim();
  s = s.replace(/^```(?:json)?/i, "").replace(/```$/, "").trim();
  const first = s.indexOf("{");
  const last = s.lastIndexOf("}");
  if (first === -1 || last === -1) throw new Error("Model did not return JSON");
  return JSON.parse(s.slice(first, last + 1));
}

async function runJson<T>(system: string, prompt: string, schema: z.ZodType<T>): Promise<T> {
  const model = await getModel();
  const { text } = await generateText({
    model,
    system: `${system}\n\nOutput MUST be a single valid JSON object. No prose, no markdown fences. All fields required. When a value is genuinely missing from the evidence, use the exact string "Unavailable" (or empty array for lists). NEVER fabricate names, URLs, numbers, or facts.`,
    prompt,
  });
  const raw = extractJson(text);
  const parsed = schema.safeParse(raw);
  if (!parsed.success) {
    throw new Error(`AI returned unexpected shape: ${parsed.error.issues.slice(0, 3).map((i) => i.path.join(".") + ": " + i.message).join("; ")}`);
  }
  return parsed.data;
}

// ---------- Server functions ----------

export const sourceAndScreen = createServerFn({ method: "POST" })
  .inputValidator((input: unknown) => SourceInput.parse(input))
  .handler(async ({ data }) => {
    const { tavilySearch } = await import("./tavily.server");
    const limit = data.limit ?? 6;

    const filterBits = [
      data.sector && `sector:${data.sector}`,
      data.stage && `stage:${data.stage}`,
      data.geography && `location:${data.geography}`,
    ].filter(Boolean).join(" ");

    // 1. Source candidates
    const searchQuery = `${data.query} ${filterBits} founder OR co-founder site:linkedin.com OR site:crunchbase.com OR site:producthunt.com OR site:github.com`;
    const search = await tavilySearch(searchQuery, {
      max_results: Math.min(limit * 2, 12),
      search_depth: "advanced",
      include_answer: true,
    });

    const snippets = search.results
      .map((r, i) => `[${i + 1}] ${r.title}\nURL: ${r.url}\n${r.content.slice(0, 600)}`)
      .join("\n\n");

    const sourced = await runJson(
      `You are an elite VC sourcing analyst. Extract REAL founders from web research. HARD RULES:
- Never invent names, companies, or URLs. If the source does not clearly name a real human founder, DO NOT include that entry.
- The 'name' field must be the founder's actual full name as it appears in the evidence. Do NOT output "Unknown", "Founder", "N/A", initials only, a company name, or any placeholder. If you cannot find a real name, omit the entry entirely.
- source_url MUST be copied verbatim from the research below.
- For any other field where the evidence is missing, use the exact string "Unavailable" — do not guess.`,
      `VC thesis query: "${data.query}"
Filters: sector=${data.sector ?? "any"}, stage=${data.stage ?? "any"}, geography=${data.geography ?? "any"}, check_size=${data.check_size ?? "any"}, risk=${data.risk ?? "any"}, ownership=${data.ownership ?? "any"}

Web research (${search.results.length} sources):
${snippets}

${search.answer ? `Overview: ${search.answer}\n\n` : ""}
Return JSON:
{
  "summary": "2-sentence landscape summary",
  "founders": [
    {
      "name": "Actual full name from evidence (never a placeholder)",
      "company": "Company",
      "role": "Co-founder & CEO",
      "location": "City, Country or Unavailable",
      "stage": "Pre-seed | Seed | Bootstrapped | Unavailable",
      "sector": "one short sector label",
      "background": "1-2 sentence factual bio",
      "signals": ["ex-Google eng", "$2M seed 2024"],
      "source_url": "exact URL from research above"
    }
  ]
}

Return up to ${limit} distinct founders with real, verifiable names. Prefer founders with no or minimal VC funding. Quality over quantity — return fewer entries rather than any placeholders.`,
      RawSourceOutput,
    );

    // Reject placeholder / obviously invalid founder names before doing any expensive screening.
    const NAME_BLOCKLIST = /^(unknown|unavailable|n\/?a|none|founder|ceo|the founder|not (found|listed|available)|anonymous|—|-)$/i;
    const validNameCandidates = sourced.founders.filter((f) => {
      const n = (f.name ?? "").trim();
      if (!n || n.length < 3) return false;
      if (NAME_BLOCKLIST.test(n)) return false;
      // Must look like a human name: at least two whitespace-separated tokens, letters present.
      if (!/[A-Za-z]/.test(n)) return false;
      if (n.split(/\s+/).filter(Boolean).length < 2) return false;
      // Reject if "name" equals the company (common LLM confusion).
      if (n.toLowerCase() === (f.company ?? "").trim().toLowerCase()) return false;
      return true;
    });

    // 2. Validation + screening per founder in parallel.
    const screened = await Promise.all(
      validNameCandidates.map(async (f) => {
        // 2a. Broaden the evidence base: run multiple targeted searches so the
        // validation step has real cross-references (a mini knowledge graph:
        // person node ↔ company node ↔ social/press nodes).
        const [profileSearch, companySearch, tractionSearch] = await Promise.all([
          tavilySearch(`"${f.name}" ${f.company} linkedin OR github OR twitter`, { max_results: 5, search_depth: "basic" }).catch(() => ({ results: [] as { url: string; title: string; content: string }[] })),
          tavilySearch(`"${f.company}" official site OR crunchbase OR linkedin company`, { max_results: 5, search_depth: "basic" }).catch(() => ({ results: [] as { url: string; title: string; content: string }[] })),
          tavilySearch(`"${f.name}" "${f.company}" funding OR launch OR product OR press`, { max_results: 5, search_depth: "basic" }).catch(() => ({ results: [] as { url: string; title: string; content: string }[] })),
        ]);

        const dedupe = new Map<string, { title: string; url: string; content: string }>();
        for (const r of [...profileSearch.results, ...companySearch.results, ...tractionSearch.results]) {
          if (!dedupe.has(r.url)) dedupe.set(r.url, r);
        }
        const evidenceItems = [...dedupe.values()];
        const evidence = evidenceItems
          .map((r, i) => `[${i + 1}] ${r.title} — ${r.url}\n${r.content.slice(0, 350)}`)
          .join("\n\n") || "(no additional evidence found)";

        // 2b. Validation layer — reconcile identity + resolve canonical links.
        let resolved: z.infer<typeof ResolvedLinksSchema>;
        try {
          resolved = await runJson(
            `You are a validation agent. Cross-reference multiple sources like a knowledge-graph resolver to (a) confirm this is a real, correctly-named human founder of this specific company, and (b) resolve canonical URLs. HARD RULES:
- Only accept a URL if it appears in the EVIDENCE below. Do NOT guess or construct URLs.
- LinkedIn URLs must start with https://www.linkedin.com/in/ (people) or https://www.linkedin.com/company/ (companies) AND appear in the evidence.
- If a URL for a given field cannot be found in the evidence, return exactly "Unavailable" for that field.
- Set identity_confirmed=false if the evidence does not clearly tie THIS name to THIS company. In that case, still return whatever URLs you did find.`,
            `CANDIDATE:
Name: ${f.name}
Company: ${f.company}
Role: ${f.role}
Primary source: ${f.source_url}

EVIDENCE (${evidenceItems.length} cross-references):
${evidence}

Return JSON:
{
  "identity_confirmed": true|false,
  "confirmation_reasoning": "1-2 sentences citing which evidence items tie the name to the company",
  "cross_references": [ { "source": "domain", "url": "exact url from evidence", "supports": "what this source confirms" } ],
  "founder_linkedin_url": "https://www.linkedin.com/in/... or Unavailable",
  "founder_twitter_url":  "https://twitter.com/... or https://x.com/... or Unavailable",
  "founder_github_url":   "https://github.com/... or Unavailable",
  "personal_site_url":    "https url or Unavailable",
  "company_website_url":  "https url or Unavailable",
  "company_linkedin_url": "https://www.linkedin.com/company/... or Unavailable",
  "company_crunchbase_url":"https://www.crunchbase.com/organization/... or Unavailable"
}`,
            ResolvedLinksSchema,
          );
        } catch (err) {
          console.error("Validation failed for", f.name, err);
          return null;
        }

        // Drop candidates whose identity cannot be confirmed against evidence.
        if (!resolved.identity_confirmed) {
          console.warn("Dropping unconfirmed candidate:", f.name, "-", resolved.confirmation_reasoning);
          return null;
        }

        // 2c. Screening / memo — feed the resolved links + evidence.
        try {
          const result = await runJson(
            `You are a rigorous VC analyst producing an evidence-backed investment memo. Score independently across three axes. Weight signals as follows:
- GitHub activity: 30%, ProductHunt traction: 25%, credible press / funding rounds: 20%, LinkedIn credibility: 15%, hackathon / community: 10%.
- Down-weight tweets, random blog posts, and low-authority sources when computing trust_score.
- For each claim, cite the exact source domain and provide a trust_score 0-1. Mark "unverifiable" / "flagged" when evidence is missing — NEVER fabricate. When evidence is missing, use the exact string "Unavailable" for any string field rather than inventing a value.`,
            `FOUNDER CANDIDATE (identity confirmed):
Name: ${f.name}
Company: ${f.company}
Role: ${f.role}
Location: ${f.location}
Stage: ${f.stage}
Sector: ${f.sector}
Background: ${f.background}
Signals: ${f.signals.join(", ")}
Primary source: ${f.source_url}

RESOLVED LINKS (knowledge graph):
- Founder LinkedIn: ${resolved.founder_linkedin_url}
- Founder GitHub:   ${resolved.founder_github_url}
- Founder Twitter:  ${resolved.founder_twitter_url}
- Personal site:    ${resolved.personal_site_url}
- Company site:     ${resolved.company_website_url}
- Company LinkedIn: ${resolved.company_linkedin_url}
- Crunchbase:       ${resolved.company_crunchbase_url}
Cross-reference note: ${resolved.confirmation_reasoning}

ADDITIONAL EVIDENCE:
${evidence}

VC THESIS: ${data.query}
Filters: sector=${data.sector ?? "any"}, stage=${data.stage ?? "any"}, geography=${data.geography ?? "any"}, check_size=${data.check_size ?? "any"}, risk=${data.risk ?? "any"}

Return JSON:
{
  "founder_axis": { "score": 0-10, "confidence": 0-1, "reasoning": "...", "key_factors": ["...", "..."] },
  "market_axis": { same shape },
  "fit_axis": { same shape },
  "composite_score": 0-10,
  "recommendation": "strong_pass" | "review" | "pass",
  "overall_trust_score": 0-1,
  "memo": {
    "thesis":   { "title": "Investment Thesis", "summary": "2-3 sentences", "claims": [ { "claim": "...", "trust_score": 0-1, "status": "verified|plausible|unverifiable|flagged", "evidence": "quote or paraphrase", "source": "domain or Unavailable" } ], "trace": ["step 1 reasoning", "step 2 reasoning", "..."] },
    "founder":  { same shape — team background, prior exits, technical depth },
    "market":   { same shape — TAM, growth, competition },
    "product":  { same shape — what they built, differentiation },
    "traction": { same shape — users, revenue, GitHub stars, PH votes },
    "risks":    { same shape — key risks and mitigations }
  },
  "cold_email_subject": "concise subject line",
  "cold_email_body": "3-paragraph personalized outreach email from a VC, referencing specific signals"
}`,
            ScreenedFounderSchema,
          );

          return { raw: f, resolved, screened: applyDeterministicTrust(result), id: `${slugify(f.name)}-${slugify(f.company)}` };
        } catch (err) {
          console.error("Screening failed for", f.name, err);
          return null;
        }
      }),
    );

    const results = screened
      .filter((x): x is NonNullable<typeof x> => x !== null)
      .map((x, i) => ({
        id: x.id,
        source: "outbound" as "outbound" | "inbound",
        rank: i + 1,
        ...x.raw,
        ...x.screened,
        links: x.resolved,
      }))
      .sort((a, b) => b.composite_score - a.composite_score);

    return {
      summary: sourced.summary,
      source_count: search.results.length,
      founders: results,
    };
  });

function slugify(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40);
}

// Inbound application → same screening pipeline
const ApplyInput = z.object({
  founder_name: z.string().min(1),
  company: z.string().min(1),
  role: z.string().min(1),
  location: z.string().min(1),
  stage: z.string().min(1),
  sector: z.string().min(1),
  pitch: z.string().min(20),
  deck_url: z.string().optional(),
  website: z.string().optional(),
});

export const submitInboundApplication = createServerFn({ method: "POST" })
  .inputValidator((input: unknown) => ApplyInput.parse(input))
  .handler(async ({ data }) => {
    const { tavilySearch } = await import("./tavily.server");

    // Enrich with web evidence about the applicant
    const evidenceSearch = await tavilySearch(
      `${data.founder_name} ${data.company} ${data.sector}`,
      { max_results: 6, search_depth: "basic" },
    ).catch(() => ({ results: [] as { url: string; title: string; content: string }[] }));

    const evidence = evidenceSearch.results
      .map((r, i) => `[${i + 1}] ${r.title} — ${r.url}\n${r.content.slice(0, 350)}`)
      .join("\n\n") || "(no external evidence found — flag claims as unverifiable)";

    const screened = await runJson(
      `You are a rigorous VC analyst screening an inbound founder application. Cross-reference the pitch against external evidence. Where evidence is absent, mark claims "unverifiable" or "flagged" — never fabricate. Weight GitHub / ProductHunt / credible press higher than social posts.`,
      `INBOUND APPLICATION:
Founder: ${data.founder_name}
Company: ${data.company}
Role: ${data.role}
Location: ${data.location}
Stage: ${data.stage}
Sector: ${data.sector}
Website: ${data.website ?? "none"}
Deck: ${data.deck_url ?? "none"}

PITCH:
${data.pitch}

EXTERNAL EVIDENCE:
${evidence}

Return the same JSON shape as the sourcing pipeline:
{
  "founder_axis": {...}, "market_axis": {...}, "fit_axis": {...},
  "composite_score": 0-10,
  "recommendation": "strong_pass" | "review" | "pass",
  "overall_trust_score": 0-1,
  "memo": { "thesis": {...}, "founder": {...}, "market": {...}, "product": {...}, "traction": {...}, "risks": {...} },
  "cold_email_subject": "reply subject",
  "cold_email_body": "personalized response"
}
Every memo section has: title, summary, claims:[{claim, trust_score, status, evidence, source}], trace:[strings].`,
      ScreenedFounderSchema,
    );

    return {
      id: `${slugify(data.founder_name)}-${slugify(data.company)}`,
      source: "inbound" as "outbound" | "inbound",
      rank: 1,
      name: data.founder_name,
      company: data.company,
      role: data.role,
      location: data.location,
      stage: data.stage,
      sector: data.sector,
      background: data.pitch.slice(0, 240),
      signals: [],
      source_url: data.website ?? data.deck_url ?? "",
      ...applyDeterministicTrust(screened),
      links: {
        identity_confirmed: true,
        confirmation_reasoning: "Self-declared via inbound application form.",
        cross_references: [],
        founder_linkedin_url: "Unavailable",
        founder_twitter_url: "Unavailable",
        founder_github_url: "Unavailable",
        personal_site_url: data.website ?? "Unavailable",
        company_website_url: data.website ?? "Unavailable",
        company_linkedin_url: "Unavailable",
        company_crunchbase_url: "Unavailable",
      },
    };
  });

export type SourceAndScreenResult = Awaited<ReturnType<typeof sourceAndScreen>>;
export type ScreenedFounder = SourceAndScreenResult["founders"][number];
