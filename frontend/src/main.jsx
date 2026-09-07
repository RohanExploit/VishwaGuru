import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import './i18n' // Initialize i18n
import './offlineQueue' // Initialize offline queue listeners
import { initNativeShell } from './native' // No-op on the web

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

// The native splash screen stays up until something hides it, so a failure here
// would leave the app on the splash forever.
initNativeShell()
