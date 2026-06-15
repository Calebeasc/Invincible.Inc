import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

const SovereignContext = createContext(null)
const TOKEN_KEY = 'sfm_dev_jwt'

export const SovereignProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '')
  const [userEmail, setUserEmail] = useState(() => localStorage.getItem('sfm_user_email') || '')
  const [configured, setConfigured] = useState(false)
  const [ready, setReady] = useState(false)

  const authHeaders = useMemo(
    () => (token ? { Authorization: `Bearer ${token}` } : {}),
    [token],
  )

  useEffect(() => {
    let cancelled = false
    fetch('/auth/dev/status', { headers: authHeaders })
      .then((r) => r.json())
      .then((data) => {
        if (cancelled) return
        setConfigured(Boolean(data.configured))
        if (data.session?.email) {
          setUserEmail(data.session.email)
          localStorage.setItem('sfm_user_email', data.session.email)
        } else if (!token) {
          setUserEmail('')
          localStorage.removeItem('sfm_user_email')
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setReady(true)
      })
    return () => { cancelled = true }
  }, [authHeaders, token])

  const persistSession = (email, jwtToken) => {
    setToken(jwtToken)
    setUserEmail(email)
    setConfigured(true)
    localStorage.setItem(TOKEN_KEY, jwtToken)
    localStorage.setItem('sfm_user_email', email)
  }

  const elevate = async (email, password, mode = 'login') => {
    const path = mode === 'setup' ? '/auth/dev/setup' : '/auth/dev/login'
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    const data = await res.json()
    if (!data.ok || !data.token) {
      return { ok: false, error: data.error || 'Authentication failed' }
    }
    persistSession(data.email, data.token)
    return { ok: true, email: data.email }
  }

  const decommission = () => {
    setToken('')
    setUserEmail('')
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem('sfm_user_email')
  }

  return (
    <SovereignContext.Provider value={{
      isDev: Boolean(token),
      userEmail,
      configured,
      ready,
      elevate,
      decommission,
      authHeaders,
    }}>
      {children}
    </SovereignContext.Provider>
  )
}

// Safe default so a missing <SovereignProvider> degrades (read-only, signed-out)
// instead of throwing and taking the whole app down — defense in depth against
// the render-crash this file caused before the provider was mounted in main.jsx.
const SOVEREIGN_DEFAULT = {
  isDev: false, userEmail: '', configured: false, ready: true,
  elevate: async () => ({ ok: false, error: 'auth unavailable' }),
  decommission: () => {}, authHeaders: {},
}

export const useSovereign = () => useContext(SovereignContext) || SOVEREIGN_DEFAULT
