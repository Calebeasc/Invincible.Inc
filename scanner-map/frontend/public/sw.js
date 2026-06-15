// Invincible.Inc Scanner — Service Worker v5
// Caches the app shell so it loads instantly and works offline.
// API calls (fetch to /users, /encounters, etc.) always go to the network.

const CACHE = 'iinc-shell-v9'
// Only files that actually exist at the dist root. Vite hashes App.css/JS into
// /assets/*, which the fetch handler caches on first online load; the shell here
// is just what's needed to OPEN offline.
const SHELL = [
  '/',
  '/index.html',
  '/icon.svg',
  '/manifest.json',
]

// Install: pre-cache the shell. Use allSettled, not addAll — addAll rejects the
// whole install if ANY single file 404s (this is exactly what broke offline:
// the old SHELL listed App.css/favicon.ico which aren't in dist, so the worker
// never finished installing and never controlled the page).
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => Promise.allSettled(SHELL.map(u => c.add(u))))
      .then(() => self.skipWaiting())
  )
})

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  )
})

self.addEventListener('message', e => {
  if (e.data?.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
})

self.addEventListener('fetch', e => {
  // Ignore unsupported browser-internal requests that otherwise throw in SW fetch().
  if (e.request.cache === 'only-if-cached' && e.request.mode !== 'same-origin') {
    return
  }

  let url
  try {
    url = new URL(e.request.url)
  } catch {
    return
  }

  if (!['http:', 'https:'].includes(url.protocol)) {
    return
  }

  // Let API calls go straight to network (never cache dynamic data)
  const isApi = url.pathname.startsWith('/users') ||
                url.pathname.startsWith('/encounters') ||
                url.pathname.startsWith('/gps') ||
                url.pathname.startsWith('/control') ||
                url.pathname.startsWith('/heatmap') ||
                url.pathname.startsWith('/route') ||
                url.pathname.startsWith('/stoppers') ||
                url.pathname.startsWith('/flock') ||
                url.pathname.startsWith('/scan') ||
                url.pathname.startsWith('/settings') ||
                url.pathname.startsWith('/accounts') ||
                url.pathname.startsWith('/hotspots') ||
                url.pathname.startsWith('/achievements') ||
                url.pathname.startsWith('/replay') ||
                url.pathname.startsWith('/targets') ||
                url.pathname.startsWith('/devices') ||
                url.pathname.startsWith('/mesh') ||
                url.pathname.startsWith('/export') ||
                url.pathname.startsWith('/stats') ||
                url.pathname.startsWith('/health') ||
                url.pathname.startsWith('/auth') ||
                url.pathname.startsWith('/api')

  if (isApi || e.request.method !== 'GET') {
    e.respondWith(
      fetch(e.request).catch(err => {
        console.error('[SW] API fetch failed:', err)
        return jsonServiceUnavailable()
      }),
    )
    return
  }

  const isNavigate = e.request.mode === 'navigate'
  if (isNavigate) {
    e.respondWith(
      (async () => {
        try {
          const res = await fetch(e.request)
          if (res.ok) {
            const clone = res.clone()
            caches.open(CACHE).then(c => c.put(e.request, clone))
          }
          return res
        } catch (err) {
          console.error('[SW] Navigation fetch failed:', err)
          const cached = await caches.match(e.request)
          return cached || jsonServiceUnavailable()
        }
      })(),
    )
    return
  }

  // Static assets: cache-first
  e.respondWith(
    caches.match(e.request).then(cached => {
      const network = (async () => {
        try {
          const res = await fetch(e.request)
          if (res.ok) {
            const clone = res.clone()
            caches.open(CACHE).then(c => c.put(e.request, clone))
          }
          return res
        } catch (err) {
          console.error('[SW] Fetch failed:', err)
          return jsonServiceUnavailable()
        }
      })()
      return cached || network
    })
  )
})

// Tapping the "GPS Tracking Active" notification brings the app to the foreground
self.addEventListener('notificationclick', e => {
  e.notification.close()
  e.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clients => {
      for (const client of clients) {
        if ('focus' in client) return client.focus()
      }
      return self.clients.openWindow('/')
    })
  )
})
