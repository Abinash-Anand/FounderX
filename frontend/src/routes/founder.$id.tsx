import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { getFounder, saveDecision, getDecision } from "@/lib/founder-store";
import type { ScreenedFounder } from "@/lib/founders.functions";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card";
import { ChevronDown, ChevronRight, Mail, Download, ArrowLeft, ShieldCheck, ShieldAlert, ExternalLink, Linkedin, Github, Twitter, Globe, Building2, Info } from "lucide-react";
import { toast } from "sonner";
import { SOURCE_TIERS, STATUS_MULTIPLIER, AXIS_WEIGHTS, SIGNAL_WEIGHTS, domainWeight } from "@/lib/trust-weights";

export const Route = createFileRoute("/founder/$id")({
  head: () => ({ meta: [{ title: "Founder detail — Foundex" }, { name: "robots", content: "noindex" }] }),
  component: FounderDetail,
});

function FounderDetail() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const [founder, setFounder] = useState<ScreenedFounder | undefined>();
  const [decision, setDecision] = useState<ReturnType<typeof getDecision>>();

  useEffect(() => {
    setFounder(getFounder(id));
    setDecision(getDecision(id));
  }, [id]);

  if (!founder) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16 text-center">
        <div className="mono text-xs text-muted-foreground uppercase tracking-widest">Not in local intel</div>
        <h1 className="mt-3 text-2xl font-semibold">Founder not found</h1>
        <p className="mt-2 text-sm text-muted-foreground">Run a discovery query first — this founder isn't in your local intel cache.</p>
        <Link to="/" className="inline-block mt-6"><Button>Back to Discover</Button></Link>
      </div>
    );
  }

  const sourceColor = founder.source === "outbound" ? "bg-accent/20 text-accent border-accent/40" : "bg-primary/20 text-primary border-primary/40";
  const initials = founder.name.split(" ").map((s) => s[0]).join("").slice(0, 2).toUpperCase();
  const scoreColor = founder.composite_score >= 8 ? "text-success" : founder.composite_score >= 6 ? "text-primary" : founder.composite_score >= 4 ? "text-accent" : "text-muted-foreground";

  const handleReject = () => {
    saveDecision({ id, verdict: "reject", at: new Date().toISOString() });
    setDecision(getDecision(id));
    toast.success("Marked as reject");
  };

  const openEmail = () => {
    const mailto = `mailto:?subject=${encodeURIComponent(founder.cold_email_subject)}&body=${encodeURIComponent(founder.cold_email_body)}`;
    window.location.href = mailto;
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-8" id="memo-print-area">
      <div className="mb-4 flex items-center justify-between print:hidden">
        <Link to="/" className="mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground flex items-center gap-1">
          <ArrowLeft className="h-3 w-3" /> Back
        </Link>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => window.print()}><Download className="h-3 w-3 mr-1" />Export PDF</Button>
        </div>
      </div>

      {/* Header card */}
      <div className={`rounded-lg border p-6 ${founder.source === "outbound" ? "border-accent/40 bg-accent/5" : "border-primary/40 bg-primary/5"}`}>
        <div className={`mono text-[10px] uppercase tracking-widest inline-block rounded-sm border px-2 py-0.5 ${sourceColor}`}>{founder.source}</div>
        <div className="mt-4 flex flex-col md:flex-row gap-6 items-start">
          <div className={`flex h-24 w-24 items-center justify-center rounded-lg mono text-3xl font-bold shrink-0 ${founder.source === "outbound" ? "bg-accent/30 text-accent-foreground" : "bg-primary/30 text-primary-foreground"}`}>
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-3xl font-semibold tracking-tight">
              {founder.links && isKnown(founder.links.founder_linkedin_url) ? (
                <a href={founder.links.founder_linkedin_url} target="_blank" rel="noreferrer" className="hover:text-primary inline-flex items-center gap-2">
                  {founder.name} <ExternalLink className="h-4 w-4 opacity-60" />
                </a>
              ) : founder.name}
            </h1>
            <div className="text-muted-foreground">
              {founder.role} @{" "}
              {founder.links && isKnown(founder.links.company_website_url) ? (
                <a href={founder.links.company_website_url} target="_blank" rel="noreferrer" className="text-foreground font-medium hover:text-primary inline-flex items-center gap-1">
                  {founder.company} <ExternalLink className="h-3 w-3 opacity-60" />
                </a>
              ) : founder.links && isKnown(founder.links.company_linkedin_url) ? (
                <a href={founder.links.company_linkedin_url} target="_blank" rel="noreferrer" className="text-foreground font-medium hover:text-primary inline-flex items-center gap-1">
                  {founder.company} <ExternalLink className="h-3 w-3 opacity-60" />
                </a>
              ) : <span className="text-foreground font-medium">{founder.company}</span>}
            </div>
            <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 mono text-[10px] uppercase tracking-wider text-muted-foreground">
              <span>{founder.location}</span><span>·</span><span>{founder.stage}</span><span>·</span><span>{founder.sector}</span>
              {founder.source_url && (
                <a href={founder.source_url} target="_blank" rel="noreferrer" className="text-primary hover:underline flex items-center gap-1">
                  Source <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
            {founder.links && <LinksRow links={founder.links} />}
            <p className="mt-3 text-sm text-foreground/90">{founder.background}</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {founder.signals.map((s, i) => (
                <Badge key={i} variant="secondary" className="mono text-[10px] font-normal bg-secondary/70 border border-border/50">{s}</Badge>
              ))}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1 shrink-0">
            <div className="flex items-center gap-1.5">
              <div className={`mono text-5xl font-semibold tabular-nums ${scoreColor}`}>{founder.composite_score.toFixed(1)}</div>
              <CompositeInfo />
            </div>
            <div className="mono text-[9px] uppercase tracking-widest text-muted-foreground">Composite / 10</div>
            <div className="mt-2 mono text-[10px] uppercase tracking-widest text-muted-foreground flex items-center gap-1">
              Trust {(founder.overall_trust_score * 100).toFixed(0)}%
              <TrustInfo />
            </div>
          </div>
        </div>
        {founder.source === "outbound" && (
          <div className="mt-5 pt-4 border-t border-border/60 flex items-center justify-between gap-3 print:hidden">
            <div className="text-xs text-muted-foreground">Outbound target — no relationship yet. Trigger cold outreach.</div>
            <Button size="sm" variant="outline" onClick={openEmail}><Mail className="h-3 w-3 mr-1" />Cold outreach</Button>
          </div>
        )}
      </div>

      {/* Axes */}
      <div className="mt-6 grid md:grid-cols-3 gap-3">
        <AxisMini title="Founder" axis={founder.founder_axis} />
        <AxisMini title="Market" axis={founder.market_axis} />
        <AxisMini title="Fit" axis={founder.fit_axis} />
      </div>

      {/* Memo */}
      <div className="mt-8">
        <div className="mono text-[10px] uppercase tracking-widest text-primary">Investment memo</div>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight">Evidence-backed analysis</h2>
        <p className="text-sm text-muted-foreground mt-1">Expand any section to see the chain-of-thought and per-claim trust scores.</p>
        <div className="mt-5 space-y-3">
          <MemoSection title="Thesis" section={founder.memo.thesis} />
          <MemoSection title="Founder" section={founder.memo.founder} />
          <MemoSection title="Market" section={founder.memo.market} />
          <MemoSection title="Product" section={founder.memo.product} />
          <MemoSection title="Traction" section={founder.memo.traction} />
          <MemoSection title="Risks" section={founder.memo.risks} />
        </div>
      </div>

      {/* Decision */}
      <div className="mt-10 rounded-lg border border-border bg-card/60 p-6 print:hidden">
        {decision ? (
          <div className="flex items-center justify-between">
            <div>
              <div className="mono text-[10px] uppercase tracking-widest text-muted-foreground">Decision recorded</div>
              <div className="mt-1 text-lg font-semibold">
                {decision.verdict === "invest" ? <span className="text-success">Invest</span> : <span className="text-destructive">Reject</span>}
              </div>
              <div className="mono text-[10px] uppercase tracking-widest text-muted-foreground">{new Date(decision.at).toLocaleString()}</div>
            </div>
            {decision.verdict === "invest" && (
              <Button variant="outline" onClick={() => navigate({ to: "/invest/$id", params: { id } })}>Open proposal</Button>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="mono text-[10px] uppercase tracking-widest text-muted-foreground">Decision</div>
              <p className="text-sm text-muted-foreground">Move this founder into the pipeline or reject.</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleReject}>Reject</Button>
              <Button onClick={() => navigate({ to: "/invest/$id", params: { id } })}>Invest</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function AxisMini({ title, axis }: { title: string; axis: ScreenedFounder["founder_axis"] }) {
  const color = axis.score >= 8 ? "text-success" : axis.score >= 6 ? "text-primary" : axis.score >= 4 ? "text-accent" : "text-muted-foreground";
  return (
    <div className="rounded-lg border border-border bg-card/60 p-4">
      <div className="flex items-center justify-between">
        <div className="mono text-[10px] uppercase tracking-widest text-muted-foreground">{title}</div>
        <div className={`mono text-2xl font-semibold tabular-nums ${color}`}>{axis.score.toFixed(1)}</div>
      </div>
      <div className="mono text-[9px] uppercase tracking-widest text-muted-foreground">conf {(axis.confidence * 100).toFixed(0)}%</div>
      <p className="mt-2 text-xs text-foreground/85">{axis.reasoning}</p>
    </div>
  );
}

function MemoSection({ title, section }: { title: string; section: ScreenedFounder["memo"]["thesis"] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg border border-border bg-card/60">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-start justify-between gap-4 p-5 text-left"
      >
        <div className="flex-1 min-w-0">
          <div className="mono text-[10px] uppercase tracking-widest text-primary">{title}</div>
          <h3 className="mt-1 text-base font-semibold tracking-tight">{section.title}</h3>
          <p className="mt-1.5 text-sm text-foreground/90">{section.summary}</p>
        </div>
        <div className="mono text-[10px] uppercase tracking-widest text-muted-foreground shrink-0 flex items-center gap-1">
          Trace {open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        </div>
      </button>
      {open && (
        <div className="border-t border-border/60 p-5 space-y-4">
          <div>
            <div className="mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">Chain of thought</div>
            <ol className="space-y-1.5">
              {section.trace.map((t, i) => (
                <li key={i} className="flex gap-3 text-xs text-foreground/85">
                  <span className="mono text-[10px] text-primary tabular-nums shrink-0 mt-0.5">{String(i + 1).padStart(2, "0")}</span>
                  <span>{t}</span>
                </li>
              ))}
            </ol>
          </div>
          <div>
            <div className="mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">Claims & trust</div>
            <div className="space-y-2">
              {section.claims.map((c, i) => <ClaimRow key={i} claim={c} />)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ClaimRow({ claim }: { claim: ScreenedFounder["memo"]["thesis"]["claims"][number] }) {
  const trust = claim.trust_score;
  const trustColor = trust >= 0.75 ? "text-success" : trust >= 0.5 ? "text-primary" : trust >= 0.25 ? "text-accent" : "text-destructive";
  const Icon = trust >= 0.5 ? ShieldCheck : ShieldAlert;
  const statusColor: Record<typeof claim.status, string> = {
    verified: "border-success/40 text-success bg-success/10",
    plausible: "border-primary/40 text-primary bg-primary/10",
    unverifiable: "border-muted-foreground/40 text-muted-foreground bg-muted/40",
    flagged: "border-destructive/40 text-destructive bg-destructive/10",
  };
  return (
    <div className="rounded-md border border-border/60 bg-background/40 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="text-sm text-foreground/95">{claim.claim}</div>
          <div className="mt-1 text-xs text-muted-foreground italic">"{claim.evidence}"</div>
          <div className="mt-1 mono text-[10px] uppercase tracking-widest text-muted-foreground">source: {claim.source}</div>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <HoverCard>
            <HoverCardTrigger asChild>
              <button className={`flex items-center gap-1 mono text-xs font-semibold ${trustColor} cursor-help`}>
                <Icon className="h-3 w-3" />{(trust * 100).toFixed(0)}%
                <Info className="h-3 w-3 opacity-60" />
              </button>
            </HoverCardTrigger>
            <HoverCardContent className="w-72 text-xs">
              <ClaimTrustBreakdown source={claim.source} status={claim.status} />
            </HoverCardContent>
          </HoverCard>
          <span className={`mono text-[9px] uppercase tracking-widest border rounded-sm px-1.5 py-0.5 ${statusColor[claim.status]}`}>{claim.status}</span>
        </div>
      </div>
    </div>
  );
}

function isKnown(v?: string): v is string {
  if (!v) return false;
  const t = v.trim();
  return t.length > 0 && !/^unavailable$/i.test(t) && !/^unknown$/i.test(t);
}

function LinksRow({ links }: { links: NonNullable<ScreenedFounder["links"]> }) {
  const items: { url: string; label: string; Icon: typeof Linkedin }[] = [];
  if (isKnown(links.founder_linkedin_url)) items.push({ url: links.founder_linkedin_url, label: "LinkedIn", Icon: Linkedin });
  if (isKnown(links.founder_github_url)) items.push({ url: links.founder_github_url, label: "GitHub", Icon: Github });
  if (isKnown(links.founder_twitter_url)) items.push({ url: links.founder_twitter_url, label: "Twitter", Icon: Twitter });
  if (isKnown(links.personal_site_url)) items.push({ url: links.personal_site_url, label: "Site", Icon: Globe });
  if (isKnown(links.company_website_url)) items.push({ url: links.company_website_url, label: "Company", Icon: Globe });
  if (isKnown(links.company_linkedin_url)) items.push({ url: links.company_linkedin_url, label: "Co. LinkedIn", Icon: Building2 });
  if (isKnown(links.company_crunchbase_url)) items.push({ url: links.company_crunchbase_url, label: "Crunchbase", Icon: ExternalLink });
  if (items.length === 0) {
    return <div className="mt-3 mono text-[10px] uppercase tracking-widest text-muted-foreground">Verified links: unavailable</div>;
  }
  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {items.map((it) => (
        <a key={it.url} href={it.url} target="_blank" rel="noreferrer"
          className="inline-flex items-center gap-1.5 rounded-md border border-border bg-background/60 px-2 py-1 mono text-[10px] uppercase tracking-widest text-foreground/80 hover:text-primary hover:border-primary/50">
          <it.Icon className="h-3 w-3" /> {it.label}
        </a>
      ))}
    </div>
  );
}

function InfoIcon() {
  return <Info className="h-3 w-3 opacity-60 cursor-help" />;
}

function CompositeInfo() {
  return (
    <HoverCard>
      <HoverCardTrigger asChild><button aria-label="How the composite score is computed"><InfoIcon /></button></HoverCardTrigger>
      <HoverCardContent className="w-80 text-xs">
        <div className="mono text-[10px] uppercase tracking-widest text-primary mb-2">Composite recipe</div>
        <p className="text-muted-foreground mb-2">The composite blends three model-scored axes with these weights:</p>
        <ul className="space-y-1 mb-3">
          {AXIS_WEIGHTS.map((a) => (
            <li key={a.label} className="flex items-baseline justify-between gap-2">
              <span><span className="font-medium">{a.label}</span> <span className="text-muted-foreground">— {a.description}</span></span>
              <span className="mono tabular-nums text-primary">{(a.weight * 100).toFixed(0)}%</span>
            </li>
          ))}
        </ul>
        <div className="mono text-[10px] uppercase tracking-widest text-primary mb-1">Signal weights used during sourcing</div>
        <ul className="space-y-0.5">
          {SIGNAL_WEIGHTS.map((s) => (
            <li key={s.label} className="flex justify-between gap-2">
              <span>{s.label}</span>
              <span className="mono tabular-nums text-muted-foreground">{(s.weight * 100).toFixed(0)}%</span>
            </li>
          ))}
        </ul>
      </HoverCardContent>
    </HoverCard>
  );
}

function TrustInfo() {
  return (
    <HoverCard>
      <HoverCardTrigger asChild><button aria-label="How trust scores are computed"><InfoIcon /></button></HoverCardTrigger>
      <HoverCardContent className="w-96 text-xs">
        <div className="mono text-[10px] uppercase tracking-widest text-primary mb-1">Trust formula</div>
        <p className="text-muted-foreground mb-2">
          Each claim's trust = <span className="mono text-foreground">source-tier weight × status multiplier</span>. The overall trust % is the mean across all memo claims. This is deterministic — no LLM guesswork.
        </p>
        <div className="mono text-[10px] uppercase tracking-widest text-primary mb-1">Source tiers</div>
        <ul className="space-y-0.5 mb-2">
          {SOURCE_TIERS.map((t) => (
            <li key={t.tier} className="flex justify-between gap-2">
              <span>{t.tier} <span className="text-muted-foreground">({t.examples.slice(0, 2).join(", ")})</span></span>
              <span className="mono tabular-nums text-primary">{(t.weight * 100).toFixed(0)}%</span>
            </li>
          ))}
        </ul>
        <div className="mono text-[10px] uppercase tracking-widest text-primary mb-1">Status multipliers</div>
        <ul className="space-y-0.5">
          {(Object.keys(STATUS_MULTIPLIER) as (keyof typeof STATUS_MULTIPLIER)[]).map((k) => (
            <li key={k} className="flex justify-between gap-2">
              <span className="capitalize">{k}</span>
              <span className="mono tabular-nums text-muted-foreground">×{STATUS_MULTIPLIER[k].toFixed(2)}</span>
            </li>
          ))}
        </ul>
      </HoverCardContent>
    </HoverCard>
  );
}

function ClaimTrustBreakdown({ source, status }: { source: string; status: "verified" | "plausible" | "unverifiable" | "flagged" }) {
  const { tier, matched } = domainWeight(source);
  const mult = STATUS_MULTIPLIER[status];
  const result = Math.max(0, Math.min(1, tier.weight * mult));
  return (
    <div>
      <div className="mono text-[10px] uppercase tracking-widest text-primary mb-1">Trust breakdown</div>
      <div className="space-y-1">
        <div className="flex justify-between gap-2">
          <span className="text-muted-foreground">Source</span>
          <span className="font-mono truncate max-w-[180px]">{source || "Unavailable"}</span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-muted-foreground">Tier</span>
          <span>{tier.tier} <span className="text-muted-foreground">({matched})</span></span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-muted-foreground">Tier weight</span>
          <span className="mono tabular-nums">{tier.weight.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-muted-foreground">Status × </span>
          <span className="mono tabular-nums">{mult.toFixed(2)} <span className="text-muted-foreground">({status})</span></span>
        </div>
        <div className="flex justify-between gap-2 border-t border-border/60 pt-1 mt-1">
          <span className="font-medium">Trust</span>
          <span className="mono tabular-nums text-primary">{(result * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}
