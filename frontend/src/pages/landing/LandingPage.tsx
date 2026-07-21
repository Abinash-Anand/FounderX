import { FounderSearchForm } from '../../features/founder-search/FounderSearchForm'

export function LandingPage() {
  return (
    <main className="landing" id="main-content">
      <section className="landing__hero" aria-labelledby="landing-title">
        <div className="landing__copy">
          <p className="eyebrow">Founder intelligence, grounded in evidence</p>
          <h1 id="landing-title">Know the founder behind the company.</h1>
          <p>
            Turn a single research question into a structured founder profile, traceable evidence,
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
