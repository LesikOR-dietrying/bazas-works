import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { App } from './app/App'
import { Providers } from './app/Providers'
import './styles.css'
import './forms.css'
import './workspace.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Providers>
      <BrowserRouter><App /></BrowserRouter>
    </Providers>
  </StrictMode>,
)
