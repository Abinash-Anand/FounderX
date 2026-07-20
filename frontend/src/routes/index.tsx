import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { useEffect, useRef, useState } from "react";
import { z } from "zod";
import { sourceAndScreen, type SourceAndScreenResult, type ScreenedFounder } from "@/lib/founders.functions";
import { saveFounders } from "@/lib/founder-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { ArrowRight, Loader2, Search, Sparkles, Mic, MicOff, ExternalLink } from "lucide-react";

const searchSchema = z.object({ q: z.string().optional() });

export const Route = createFileRoute("/")({
  validateSearch: (s) => searchSchema.parse(s),
  head: () => ({
    meta: [
      { title: "Discover founders — Foundex" },
      { name: "description", content: "Query the open web for real early-stage founders. Backend screening returns ranked, evidence-backed profiles." },
    ],
  }),
  component: DiscoverPage,
});

const SECTORS = ["AI/ML", "Fintech", "Climate", "Devtools", "Healthtech", "Consumer", "Crypto", "Bio"];
const STAGES = ["Pre-seed", "Seed", "Series A", "Bootstrapped", "No funding"];
const GEOS = ["USA", "Europe", "UK", "Asia", "Global", "Remote"];
const CHECKS = ["$50k-$250k", "$250k-$1M", "$1M-$3M", "$3M+"];
const RISKS = ["Low", "Medium", "High"];
const OWNERSHIP = ["1-5%", "5-10%", "10-20%", "20%+"];

type Filters = {
  sector: string;
  stage: string;
  geography: string;
  check_size: string;
  risk: string;
  ownership: string;
};

function DiscoverPage() {
  const navigate = useNavigate();
  const initial = Route.useSearch().q ?? "";
  const [query, setQuery] = useState(initial);
  const [filters, setFilters] = useState<Filters>({
    sector: "", stage: "", geography: "", check_size: "", risk: "", ownership: "",
  });
  const source = useServerFn(sourceAndScreen);

  const m = useMutation({
    mutationFn: (q: string) => source({
      data: {
        query: q,
        sector: filters.sector || undefined,
        stage: filters.stage || undefined,
        geography: filters.geography || undefined,
        check_size: filters.check_size || undefined,
        risk: filters.risk || undefined,
        ownership: filters.ownership || undefined,
        limit: 6,
      },
    }),
    onSuccess: (r: SourceAndScreenResult) => { if (r?.founders?.length) saveFounders(r.founders); },
    onError: (e: Error) => toast.error(e.message ?? "Search failed"),
  });

  const submit = (q: string) => {
    if (!q.trim()) {
      toast.error("Enter a thesis query or filter");
      return;
    }
    navigate({ to: "/", search: { q } });
    m.mutate(q.trim());
  };

  const data = m.data as SourceAndScreenResult | undefined;
  const shown: ScreenedFounder[] = (data?.founders ?? []).filter((f) => {
    const n = (f.name ?? "").trim();
    return n.length >= 3 && /[A-Za-z]/.test(n) && n.split(/\s+/).filter(Boolean).length >= 2 && !/^unavailable$/i.test(n) && !/^unknown$/i.test(n);
  });

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-border/60">
        <div className="absolute inset-0 grid-bg opacity-40 [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_75%)]" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-background pointer-events-none" />
        <div className="relative mx-auto max-w-5xl px-6 pt-16 pb-12 text-center">
          <div className="mono inline-flex items-center gap-2 rounded-full border border-border/70 bg-card/50 px-3 py-1 text-[10px] uppercase tracking-widest text-muted-foreground">
            <Sparkles className="h-3 w-3 text-primary" />
            Thesis engine · Backend screening · Trust-scored memos
          </div>
          <h1 className="mt-6 text-5xl md:text-6xl font-semibold tracking-tight" style={{ fontFamily: "'Instrument Serif', serif", fontWeight: 400 }}>
            Find the next moonshot startup <span className="text-primary italic">before anybody else does</span>.
          </h1>
          <p className="mt-4 text-base text-muted-foreground max-w-2xl mx-auto">
            Configure your thesis with filters or type it in plain English. Foundex sources and screens founders on the backend — you see only ranked, evidence-backed results.
          </p>

          {/* Search bar */}
          <form
            className="mt-8 flex items-center gap-2 mx-auto max-w-3xl rounded-xl border border-border bg-card/80 p-1.5 shadow-2xl shadow-black/40"
            onSubmit={(e) => { e.preventDefault(); submit(query); }}
          >
            <div className="pl-3 text-muted-foreground"><Search className="h-4 w-4" /></div>
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Solo AI devtools founders raising pre-seed"
              className="flex-1 border-0 bg-transparent shadow-none focus-visible:ring-0 text-base"
            />
            <VoiceButton onTranscript={(t: string) => setQuery((q: string) => (q ? q + " " : "") + t)} />
            <Button type="submit" disabled={m.isPending} className="rounded-lg">
              {m.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <>Source & screen <ArrowRight className="ml-1 h-4 w-4" /></>}
            </Button>
          </form>

          {/* Filter presets */}
          <div className="mt-5 grid grid-cols-2 md:grid-cols-3 gap-3 max-w-3xl mx-auto text-left">
            <FilterSelect label="Sector" value={filters.sector} options={SECTORS} onChange={(v) => setFilters((f) => ({ ...f, sector: v }))} />
            <FilterSelect label="Stage" value={filters.stage} options={STAGES} onChange={(v) => setFilters((f) => ({ ...f, stage: v }))} />
            <FilterSelect label="Geography" value={filters.geography} options={GEOS} onChange={(v) => setFilters((f) => ({ ...f, geography: v }))} />
            <FilterSelect label="Check size" value={filters.check_size} options={CHECKS} onChange={(v) => setFilters((f) => ({ ...f, check_size: v }))} />
            <FilterSelect label="Risk" value={filters.risk} options={RISKS} onChange={(v) => setFilters((f) => ({ ...f, risk: v }))} />
            <FilterSelect label="Ownership" value={filters.ownership} options={OWNERSHIP} onChange={(v) => setFilters((f) => ({ ...f, ownership: v }))} />
          </div>
        </div>
      </section>

      {/* Results */}
      <section className="mx-auto max-w-7xl px-6 py-10">
        {m.isPending && <LoadingIntel />}
        {m.isError && (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-6 text-sm text-destructive">
            {(m.error as Error).message}
          </div>
        )}
        {!m.isPending && shown.length > 0 && (
          <>
            <div className="flex items-baseline justify-between mb-6 border-b border-border/60 pb-3">
              <div>
                <div className="mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  Fresh intel
                </div>
                <h2 className="mt-1 text-xl font-semibold tracking-tight">
                  {shown.length} founder{shown.length === 1 ? "" : "s"} · screened & ranked
                </h2>
              </div>
              {data?.source_count != null && (
                <div className="mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  {data.source_count} sources scanned
                </div>
              )}
            </div>
            {data?.summary && (
              <p className="mb-6 text-sm text-muted-foreground italic border-l-2 border-primary/60 pl-4">{data.summary}</p>
            )}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {shown.map((f, i) => <FounderCard key={f.id} f={f} rank={i + 1} />)}
            </div>
          </>
        )}
        {!m.isPending && shown.length === 0 && <EmptyState />}
      </section>
    </div>
  );
}

function FilterSelect({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <div>
      <Label className="mono text-[10px] uppercase tracking-widest text-muted-foreground">{label}</Label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1.5 w-full rounded-md border border-border bg-card/60 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
      >
        <option value="">Any</option>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

// Web Speech API voice input
function VoiceButton({ onTranscript }: { onTranscript: (text: string) => void }) {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(true);
  const recRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setSupported(false); return; }
  }, []);

  const toggle = () => {
    if (!supported) { toast.error("Voice input not supported in this browser"); return; }
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (listening) { recRef.current?.stop(); return; }
    const rec = new SR();
    rec.lang = "en-US"; rec.continuous = false; rec.interimResults = false;
    rec.onresult = (e: any) => {
      const t = Array.from(e.results).map((r: any) => r[0].transcript).join(" ");
      onTranscript(t);
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recRef.current = rec;
    setListening(true);
    rec.start();
  };

  return (
    <Button type="button" variant="ghost" size="sm" onClick={toggle} className="rounded-lg" aria-label="Voice input">
      {listening ? <MicOff className="h-4 w-4 text-destructive" /> : <Mic className="h-4 w-4" />}
    </Button>
  );
}

function LoadingIntel() {
  return (
    <div className="mono text-xs uppercase tracking-widest text-muted-foreground">
      <div className="flex items-center gap-2">
        <Loader2 className="h-3 w-3 animate-spin text-primary" />
        Sourcing · Screening on backend · Composing memos · Trust-scoring claims
      </div>
      <div className="mt-6 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-52 rounded-lg border border-border bg-card/50 animate-pulse" style={{ animationDelay: `${i * 80}ms` }} />
        ))}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-border bg-card/30 p-10 text-center">
      <div className="mono text-[10px] uppercase tracking-widest text-muted-foreground">Awaiting thesis</div>
      <p className="mt-2 text-sm text-muted-foreground">Configure filters or type a query. Results appear ranked here.</p>
    </div>
  );
}

function isKnown(v?: string): v is string {
  if (!v) return false;
  const t = v.trim();
  return t.length > 0 && !/^unavailable$/i.test(t) && !/^unknown$/i.test(t);
}

function FounderCard({ f, rank }: { f: ScreenedFounder; rank: number }) {
  const scoreColor = f.composite_score >= 8 ? "text-success" : f.composite_score >= 6 ? "text-primary" : f.composite_score >= 4 ? "text-accent" : "text-muted-foreground";
  const sourceColor = f.source === "outbound" ? "bg-accent/20 text-accent border-accent/40" : "bg-primary/20 text-primary border-primary/40";
  const founderLink = isKnown(f.links?.founder_linkedin_url) ? f.links.founder_linkedin_url
    : isKnown(f.links?.personal_site_url) ? f.links.personal_site_url
    : isKnown(f.links?.founder_github_url) ? f.links.founder_github_url
    : isKnown(f.links?.founder_twitter_url) ? f.links.founder_twitter_url
    : null;
  const companyLink = isKnown(f.links?.company_website_url) ? f.links.company_website_url
    : isKnown(f.links?.company_linkedin_url) ? f.links.company_linkedin_url
    : isKnown(f.links?.company_crunchbase_url) ? f.links.company_crunchbase_url
    : null;
  return (
    <div className="group rounded-lg border border-border bg-card/60 hover:border-primary/50 hover:bg-card transition-all p-5 flex flex-col">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="mono text-[10px] text-muted-foreground">#{String(rank).padStart(2, "0")}</span>
          <span className={`mono text-[9px] uppercase tracking-widest border rounded-sm px-1.5 py-0.5 ${sourceColor}`}>{f.source}</span>
        </div>
        <div className={`mono text-3xl font-semibold tabular-nums ${scoreColor}`}>{f.composite_score.toFixed(1)}</div>
      </div>
      <h3 className="mt-3 text-lg font-semibold tracking-tight truncate">
        {founderLink ? (
          <a href={founderLink} target="_blank" rel="noreferrer" className="hover:text-primary inline-flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            {f.name} <ExternalLink className="h-3 w-3 opacity-60" />
          </a>
        ) : f.name}
      </h3>
      <div className="text-sm text-muted-foreground truncate">
        {f.role} @{" "}
        {companyLink ? (
          <a href={companyLink} target="_blank" rel="noreferrer" className="text-foreground/90 hover:text-primary inline-flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            {f.company} <ExternalLink className="h-3 w-3 opacity-60" />
          </a>
        ) : <span className="text-foreground/90">{f.company}</span>}
      </div>
      <div className="mt-1 flex flex-wrap gap-x-2 gap-y-0.5 mono text-[10px] uppercase tracking-wider text-muted-foreground">
        <span>{f.location}</span><span className="opacity-40">·</span><span>{f.stage}</span><span className="opacity-40">·</span><span>{f.sector}</span>
      </div>
      <p className="mt-3 text-xs text-foreground/80 line-clamp-3 flex-1">{f.background}</p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {f.signals.slice(0, 3).map((s, i) => (
          <Badge key={i} variant="secondary" className="mono text-[10px] font-normal bg-secondary/70 border border-border/50">{s}</Badge>
        ))}
      </div>
      <div className="mt-4 flex items-center justify-between pt-3 border-t border-border/50">
        <div className="mono text-[10px] uppercase tracking-widest text-muted-foreground">
          Trust {(f.overall_trust_score * 100).toFixed(0)}%
        </div>
        <Link to="/founder/$id" params={{ id: f.id }} className="mono text-[10px] uppercase tracking-widest text-primary hover:text-primary/80 flex items-center gap-1">
          See more <ExternalLink className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}
