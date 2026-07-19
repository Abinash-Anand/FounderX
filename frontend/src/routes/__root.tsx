import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";
import { Toaster } from "@/components/ui/sonner";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <div className="mono text-xs text-primary tracking-widest">ERR/404</div>
        <h1 className="mt-3 text-6xl font-semibold tracking-tight">Signal lost</h1>
        <p className="mt-3 text-sm text-muted-foreground">The intel you're looking for isn't in the system.</p>
        <div className="mt-6">
          <Link to="/" className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
            Return to dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <div className="mono text-xs text-destructive tracking-widest">ERR/RUNTIME</div>
        <h1 className="mt-3 text-2xl font-semibold">This view didn't load</h1>
        <p className="mt-2 text-sm text-muted-foreground">Something went wrong. Try again or head back to the dashboard.</p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => { router.invalidate(); reset(); }}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >Try again</button>
          <a href="/" className="rounded-md border border-border bg-background px-4 py-2 text-sm font-medium hover:bg-accent">Dashboard</a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Foundex — Founder intelligence for early-stage investors" },
      { name: "description", content: "Source, screen, and validate real founders with evidence-backed memos and trust scores. Notion-approachable, Bloomberg-deep." },
      { name: "author", content: "Foundex" },
      { property: "og:title", content: "Foundex — Founder intelligence" },
      { property: "og:description", content: "Source, screen, and validate founders. Evidence-backed memos, trust scores, and cold outreach in one place." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Instrument+Serif&display=swap" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head><HeadContent /></head>
      <body style={{ fontFamily: "Inter, system-ui, sans-serif" }}>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function TopNav() {
  const linkCls = "mono text-xs uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors";
  const activeCls = "text-primary";
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-primary text-primary-foreground">
            <span className="mono text-sm font-bold">F</span>
          </div>
          <span className="mono text-sm font-semibold tracking-widest">
            FOUND<span className="text-primary">EX</span>
          </span>
        </Link>
        <nav className="flex items-center gap-8">
          <Link to="/" className={linkCls} activeProps={{ className: `${linkCls} ${activeCls}` }} activeOptions={{ exact: true }}>
            Discover
          </Link>
          <Link to="/apply" className={linkCls} activeProps={{ className: `${linkCls} ${activeCls}` }}>
            Founder apply
          </Link>
        </nav>
        <div className="flex items-center gap-2 mono text-[10px] uppercase tracking-widest text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
          Live intel
        </div>
      </div>
    </header>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen flex flex-col bg-background text-foreground">
        <TopNav />
        <main className="flex-1"><Outlet /></main>
        <footer className="border-t border-border/60 py-6">
          <div className="mx-auto max-w-7xl px-6 flex items-center justify-between mono text-[10px] uppercase tracking-widest text-muted-foreground">
            <span>Foundex · Intelligence layer for early-stage capital</span>
            <span>v0.2 · MVP</span>
          </div>
        </footer>
      </div>
      <Toaster />
    </QueryClientProvider>
  );
}
