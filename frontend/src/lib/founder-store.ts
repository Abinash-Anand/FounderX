import type { ScreenedFounder } from "./founders.functions";

const KEY = "foundex.founders.v1";

export function saveFounders(founders: ScreenedFounder[]) {
  if (typeof window === "undefined") return;
  const existing = loadFounders();
  const map = new Map(existing.map((f) => [f.id, f]));
  for (const f of founders) map.set(f.id, f);
  localStorage.setItem(KEY, JSON.stringify([...map.values()]));
}

export function loadFounders(): ScreenedFounder[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as ScreenedFounder[]) : [];
  } catch {
    return [];
  }
}

export function getFounder(id: string): ScreenedFounder | undefined {
  return loadFounders().find((f) => f.id === id);
}

const DECISION_KEY = "foundex.decisions.v1";
export type Decision = { id: string; verdict: "invest" | "reject"; at: string; note?: string };

export function saveDecision(d: Decision) {
  if (typeof window === "undefined") return;
  const all = loadDecisions().filter((x) => x.id !== d.id);
  all.push(d);
  localStorage.setItem(DECISION_KEY, JSON.stringify(all));
}

export function loadDecisions(): Decision[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(DECISION_KEY);
    return raw ? (JSON.parse(raw) as Decision[]) : [];
  } catch {
    return [];
  }
}

export function getDecision(id: string): Decision | undefined {
  return loadDecisions().find((d) => d.id === id);
}
