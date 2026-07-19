import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { getFounder, saveDecision } from "@/lib/founder-store";
import type { ScreenedFounder } from "@/lib/founders.functions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Send } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/invest/$id")({
  head: () => ({ meta: [{ title: "Investment proposal — Foundex" }, { name: "robots", content: "noindex" }] }),
  component: InvestPage,
});

function InvestPage() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const [founder, setFounder] = useState<ScreenedFounder | undefined>();
  useEffect(() => { setFounder(getFounder(id)); }, [id]);

  const [check, setCheck] = useState("500000");
  const [equity, setEquity] = useState("8");
  const [valuation, setValuation] = useState("6250000");
  const [structure, setStructure] = useState("SAFE (post-money)");
  const [proRata, setProRata] = useState("Yes — up to 2x on next round");
  const [boardRights, setBoardRights] = useState("Observer seat");
  const [conditions, setConditions] = useState("Reference checks, IP assignment, standard reps & warranties.");
  const [note, setNote] = useState("");

  if (!founder) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-16 text-center">
        <p className="text-muted-foreground">Founder not in local intel.</p>
        <Link to="/" className="inline-block mt-4"><Button>Back</Button></Link>
      </div>
    );
  }

  const send = () => {
    saveDecision({ id, verdict: "invest", at: new Date().toISOString(), note: `Check $${check} for ${equity}% @ $${valuation} valuation` });
    toast.success("Investment proposal recorded & marked ready to send");
    navigate({ to: "/founder/$id", params: { id } });
  };

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <Link to="/founder/$id" params={{ id }} className="mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground flex items-center gap-1">
        <ArrowLeft className="h-3 w-3" /> Back to memo
      </Link>

      <div className="mt-4 mono text-[10px] uppercase tracking-widest text-primary">Investment proposal</div>
      <h1 className="mt-1 text-3xl font-semibold tracking-tight">{founder.name} · {founder.company}</h1>
      <p className="mt-1 text-sm text-muted-foreground">Configure terms and send the proposal to the founder.</p>

      <div className="mt-8 grid md:grid-cols-2 gap-5">
        <Field label="Check size (USD)" value={check} onChange={setCheck} type="number" />
        <Field label="Equity target (%)" value={equity} onChange={setEquity} type="number" />
        <Field label="Valuation cap (USD)" value={valuation} onChange={setValuation} type="number" />
        <Field label="Investment structure" value={structure} onChange={setStructure} />
        <Field label="Pro-rata rights" value={proRata} onChange={setProRata} />
        <Field label="Board rights" value={boardRights} onChange={setBoardRights} />
      </div>

      <div className="mt-5 space-y-2">
        <Label className="mono text-[10px] uppercase tracking-widest text-muted-foreground">Closing conditions</Label>
        <Textarea rows={3} value={conditions} onChange={(e) => setConditions(e.target.value)} className="bg-card/60 border-border" />
      </div>

      <div className="mt-5 space-y-2">
        <Label className="mono text-[10px] uppercase tracking-widest text-muted-foreground">Personal note to founder</Label>
        <Textarea rows={4} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Why we want to back you…" className="bg-card/60 border-border" />
      </div>

      <div className="mt-8 flex items-center justify-between gap-3 pt-6 border-t border-border/60">
        <Button variant="outline" onClick={() => navigate({ to: "/founder/$id", params: { id } })}>Cancel</Button>
        <Button onClick={send}><Send className="h-3 w-3 mr-1" />Send investment proposal</Button>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (v: string) => void; type?: string }) {
  return (
    <div className="space-y-2">
      <Label className="mono text-[10px] uppercase tracking-widest text-muted-foreground">{label}</Label>
      <Input type={type} value={value} onChange={(e) => onChange(e.target.value)} className="bg-card/60 border-border" />
    </div>
  );
}
