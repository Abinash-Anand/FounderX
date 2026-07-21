import { Component, type ErrorInfo, type PropsWithChildren, type ReactNode } from 'react'

type State = {
  error: Error | null
}

export class AppErrorBoundary extends Component<PropsWithChildren, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error('Unhandled FounderX application error', error, errorInfo)
    }
  }

  private reset = () => {
    this.setState({ error: null })
  }

  render(): ReactNode {
    if (!this.state.error) {
      return this.props.children
    }

    return (
      <main className="app-error" aria-labelledby="app-error-title">
        <div className="app-error__panel">
          <p className="eyebrow">Application error</p>
          <h1 id="app-error-title">FounderX could not load</h1>
          <p>Something unexpected happened. Reset the application to try again.</p>
          <button className="button button--primary" type="button" onClick={this.reset}>
            Try again
          </button>
        </div>
      </main>
    )
  }
}
