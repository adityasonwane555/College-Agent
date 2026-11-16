/**
 * BUDDY AI 2.0 — Frontend React Application Entry Point
 *
 * Architecture & Bootstrap:
 *   - React DOM Root Mounting:
 *       - Mounts the top-level <App /> container into the browser DOM element (#root).
 *   - Development StrictMode:
 *       - Wraps application root in <StrictMode> to detect side effects and verify cleanup hooks.
 *   - Global Stylesheet Ingestion:
 *       - Loads base typography, CSS variables, and kiosk viewport layouts from index.css.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
