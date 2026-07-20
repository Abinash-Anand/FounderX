import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { useState } from "react";
import { submitInboundApplication } from "@/lib/founders.functions";
import { saveFounders } from "@/lib/founder-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Send } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/apply")({
  head: () => ({
    meta: [
      { title: "Apply — Foundex" },
      { name: "description", content: "Founders: apply to be discovered and evaluated. Submit your deck and details; Foundex screens you and puts you in front of aligned VCs." },
    ],
  }),
  component: ApplyPage,
});

function ApplyPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    founder_name: "", company: "", role: "Co-founder & CEO", location: "",
    stage: "Pre-seed", sector: "", pitch: "", deck_url: "", website: "",
  });
  const submit = useServerFn(submitInboundApplication);
  const m = useMutation({
    mutationFn: () => submit({ data: form }),
    onSuccess: (data) => {
      // The inbound founder gets pushed into the same pool
      saveFounders([{ ...data, source: "inbound" }]);
      toast.success("Application submitted & screened");
      navigate({ to: "/founder/$id", params: { id: data.id } });
    },
    onError: (e: Error) => toast.error(e.message ?? "Submission failed"),
  });

  const set = (k: keyof typeof form) => (v: string) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <div className="mono text-[10px] uppercase tracking-widest text-primary">Founder inbound</div>
      <h1 className="mt-2 text-4xl font-semibold tracking-tight" style={{ fontFamily: "'Instrument Serif', serif", fontWeight: 400 }}>
        Apply to be seen by aligned VCs.
      </h1>
      <p className="mt-2 text-sm text-muted-foreground max-w-xl">
        Your application enters the same screening pipeline as our outbound sourcing. You'll get an evidence-backed memo and trust score — visible to funds whose thesis you match.
      </p>

      <form
        className="mt-8 grid md:grid-cols-2 gap-5"
        onSubmit={(e) => {
          e.preventDefault();
          if (!form.founder_name || !form.company || !form.pitch) { toast.error("Fill required fields"); return; }
          m.mutate();
        }}
      >
        <F label="Your name *" value={form.founder_name} onChange={set("founder_name")} />
        <F label="Company *" value={form.company} onChange={set("company")} />
        <F label="Role" value={form.role} onChange={set("role")} />
        <F label="Location" value={form.location} onChange={set("location")} placeholder="City, Country" />
        <F label="Stage" value={form.stage} onChange={set("stage")} />
        <F label="Sector" value={form.sector} onChange={set("sector")} placeholder="AI/ML, Fintech…" />
        <F label="Website" value={form.website} onChange={set("website")} placeholder="https://…" />
        <F label="Deck URL" value={form.deck_url} onChange={set("deck_url")} placeholder="Public link to pitch deck" />

        <div className="md:col-span-2 space-y-2">
          <Label className="mono text-[10px] uppercase tracking-widest text-muted-foreground">Pitch *</Label>
          <Textarea
            rows={8} value={form.pitch} onChange={(e) => set("pitch")(e.target.value)}
            placeholder="What are you building? Who's it for? Traction, team, funding history, why now."
            className="bg-card/60 border-border resize-none"
          />
        </div>

        <div className="md:col-span-2 flex justify-end pt-3 border-t border-border/60">
          <Button type="submit" disabled={m.isPending}>
            {m.isPending ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />Screening…</> : <><Send className="h-3 w-3 mr-1" />Submit application</>}
          </Button>
        </div>
      </form>
    </div>
  );
}

function F({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <div className="space-y-2">
      <Label className="mono text-[10px] uppercase tracking-widest text-muted-foreground">{label}</Label>
      <Input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="bg-card/60 border-border" />
    </div>
  );
}
