import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { App } from './app/App'
import './design-system/styles/global.css'

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('FounderX could not find the application root element.')
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
