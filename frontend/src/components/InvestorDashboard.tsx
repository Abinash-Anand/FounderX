import { FounderScore } from './FounderScore'
import { IdeaMarketScore } from './IdeaMarketScore'
import { MarketScore } from './MarketScore'
import { MomentumTrend } from './MomentumTrend'
import { PitchDeckUpload } from './PitchDeckUpload'

export function InvestorDashboard() {
  return (
    <main>
      <header className="site-header">
        <a className="wordmark" href="/" aria-label="VC Brain home">
          VC<span>/</span>BRAIN
        </a>
        <div className="system-status"><i /> Intelligence online</div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">Investor dashboard · Sunday, 19 July</p>
          <h1>Decide at the speed<br />of conviction.</h1>
        </div>
        <div className="decision-clock">
          <span>Decision window</span>
          <strong>18:42:09</strong>
          <small>remaining</small>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="score-stack">
          <FounderScore />
          <MarketScore />
          <IdeaMarketScore />
        </div>
        <MomentumTrend />
        <PitchDeckUpload />
      </section>
    </main>
  )
}

