import React, { useState, useEffect, useCallback, useRef, useMemo, Component } from 'react'
import MapView from './components/MapView'
import Sidebar from './components/Sidebar'
import StatusBar from './components/StatusBar'
import useMesh from './hooks/useMesh'
import SettingsPanel from './components/SettingsPanel'
import TargetsPanel from './components/TargetsPanel'
import DataPanel from './components/DataPanel'
import UserModal, { OtpVerifyModal } from './components/UserModal'
import SystemAccessModal from './components/SystemAccessModal'
import UpdateToast from './components/UpdateToast'
import StatsPanel from './components/StatsPanel'
import ReplayPanel from './components/ReplayPanel'
import { useSovereign } from './context/SovereignContext'
import { playWatcherAlert, playStopperAlert, playGenericAlert,
         playTailAlert, playHotspotAlert, resumeAudio } from './utils/audio'
import { enableWakePrevention, tryAutoWakeLock } from './utils/wakelock'
import { GPSProcessor, startStationaryDetector } from './utils/gpsAccuracy'
import './App.css'

const API = ''

// ── Device fingerprint ────────────────────────────────────────────────────────
// Combines stable browser/hardware properties into a prefix so the same physical
// device produces the same prefix even if localStorage is cleared.
// Full ID format: "<8-char-fingerprint>-<8-char-random>"
function getDeviceId() {
  const stored = localStorage.getItem('sfm_device_id')
  if (stored) return stored

  const parts = [
    navigator.userAgent,
    navigator.language,
    `${screen.width}x${screen.height}x${screen.colorDepth}`,
    Intl.DateTimeFormat().resolvedOptions().timeZone,
    String(navigator.hardwareConcurrency || 0),
    String(navigator.maxTouchPoints || 0),
    navigator.platform || '',
  ]
  let h = 5381
  for (const s of parts.join('||')) {
    h = ((h << 5) + h + s.charCodeAt(0)) >>> 0
  }
  const fp   = h.toString(16).padStart(8, '0')
  const rand = Math.random().toString(36).slice(2, 10)
  const id   = `${fp}-${rand}`
  localStorage.setItem('sfm_device_id', id)
  return id
}

const DEVICE_ID = getDeviceId()

// ── Error boundary — catches render crashes and shows a tap-to-reload screen ─
class AppErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { crashed: false, err: '' } }
  static getDerivedStateFromError(err) { return { crashed: true, err: err?.message || '' } }
  render() {
    if (!this.state.crashed) return this.props.children
    return (
      <div onClick={() => window.location.reload()} style={{
        position: 'fixed', inset: 0, background: '#0b0f14',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        gap: 16, fontFamily: 'monospace', cursor: 'pointer', userSelect: 'none',
      }}>
        <div style={{ fontSize: 36 }}>⚠️</div>
        <div style={{ fontSize: 16, color: '#fff', fontWeight: 700 }}>Something went wrong</div>
        <div style={{ fontSize: 12, color: 'rgba(200,216,232,0.5)', textAlign: 'center', maxWidth: 300, lineHeight: 1.6 }}>
          {this.state.err || 'An unexpected error occurred.'}
        </div>
        <div style={{ fontSize: 13, color: '#0A84FF', marginTop: 8 }}>Tap to reload</div>
      </div>
    )
  }
}

// ── Gate screens ──────────────────────────────────────────────────────────────
function PendingScreen({ username }) {
  return (
    <div style={{ position:'fixed', inset:0, background:'#0b0f14', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:20, fontFamily:'monospace' }}>
      <div style={{ fontSize:40 }}>⏳</div>
      <div style={{ fontSize:18, color:'#fff', fontWeight:700 }}>Waiting for Approval</div>
      <div style={{ fontSize:13, color:'rgba(200,216,232,0.5)', textAlign:'center', maxWidth:300, lineHeight:1.7 }}>
        {username
          ? <>Your request as <span style={{ color:'#00d4ff' }}>{username}</span> has been sent.<br /></>
          : null}
        An operator will approve or deny your access.
      </div>
      <div style={{ width:8, height:8, borderRadius:'50%', background:'#00d4ff', boxShadow:'0 0 12px #00d4ff', animation:'sfmPulse 1.5s ease-in-out infinite' }} />
      <style>{`@keyframes sfmPulse{0%,100%{opacity:1}50%{opacity:0.2}}`}</style>
    </div>
  )
}

function BlockedScreen() {
  return (
    <div style={{ position:'fixed', inset:0, background:'#0b0f14', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:20, fontFamily:'monospace' }}>
      <div style={{ fontSize:40 }}>🚫</div>
      <div style={{ fontSize:18, color:'#FF453A', fontWeight:700 }}>Access Denied</div>
      <div style={{ fontSize:13, color:'rgba(200,216,232,0.5)', textAlign:'center', maxWidth:280, lineHeight:1.6 }}>
        Your device has been blocked by an operator.
      </div>
    </div>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────
async function doRegister(username, vehicle) {
  const r = await fetch('/users/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ device_id: DEVICE_ID, username, vehicle }),
  })
  return r.json()
}

// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  const { isDev } = useSovereign()
  const [mode, setMode] = useState('user')

  useEffect(() => {
    // Sync mode with sovereign context
    if (isDev) setMode('sovereign')
    else setMode('user')
  }, [isDev])

  const theme = {
    accent: mode === 'sovereign' ? '#FF453A' : '#00D4FF',
    bg: '#0A0E14',
    dim: 'rgba(180,195,220,0.5)'
  }

  const [running, setRunning]         = useState(false)
  const [timeRange, setTimeRange]     = useState(3600000)
  const [heatCells, setHeatCells]     = useState([])
  const [encounters, setEncounters]   = useState([])
  const [routePoints, setRoutePoints] = useState([])
  const [showMarkers, setShowMarkers]         = useState(true)
  const [showRoute, setShowRoute]             = useState(true)
  const [showFlockCameras, setShowFlockCameras] = useState(true)
  const [flockCameras, setFlockCameras]       = useState([])
  const [showAircraft, setShowAircraft]       = useState(true)
  const [aircraftData, setAircraftData]       = useState([]) // @tron: Live ADS-B flight data
  const [loading, setLoading]         = useState(false)
  const [lastPoll, setLastPoll]       = useState(null)  // eslint-disable-line no-unused-vars
  const [userPos, setUserPos]         = useState(null)
  const [alerts, setAlerts]           = useState([])   // critical toasts only
  const [scanLog, setScanLog]         = useState([])   // desktop scan console ticker
  const [panel, setPanel]             = useState(null)
  const [appSettings, setAppSettings] = useState({ audio_enabled:true, audio_volume:0.7, alert_radius_m:300, alert_cooldown_s:30 })
  const [scanMode, setScanMode]       = useState('idle')
  // 'closed' | 'half' | 'full' — drives Waze-style bottom sheet snap points
  const [sidebarState, setSidebarState] = useState('closed')
  const sidebarOpen       = sidebarState !== 'closed'
  const sidebarFullscreen = sidebarState === 'full'

  // Multi-device account linkage
  const [accountId, setAccountId] = useState(() => localStorage.getItem('sfm_account_id') || '')
  const handleAccountLinked = useCallback((id) => {
    setAccountId(id)
    localStorage.setItem('sfm_account_id', id)
  }, [])

  // Trophy score — distance × speed multiplier, persisted in localStorage
  const [trophyScore, setTrophyScore] = useState(() =>
    parseInt(localStorage.getItem('sfm_trophy_score') || '0', 10)
  )
  const [sessionStats, setSessionStats] = useState({ topSpeed: 0, totalDist: 0, speedSum: 0, speedCount: 0 })
  const prevTrophyPosRef  = useRef(null)
  const prevTopSpeedRef   = useRef(0)
  const gpsProcessorRef   = useRef(new GPSProcessor())
  const [activeUsers, setActiveUsers] = useState([])

  const [username, setUsername]       = useState(() => localStorage.getItem('sfm_username') || '')
  const [vehicle,  setVehicle]        = useState(() => localStorage.getItem('sfm_vehicle')  || 'motorcycle')
  // 'checking' | 'pending' | 'blocked' | 'approved'
  // For returning users, optimistically show 'approved' immediately so there's
  // no black screen while the async auth check is in flight (~1 second).
  // The poll will flip to 'blocked' or 'pending' within seconds if needed.
  const [authStatus, setAuthStatus]   = useState(() =>
    localStorage.getItem('sfm_username') ? 'approved' : 'checking'
  )
  const [canContribute, setCanContribute] = useState(true)
  const [needsOtpVerify, setNeedsOtpVerify] = useState(false)

  // ── Feature 1: Replay mode ────────────────────────────────────────────────
  const [replayMode,     setReplayMode]     = useState(false)
  const [replayState,    setReplayState]    = useState(null)   // {cursor, data, playing}

  // ── Feature 2: Tail detection ─────────────────────────────────────────────
  const [tailKeys, setTailKeys] = useState(new Set())   // target_keys flagged as tails

  // ── Feature 4: Stopper hotspots ───────────────────────────────────────────
  const [hotspots,         setHotspots]         = useState([])

  // ── Omni-Mesh: live field-sensor picture (offline-safe; see hooks/useMesh) ──
  const { meshNodes, meshDetections, meshStatus, meshStats } = useMesh()
  const [showMesh, setShowMesh] = useState(() => localStorage.getItem('sfm_show_mesh') !== '0')
  useEffect(() => { localStorage.setItem('sfm_show_mesh', showMesh ? '1' : '0') }, [showMesh])

  // ── Live stopper tracking ──────────────────────────────────────────────────
  const [stopperTrails, setStopperTrails] = useState([])
  const hotspotAlertedRef  = useRef(new Set())         // hotspot ids already alerted this session
  const hotspotCooldownRef = useRef({})                // id -> last alert timestamp

  // ── Refs (must be before any conditional return) ──────────────────────────
  const alertIdRef        = useRef(0)
  const userPosRef        = useRef(null)
  const canContributeRef  = useRef(true)
  const usernameRef       = useRef(username)
  const vehicleRef        = useRef(vehicle)
  const bgBufferRef       = useRef([])      // GPS fixes buffered while backgrounded
  const isBackgroundedRef = useRef(false)
  const swRegRef          = useRef(null)    // Service Worker registration
  const isMobile          = useRef(/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)).current

  // ── Sync refs ─────────────────────────────────────────────────────────────
  useEffect(() => { userPosRef.current = userPos },            [userPos])

  // ── Trophy score accumulation — distance × speed multiplier ───────────────
  useEffect(() => {
    if (!userPos) return
    const prev = prevTrophyPosRef.current
    prevTrophyPosRef.current = userPos
    if (!prev) return
    const R = 6371000
    const dLat = (userPos.lat - prev.lat) * Math.PI / 180
    const dLon = (userPos.lon - prev.lon) * Math.PI / 180
    const a = Math.sin(dLat/2)**2 + Math.cos(prev.lat*Math.PI/180)*Math.cos(userPos.lat*Math.PI/180)*Math.sin(dLon/2)**2
    const dist = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
    if (dist < 2 || dist > 500) return  // ignore tiny jitter or GPS jumps
    const mph = (userPos.speed ?? 0) * 2.23694
    const mult = mph < 10 ? 1 : mph < 40 ? 2 : 3
    const pts = Math.max(1, Math.round(dist / 20 * mult))  // ~1pt per 20m base
    setTrophyScore(s => {
      const next = s + pts
      localStorage.setItem('sfm_trophy_score', String(next))
      return next
    })
    setSessionStats(s => {
      const newTop = Math.max(s.topSpeed, mph)
      // Fire a toast when a new session top speed is beaten (only above 15 mph to avoid noise)
      if (newTop > s.topSpeed && newTop > 15 && newTop > prevTopSpeedRef.current) {
        prevTopSpeedRef.current = newTop
        const id = ++alertIdRef.current
        setAlerts(prev => [...prev.slice(-4), {
          id, type: 'top_speed', color: 'green',
          message: `New top speed: ${newTop.toFixed(1)} mph`,
        }])
        setTimeout(() => setAlerts(prev => prev.filter(a => a.id !== id)), 5000)
      }
      return {
        topSpeed:   newTop,
        totalDist:  s.totalDist + dist,
        speedSum:   s.speedSum + mph,
        speedCount: s.speedCount + 1,
      }
    })
  }, [userPos])

  useEffect(() => { canContributeRef.current = canContribute }, [canContribute])
  useEffect(() => { usernameRef.current  = username },          [username])
  useEffect(() => { vehicleRef.current   = vehicle },           [vehicle])

  // ── Notification permission + SW registration (mobile only) ──────────────
  // The persistent notification is how Google Maps keeps running in the background.
  // Android sees Chrome has an active notification → treats it as a foreground process.
  useEffect(() => {
    if (!isMobile) return
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready
        .then(reg => { swRegRef.current = reg })
        .catch(() => {})
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Background / foreground detection (mobile only) ──────────────────────
  // When backgrounded: show a persistent notification (keeps Chrome alive) and
  //   switch GPS pushes to local buffer instead of uploading.
  // When foregrounded: close notification and flush the buffer to /gps/batch.
  useEffect(() => {
    if (!isMobile) return

    const showNotif = async () => {
      const reg = swRegRef.current
      if (!reg || Notification.permission !== 'granted') return
      try {
        await reg.showNotification('GPS Tracking Active', {
          body: 'Buffering data · Tap to return to app',
          tag: 'sfm-tracking',
          silent: true,
          requireInteraction: true,
        })
      } catch {}
    }

    const closeNotif = async () => {
      const reg = swRegRef.current
      if (!reg) return
      try {
        const notifs = await reg.getNotifications({ tag: 'sfm-tracking' })
        notifs.forEach(n => n.close())
      } catch {}
    }

    const flushBuffer = () => {
      const fixes = bgBufferRef.current.splice(0)
      if (fixes.length === 0) return
      fetch('/gps/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fixes),
      }).catch(() => {})
    }

    const onVisChange = () => {
      if (document.hidden) {
        isBackgroundedRef.current = true
        showNotif()
      } else {
        isBackgroundedRef.current = false
        closeNotif()
        flushBuffer()
      }
    }

    document.addEventListener('visibilitychange', onVisChange)
    return () => document.removeEventListener('visibilitychange', onVisChange)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Initial registration check (returning users) ──────────────────────────
  useEffect(() => {
    if (!username) {
      setAuthStatus('approved') // No username yet — UserModal will prompt and then register
      return
    }
    doRegister(username, vehicle)
      .then(d => {
        if (typeof d.can_contribute === 'number') setCanContribute(d.can_contribute !== 0)
        setAuthStatus(d.status || 'pending')
      })
      .catch(() => setAuthStatus('pending'))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Poll: pending → 3 s, approved → 60 s (picks up can_contribute changes) ─
  useEffect(() => {
    if (authStatus !== 'pending' && authStatus !== 'approved') return
    if (!username) return
    const ms = authStatus === 'pending' ? 3000 : 60000
    const id = setInterval(async () => {
      try {
        const d = await doRegister(username, vehicle)
        if (d.needs_reregister) {
          // Dev has requested identity verification via OTP
          setNeedsOtpVerify(true)
          return
        }
        if (typeof d.can_contribute === 'number') setCanContribute(d.can_contribute !== 0)
        if (d.status && d.status !== authStatus) setAuthStatus(d.status)
      } catch {}
    }, ms)
    return () => clearInterval(id)
  }, [authStatus, username, vehicle])

  // ── Load settings ─────────────────────────────────────────────────────────
  useEffect(() => {
    fetch(`${API}/settings`).then(r=>r.json()).then(s=>{setAppSettings(s);setScanMode(s.scan_mode||'idle')}).catch(()=>{})
  }, [])

  // ── GPS + presence (background-safe) ─────────────────────────────────────
  // watchPosition is OS-level and keeps firing even with screen off on Android.
  // We drive BOTH the GPS push and presence broadcast from inside this callback
  // so they survive Chrome's setInterval throttling (which goes to 1+ min in bg).
  // keepalive:true ensures the fetch completes even if the page is backgrounded.
  // A setInterval fallback fires when stationary (no new GPS fixes) — it is
  // throttled in background but that's OK; watchPosition handles the bg case.
  useEffect(() => {
    if (!navigator.geolocation) return

    let lastGpsPush      = 0
    let lastPresencePush = 0
    const GPS_MS      = 2000   // min gap between GPS backend pushes
    const PRESENCE_MS = 5000   // min gap between presence broadcasts

    const pushPresence = (lat, lon, heading, speed) => {
      const uname = usernameRef.current
      if (!uname) return
      fetch('/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: uname, vehicle: vehicleRef.current, device_id: DEVICE_ID,
          lat: lat ?? null, lon: lon ?? null,
          heading: heading ?? null, speed: speed ?? null,
        }),
        keepalive: true,
      }).catch(() => {})
    }

    // iOS 13+: request DeviceOrientation permission for accurate compass heading
    if (typeof DeviceOrientationEvent !== 'undefined' &&
        typeof DeviceOrientationEvent.requestPermission === 'function') {
      DeviceOrientationEvent.requestPermission().catch(() => {})
    }
    // Listen for iOS compass heading (webkitCompassHeading is much more accurate
    // than the heading value from geolocation on iOS Safari)
    let compassHeading = null
    const onOrientation = (e) => {
      if (e.webkitCompassHeading != null) {
        compassHeading = e.webkitCompassHeading
      }
    }
    window.addEventListener('deviceorientation', onOrientation, true)

    // Start stationary detector (DeviceMotion-based) — reduces GPS drift when parked
    const stopStationary = startStationaryDetector((isStill) => {
      gpsProcessorRef.current.setStationary(isStill)
    })

    // Primary: OS-driven, works with screen off on Android
    const watchId = navigator.geolocation.watchPosition(
      p => {
        const { latitude: lat, longitude: lon, accuracy, speed } = p.coords
        // Use iOS compass heading when available (far more accurate than geolocation heading)
        const rawHeading = compassHeading ?? p.coords.heading

        // Run all accuracy algorithms (Kalman + outlier rejection + dead reckoning + smoothing)
        const smoothed = gpsProcessorRef.current.process({
          lat, lon, accuracy: accuracy ?? 50,
          speed, heading: rawHeading,
          timestamp: p.timestamp || Date.now(),
        })
        if (!smoothed) return   // fix rejected — keep last known position

        setUserPos({ lat: smoothed.lat, lon: smoothed.lon, heading: smoothed.heading, speed: smoothed.speed })
        const now = Date.now()

        if (now - lastGpsPush >= GPS_MS && canContributeRef.current) {
          lastGpsPush = now
          if (isBackgroundedRef.current) {
            // Buffer for batch upload when app returns to foreground
            bgBufferRef.current.push({ lat, lon, accuracy_m: accuracy, heading, speed_mps: speed, ts_ms: now })
          } else {
            fetch('/gps/update', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ lat, lon, accuracy_m: accuracy, heading, speed_mps: speed }),
              keepalive: true,
            }).catch(() => {})
          }
        }

        if (now - lastPresencePush >= PRESENCE_MS) {
          lastPresencePush = now
          pushPresence(lat, lon, heading, speed)
        }
      },
      err => console.warn('GPS:', err.message),
      // maximumAge:0  → never return a cached position; always request a fresh fix
      // timeout:5000  → shorter timeout so stale positions don't linger
      { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
    )

    // Fallback: timer-driven presence for when device is stationary (no new fixes).
    // Throttled by Chrome in background (~1 min), but watchPosition covers that case.
    const intervalId = setInterval(() => {
      const now = Date.now()
      if (now - lastPresencePush >= PRESENCE_MS) {
        const pos = userPosRef.current
        lastPresencePush = now
        pushPresence(pos?.lat, pos?.lon, pos?.heading, pos?.speed)
      }
    }, 5000)

    return () => {
      navigator.geolocation.clearWatch(watchId)
      window.removeEventListener('deviceorientation', onOrientation, true)
      stopStationary()
      clearInterval(intervalId)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Poll active users ─────────────────────────────────────────────────────
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const r = await fetch(`${API}/users?device_id=${encodeURIComponent(DEVICE_ID)}`)
        if (r.ok) setActiveUsers(((await r.json()).users || []).filter(u => !u.hidden))
      } catch {}
    }, 3000)
    return () => clearInterval(id)
  }, [])

  // ── Phone GPS relay ───────────────────────────────────────────────────────
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const r = await fetch(`${API}/gps/status`)
        if (!r.ok) return
        const fix = await r.json()
        if (fix.lat !== null && fix.source === 'phone') setUserPos({ lat:fix.lat, lon:fix.lon })
      } catch {}
    }, 1500)
    return () => clearInterval(id)
  }, [])

  // ── Wake lock: prevent screen from dimming before first tap ─────────────────
  useEffect(() => { tryAutoWakeLock() }, [])

  // ── Notification permission ───────────────────────────────────────────────
  useEffect(() => {
    if (Notification.permission === 'default') Notification.requestPermission()
  }, [])

  // ── Alert handler ─────────────────────────────────────────────────────────
  const handleAlert = useCallback((alert) => {
    resumeAudio()
    const id = ++alertIdRef.current
    const vol = appSettings.audio_volume ?? 0.7

    // Feature 2: tail detection
    if (alert.type === 'tail_detection') {
      if (alert.target_key) {
        setTailKeys(prev => new Set([...prev, alert.target_key]))
      }
      setAlerts(prev => {
        const safePrev = Array.isArray(prev) ? prev : [];
        return [...safePrev.slice(-4), {
          ...alert, id,
          type: alert.label || 'Device',
          priority: 'high',
          icon: '🔁',
        }];
      })
      playTailAlert(vol)
      if (Notification.permission === 'granted') {
        new Notification('⚠ Tail detected', { body: alert.message || 'Device keeps appearing', silent: true })
      }
      setTimeout(() => setAlerts(prev => prev.filter(a => a.id !== id)), 12000)
      return
    }

    // Feature 3: daily Stopper surge
    if (alert.type === 'stopper_surge') {
      setAlerts(prev => [...prev.slice(-4), {
        ...alert, id,
        type: 'Surge Alert',
        priority: 'high',
        icon: '📈',
        color: 'red',
      }])
      playStopperAlert(vol)
      if (Notification.permission === 'granted') {
        new Notification('📈 Stopper Surge', { body: alert.message, silent: true })
      }
      setTimeout(() => setAlerts(prev => prev.filter(a => a.id !== id)), 15000)
      return
    }

    // Feature 4: hotspot proximity
    if (alert.type === 'hotspot_proximity') {
      setAlerts(prev => [...prev.slice(-4), {
        ...alert, id,
        type: 'Hotspot',
        priority: 'high',
        icon: '🔥',
        color: 'red',
      }])
      playHotspotAlert(vol)
      if (Notification.permission === 'granted') {
        new Notification('🔥 Stopper Hotspot nearby', { body: alert.message, silent: true })
      }
      setTimeout(() => setAlerts(prev => prev.filter(a => a.id !== id)), 10000)
      return
    }

    // @tron: Police Aircraft Alert
    if (alert.type === 'Police-Aircraft') {
      setAlerts(prev => [...prev.slice(-4), {
        ...alert, id,
        priority: 'high',
        icon: '🚁',
        color: 'red',
      }])
      playStopperAlert(vol, 'siren') // Use siren for airborne threats
      if (Notification.permission === 'granted') {
        new Notification('⚠️ POLICE AIR DETECTED', { body: alert.message, silent: false })
      }
      setTimeout(() => setAlerts(prev => prev.filter(a => a.id !== id)), 15000)
      return
    }

    // Standard proximity alerts
    const watcherStyle = localStorage.getItem('sfm_watcher_sound') || 'chirp'
    const stopperStyle = localStorage.getItem('sfm_stopper_sound') || 'siren'

    if (alert.type === 'Fun-Stopper') {
      // Stopper: always a full toast + sound + OS notification
      setAlerts(prev => [...prev.slice(-4), {...alert, id}])
      playStopperAlert(vol, stopperStyle)
      if (Notification.permission === 'granted') {
        new Notification('🚔 Fun-Stopper nearby', { body: `${alert.distance}m away · ${alert.rssi?.toFixed(0)} dBm`, silent: false })
      }
      setTimeout(() => setAlerts(prev => prev.filter(a => a.id !== id)), 10000)
    } else if (alert.type === 'Fun-Watcher') {
      // Watcher (first-seen only — MapView already deduped): small toast + sound
      setAlerts(prev => [...prev.slice(-3), {...alert, id}])
      playWatcherAlert(vol, watcherStyle)
      setTimeout(() => setAlerts(prev => prev.filter(a => a.id !== id)), 6000)
    } else {
      // Special device (ring/axon/flock/drone/smartglasses) first-seen:
      // desktop → add to scan console ticker only (no toast, no sound)
      // mobile → brief small toast
      const SPECIAL_EMOJI = { ring:'🔔', axon:'📹', flock:'📷', drone:'🚁', smartglasses:'🕶' }
      const em = SPECIAL_EMOJI[alert.device_type] || '⚡'
      const entry = { ...alert, id, em, ts: Date.now() }
      setScanLog(prev => [...prev.slice(-9), entry])
      if (isMobile) {
        setAlerts(prev => [...prev.slice(-2), {...alert, id, icon: em}])
        setTimeout(() => setAlerts(prev => prev.filter(a => a.id !== id)), 4000)
      }
    }
  }, [appSettings])

  // ── Poll queued alerts ────────────────────────────────────────────────────
  useEffect(() => {
    if (!username) return
    const id = setInterval(async () => {
      try {
        const r = await fetch(`${API}/users/alerts?username=${encodeURIComponent(username)}`)
        if (!r.ok) return
        const { alerts: pending } = await r.json()
        pending?.forEach(a => handleAlert(a))
      } catch {}
    }, 2000)
    return () => clearInterval(id)
  }, [username, handleAlert])

  // ── Feature 4: Poll hotspots (every 60 s) ────────────────────────────────
  useEffect(() => {
    const load = () =>
      fetch('/hotspots')
        .then(r => r.json())
        .then(d => setHotspots(d.hotspots || []))
        .catch(() => {})
    load()
    const id = setInterval(load, 60000)
    return () => clearInterval(id)
  }, [])

  // ── Live stopper tracking (every 10 s) ────────────────────────────────────
  useEffect(() => {
    const load = () =>
      fetch('/stoppers/active?window_min=30')
        .then(r => r.json())
        .then(d => setStopperTrails(d.stoppers || []))
        .catch(() => {})
    load()
    const id = setInterval(load, 10000)
    return () => clearInterval(id)
  }, [])

  // ── Flock / ALPR camera locations (fetch once, refresh every 30 min) ─────
  useEffect(() => {
    const load = () =>
      fetch('/flock/cameras')
        .then(r => r.json())
        .then(d => setFlockCameras(d.cameras || []))
        .catch(() => {})
    load()
    const id = setInterval(load, 30 * 60 * 1000)
    return () => clearInterval(id)
  }, [])

  // ── @tron: ADS-B Aircraft Tracking (refresh every 5 s) ───────────────────
  useEffect(() => {
    const load = () =>
      fetch('/adsb/status')
        .then(r => r.json())
        .then(d => setAircraftData(d.aircraft || []))
        .catch(() => {})
    load()
    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [])

  // ── Feature 4: Hotspot proximity check on every GPS fix ───────────────────
  useEffect(() => {
    if (!userPos || hotspots.length === 0 || replayMode) return
    const now = Date.now()
    const COOLDOWN_MS = 120_000   // 2 min per hotspot

    hotspots.forEach(hs => {
      if (!hs.lat || !hs.lon) return
      const last = hotspotCooldownRef.current[hs.id] || 0
      if (now - last < COOLDOWN_MS) return

      // Haversine distance
      const R = 6_371_000
      const dLat = (hs.lat - userPos.lat) * Math.PI / 180
      const dLon = (hs.lon - userPos.lon) * Math.PI / 180
      const a = Math.sin(dLat/2)**2 + Math.cos(userPos.lat*Math.PI/180)*Math.cos(hs.lat*Math.PI/180)*Math.sin(dLon/2)**2
      const dist = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))

      const inProximity = dist <= 500

      // Heading cone check (±30° ahead, within 1 km)
      let inCone = false
      if (userPos.heading != null && userPos.speed != null && userPos.speed >= 1) {
        const dLon2 = (hs.lon - userPos.lon) * Math.PI / 180
        const y = Math.sin(dLon2) * Math.cos(hs.lat * Math.PI / 180)
        const x = Math.cos(userPos.lat*Math.PI/180)*Math.sin(hs.lat*Math.PI/180)
                - Math.sin(userPos.lat*Math.PI/180)*Math.cos(hs.lat*Math.PI/180)*Math.cos(dLon2)
        const bear = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360
        const angleDiff = Math.min(Math.abs(userPos.heading - bear), 360 - Math.abs(userPos.heading - bear))
        if (angleDiff <= 30 && dist <= 1000) inCone = true
      }

      if (inProximity || inCone) {
        hotspotCooldownRef.current[hs.id] = now
        const reason = inCone ? `~${Math.round(dist)}m ahead` : `${Math.round(dist)}m away`
        handleAlert({
          type:    'hotspot_proximity',
          message: `Stopper Hotspot ${reason} — seen ${hs.day_count}+ days`,
          color:   'red',
          distance: Math.round(dist),
          in_cone:  inCone,
        })
      }
    })
  }, [userPos, hotspots, replayMode, handleAlert])

  // ── Feature 1: Replay update callback ────────────────────────────────────
  const handleReplayUpdate = useCallback(({ cursor, data, playing }) => {
    setReplayState({ cursor, data, playing })
  }, [])

  // ── Poll map data ─────────────────────────────────────────────────────────
  const refresh = useCallback(async () => {
    const sp = timeRange === 0 ? '' : `since=${Date.now() - timeRange}`
    try {
      const [hRes, eRes, rRes] = await Promise.all([
        fetch(`${API}/heatmap?${sp}`),
        fetch(`${API}/encounters?${sp}&limit=30`),
        fetch(`${API}/route?${sp}&limit=5000`),
      ])
      if (hRes.ok) setHeatCells((await hRes.json()).cells || [])
      if (eRes.ok) setEncounters((await eRes.json()).encounters || [])
      if (rRes.ok) setRoutePoints((await rRes.json()).points || [])
      setLastPoll(new Date())
    } catch {}
  }, [timeRange])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 3000)
    return () => clearInterval(id)
  }, [refresh])

  // ── Scanner status + auto-start on mobile ────────────────────────────────
  useEffect(() => {
    fetch(`${API}/control/status`).then(r=>r.json()).then(d => {
      setRunning(d.running)
      setScanMode(d.mode || 'idle')
      if (!d.running) {
        fetch(`${API}/control/start`, { method:'POST' })
          .then(r => r.json())
          .then(d => { setRunning(true); setScanMode(d.mode || 'idle') })
          .catch(() => {})
      }
    }).catch(() => {})
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Callbacks ─────────────────────────────────────────────────────────────
  const closeSidebar = useCallback(() => setSidebarState('closed'), [])

  // ── Handlers ──────────────────────────────────────────────────────────────
  const toggleScanning = async () => {
    resumeAudio()
    setLoading(true)
    try {
      const res = await fetch(`${API}${running ? '/control/stop' : '/control/start'}`, { method:'POST' })
      const d = await res.json()
      setRunning(!running)
      setScanMode(d.mode || scanMode)
    } finally { setLoading(false) }
  }

  const handleInteraction = () => {
    resumeAudio()
    enableWakePrevention()
  }

  // Called when user submits the join form for the first time
  const handleUserDone = async (name, veh) => {
    localStorage.setItem('sfm_username', name)
    localStorage.setItem('sfm_vehicle', veh)
    setUsername(name)
    setVehicle(veh)
    setAuthStatus('checking')
    try {
      const d = await doRegister(name, veh)
      if (typeof d.can_contribute === 'number') setCanContribute(d.can_contribute !== 0)
      setAuthStatus(d.status || 'pending')
    } catch {
      setAuthStatus('pending')
    }
  }

  // ── Feature 1: Derive replay map data from cursor ─────────────────────────
  const replayEncounters = useMemo(() => {
    if (!replayMode || !replayState?.data) return null
    return replayState.data.encounters.filter(e => e.peak_ts_ms <= replayState.cursor)
  }, [replayMode, replayState])

  const replayRoute = useMemo(() => {
    if (!replayMode || !replayState?.data) return null
    return replayState.data.route.filter(p => p.ts <= replayState.cursor)
  }, [replayMode, replayState])

  const replayHeatCells = useMemo(() => {
    if (!replayMode || !replayEncounters || replayEncounters.length === 0) return []
    const maxRssi = Math.max(...replayEncounters.map(e => e.rssi_max))
    const floor   = -95
    return replayEncounters
      .filter(e => e.lat && e.lon)
      .map(e => ({
        lat:       e.lat,
        lon:       e.lon,
        intensity: Math.max(0.1, Math.min(1.0, (e.rssi_max - floor) / Math.max(1, maxRssi - floor))),
      }))
  }, [replayMode, replayEncounters])

  // ── Gate renders (ALL hooks are above this point) ─────────────────────────
  if (!username)                return <UserModal onDone={handleUserDone} />
  if (authStatus === 'blocked')  return <BlockedScreen />
  if (authStatus === 'pending')  return <PendingScreen username={username} />
  if (needsOtpVerify) return (
    <OtpVerifyModal
      deviceId={DEVICE_ID}
      onVerified={(acctId) => {
        if (acctId) handleAccountLinked(acctId)
        setNeedsOtpVerify(false)
      }}
    />
  )

  // ── Main app ───────────────────────────────────────────────────────────────
  return (
  <AppErrorBoundary>
    <UpdateToast />
    <div className="app-shell" onClick={handleInteraction}>

      {/* Mobile menu button */}
      <button
        className={`mobile-menu-btn${sidebarOpen ? ' open' : ''}`}
        onClick={() => setSidebarState(s => s === 'closed' ? 'half' : 'closed')}
        title="Menu"
      >☰</button>

      {/* Alert toasts */}
      <div className="alert-stack">
        {alerts.map(a => {
          const icon = a.icon
            ? a.icon
            : a.type === 'Fun-Watcher' ? '📷'
            : a.type === 'Fun-Stopper' ? '🚔'
            : '⚠'
          const title = a.type === 'tail_detection'
            ? `${a.label || 'Device'} TAILING`
            : a.type === 'stopper_surge'
            ? 'STOPPER SURGE'
            : a.type === 'hotspot_proximity'
            ? '🔥 HOTSPOT NEARBY'
            : `${a.type} DETECTED`
          const sub = a.message
            ? a.message
            : a.distance != null
              ? `${a.distance}m away · ${a.rssi?.toFixed(0)} dBm`
              : ''
          return (
            <div key={a.id} className={`alert-toast alert-${a.color}${a.priority === 'high' ? ' alert-high-priority' : ''}`}>
              <span className="alert-icon">{icon}</span>
              <div className="alert-body">
                <div className="alert-title">{title}</div>
                {sub && <div className="alert-sub">{sub}</div>}
              </div>
              <button className="alert-close" onClick={() => setAlerts(p => p.filter(x => x.id !== a.id))}>✕</button>
            </div>
          )
        })}
      </div>

      {/* Panels */}
  const [panelMode, setPanelMode]     = useState(null)

  // ... rest of state ...

  {panel==='settings' && <SettingsPanel onClose={()=>setPanel(null)} onOpenUserModal={(m) => { setPanel('user_modal'); setPanelMode(m); }} onOpenSystemAccess={() => setPanel('system_access')} onSaved={s=>{setAppSettings(s);setScanMode(s.scan_mode||'idle')}}/>}
  {panel==='user_modal' && <UserModal initialMode={panelMode} onDone={handleUserDone} onClose={() => { setPanel(null); setPanelMode(null); }} />}
  {panel==='system_access' && <SystemAccessModal onClose={() => setPanel(null)} />}
      {panel==='targets'      && <TargetsPanel     onClose={()=>setPanel(null)}/>}
      {panel==='data'         && <DataPanel        onClose={()=>setPanel(null)}/>}
      {panel==='leaderboard'  && <StatsPanel onClose={()=>setPanel(null)} myUsername={username} deviceId={DEVICE_ID}/>}

      <Sidebar
        running={running} loading={loading}
        timeRange={timeRange} setTimeRange={setTimeRange}
        showMarkers={showMarkers} setShowMarkers={setShowMarkers}
        showRoute={showRoute} setShowRoute={setShowRoute}
        showFlockCameras={showFlockCameras} setShowFlockCameras={setShowFlockCameras}
        flockCameraCount={flockCameras.length}
        showAircraft={showAircraft} setShowAircraft={setShowAircraft}
        aircraftCount={aircraftData.length}
        onToggle={toggleScanning}
        heatCells={heatCells} encounters={encounters} routePoints={routePoints}
        userPos={userPos} api={API} scanMode={scanMode}
        onOpenSettings={()=>setPanel('settings')}
        onOpenTargets={()=>setPanel('targets')}
        onOpenData={()=>setPanel('data')}
        onOpenLeaderboard={()=>{ setPanel('leaderboard'); setSidebarState('closed') }}
        onOpenReplay={()=>{ setReplayMode(true); setSidebarState('closed') }}
        username={username} vehicle={vehicle}
        activeUsers={activeUsers}
        sidebarState={sidebarState} onSidebarState={setSidebarState}
        onClose={closeSidebar}
        deviceId={DEVICE_ID}
        accountId={accountId}
        onAccountLinked={handleAccountLinked}
        trophyScore={trophyScore}
        sessionStats={sessionStats}
        hotspotCount={hotspots.length}
        tailKeys={tailKeys}
      />

      {sidebarOpen && <div className="sidebar-overlay" onClick={closeSidebar} />}

      <div className="map-area" style={{position:'relative'}}>
        <MapView
          heatCells={heatCells} encounters={encounters}
          showMarkers={showMarkers} userPos={replayMode ? null : userPos}
          routePoints={routePoints} showRoute={showRoute}
          onAlert={handleAlert}
          alertRadiusM={appSettings.alert_radius_m}
          alertCooldownMs={(appSettings.alert_cooldown_s||30)*1000}
          activeUsers={activeUsers} myUsername={username} myVehicle={vehicle}
          hotspots={hotspots}
          tailKeys={tailKeys}
          stopperTrails={stopperTrails}
          flockCameras={flockCameras}
          showFlockCameras={showFlockCameras}
          meshNodes={meshNodes}
          meshDetections={meshDetections}
          showMesh={showMesh}
          aircraftData={showAircraft ? aircraftData : []}
          replayMode={replayMode}
          replayEncounters={replayEncounters}
          replayRoute={replayRoute}
          replayHeatCells={replayHeatCells}
          sidebarState={sidebarState}
        />

        {/* Omni-Mesh status pill — tap to toggle the mesh layer. Always shows the
            connection state so a server outage is visible, not silent. */}
        <button
          type="button"
          onClick={() => setShowMesh((v) => !v)}
          title="Omni-Mesh field sensors — tap to toggle layer"
          style={{
            position: 'absolute', top: 12, right: 12, zIndex: 901,
            display: 'flex', alignItems: 'center', gap: 7,
            border: `1px solid ${meshStatus === 'live' ? 'rgba(0,230,118,0.5)' : 'rgba(255,77,109,0.5)'}`,
            background: 'rgba(8,12,20,0.88)',
            color: showMesh ? '#E8EDF5' : '#5a7a96',
            borderRadius: 999, padding: '7px 12px', fontSize: 11,
            fontFamily: 'monospace', fontWeight: 700, cursor: 'pointer',
          }}
        >
          <span style={{
            width: 9, height: 9, borderRadius: '50%',
            background: meshStatus === 'live' ? '#00e676' : '#ff4d6d',
            boxShadow: meshStatus === 'live' ? '0 0 6px #00e676' : 'none',
          }} />
          {meshStatus === 'live'
            ? `MESH · ${meshStats?.nodes_online ?? meshNodes.length} sensors · ${meshStats?.detections ?? meshDetections.length}`
            : `MESH OFFLINE · ${meshDetections.length} cached`}
          {!showMesh && <span style={{ color: '#5a7a96' }}>(hidden)</span>}
        </button>

        {/* Feature 1: Replay panel — floats above the map */}
        {replayMode && (
          <ReplayPanel
            onClose={() => { setReplayMode(false); setReplayState(null) }}
            onReplayUpdate={handleReplayUpdate}
          />
        )}

        <StatusBar
          running={running}
          watcherCount={encounters.filter(e=>e.label==='Fun-Watcher').length}
          stopperCount={encounters.filter(e=>e.label==='Fun-Stopper').length}
          isOwner={mode === 'sovereign'}
        />

        {/* Scan console — desktop only, shows recent special device detections */}
        {!isMobile && scanLog.length > 0 && (
          <div className="scan-console">
            <div className="scan-console-header">SCAN LOG</div>
            {[...scanLog].reverse().map(entry => {
              const t = new Date(entry.ts)
              const hm = `${t.getHours().toString().padStart(2,'0')}:${t.getMinutes().toString().padStart(2,'0')}:${t.getSeconds().toString().padStart(2,'0')}`
              const label = entry.device_name || entry.device_type || entry.type || 'Device'
              const dist  = entry.distance != null ? `${entry.distance}m` : ''
              const rssi  = entry.rssi    != null ? `${Number(entry.rssi).toFixed(0)} dBm` : ''
              return (
                <div key={entry.id} className="scan-console-row">
                  <span className="sc-em">{entry.em}</span>
                  <span className="sc-label">{label}</span>
                  {rssi && <span className="sc-rssi">{rssi}</span>}
                  {dist && <span className="sc-dist">{dist}</span>}
                  <span className="sc-time">{hm}</span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  </AppErrorBoundary>
  )
}
