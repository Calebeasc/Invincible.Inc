import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import DevPanel from './components/DevPanel'
import InstallPage from './components/InstallPage'
import CopyrightPage from './components/CopyrightPage'
import { SovereignProvider } from './context/SovereignContext'

const hash = window.location.hash
const isDev       = hash === '#dev'
const isInstall   = hash === '#install'
const isCopyright = hash === '#legal'

// Register Service Worker on mobile so Android grants background GPS execution.
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {})
}

// Every branch is wrapped in <SovereignProvider> — App and DevPanel both call
// useSovereign(), and without the provider that hook returned null and the app
// crashed on render (blank screen, which also blocked the service worker from
// ever caching the shell for offline). Do not unwrap.
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <SovereignProvider>
      {isDev       ? <DevPanel />      :
       isInstall   ? <InstallPage />   :
       isCopyright ? <CopyrightPage /> :
                     <App />}
    </SovereignProvider>
  </React.StrictMode>
)
