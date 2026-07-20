export interface TavilyResult {
  url: string;
  title: string;
  content: string;
  score?: number;
}

export interface TavilyResponse {
  results: TavilyResult[];
  answer?: string;
}

export async function tavilySearch(query: string, opts: { max_results?: number; search_depth?: "basic" | "advanced"; include_answer?: boolean } = {}): Promise<TavilyResponse> {
  const key = process.env.TAVILY_API_KEY;
  if (!key) throw new Error("Missing TAVILY_API_KEY");

  const resp = await fetch("https://api.tavily.com/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      api_key: key,
      query,
      max_results: opts.max_results ?? 8,
      search_depth: opts.search_depth ?? "basic",
      include_answer: opts.include_answer ?? false,
    }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Tavily error ${resp.status}: ${text.slice(0, 200)}`);
  }
  return (await resp.json()) as TavilyResponse;
}
