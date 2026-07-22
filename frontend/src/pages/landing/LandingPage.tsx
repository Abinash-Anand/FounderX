import { FounderSearchForm } from '../../features/founder-search/FounderSearchForm'

export function LandingPage() {
  return (
    <main className="landing" id="main-content">
      <section className="landing__hero" aria-labelledby="landing-title">
        <div className="landing__copy">
          <p className="eyebrow">Evidence-backed founder discovery</p>
          <h1 id="landing-title">Find the founders worth a closer look.</h1>
          <p>
            Turn an investment thesis into focused founder research, traceable evidence,
            investment intelligence, and a clear recommendation.
          </p>
        </div>
        <FounderSearchForm />
        <div className="landing__principles" aria-label="Research principles">
          <span>Public-source research</span>
          <span>Evidence-linked insights</span>
          <span>Explicit uncertainty</span>
        </div>
      </section>
    </main>
  )
}
