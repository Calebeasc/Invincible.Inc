import { useEffect, useRef, useState, useCallback } from 'react'

// useMesh — subscribe to the server's Omni-Mesh and keep a live, offline-safe
// picture of sensor nodes + their detections for the map.
//
// RESILIENCE CONTRACT (why this hook is defensive everywhere):
//   The phone must open and show the last-known mesh even if the server is down.
//   So we (1) hydrate from a localStorage cache on mount before any network,
//   (2) keep showing that cache while disconnected, (3) reconnect with capped
//   backoff, and (4) never throw — a dead server yields status:'offline', not a
//   broken app. The heavy lifting (fusing hundreds of sensors) stays on the
//   server; the client only applies ~1 small diff/sec.

const CACHE_KEY = 'sfm_mesh_cache_v1'
const PERSIST_EVERY_MS = 10000   // throttle localStorage writes — not every frame
const MAX_CACHE_DETS = 2000      // cap what we persist/expose so phones stay light
const BACKOFF_MIN = 1000
const BACKOFF_MAX = 30000

function loadCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return { nodes: [], detections: [] }
    const c = JSON.parse(raw)
    return { nodes: c.nodes || [], detections: c.detections || [] }
  } catch {
    return { nodes: [], detections: [] }
  }
}

export default function useMesh({ enabled = true } = {}) {
  const cached = loadCache()
  const [meshNodes, setMeshNodes] = useState(cached.nodes)
  const [meshDetections, setMeshDetections] = useState(cached.detections)
  const [meshStatus, setMeshStatus] = useState('connecting') // connecting | live | offline
  const [meshStats, setMeshStats] = useState(null)

  // Canonical maps live in refs so diff-application doesn't trigger renders;
  // we publish arrays to state on a natural ~1/sec cadence (diff arrival).
  const nodesRef = useRef(new Map(cached.nodes.map((n) => [n.device_id, n])))
  const detsRef = useRef(new Map(cached.detections.map((d) => [d.mac, d])))
  const wsRef = useRef(null)
  const backoffRef = useRef(BACKOFF_MIN)
  const reconnectTimerRef = useRef(null)
  const lastPersistRef = useRef(0)
  const aliveRef = useRef(true)

  const persist = useCallback((force = false) => {
    const now = Date.now()
    if (!force && now - lastPersistRef.current < PERSIST_EVERY_MS) return
    lastPersistRef.current = now
    try {
      const dets = [...detsRef.current.values()]
        .sort((a, b) => (b.last_seen || 0) - (a.last_seen || 0))
        .slice(0, MAX_CACHE_DETS)
      localStorage.setItem(CACHE_KEY, JSON.stringify({
        nodes: [...nodesRef.current.values()], detections: dets,
      }))
    } catch { /* quota / private mode — last-known just won't persist, no crash */ }
  }, [])

  const publish = useCallback(() => {
    setMeshNodes([...nodesRef.current.values()])
    setMeshDetections(
      [...detsRef.current.values()]
        .sort((a, b) => (b.last_seen || 0) - (a.last_seen || 0))
        .slice(0, MAX_CACHE_DETS),
    )
  }, [])

  const applyFrame = useCallback((frame) => {
    if (!frame || typeof frame !== 'object') return
    if (frame.t === 'snapshot') {
      nodesRef.current = new Map((frame.nodes || []).map((n) => [n.device_id, n]))
      detsRef.current = new Map((frame.detections || []).map((d) => [d.mac, d]))
    } else if (frame.t === 'diff') {
      for (const n of frame.nodes_upsert || []) nodesRef.current.set(n.device_id, n)
      for (const id of frame.nodes_remove || []) nodesRef.current.delete(id)
      for (const d of frame.det_upsert || []) detsRef.current.set(d.mac, d)
      for (const mac of frame.det_remove || []) detsRef.current.delete(mac)
    } else {
      return
    }
    if (frame.stats) setMeshStats(frame.stats)
    publish()
    persist()
  }, [publish, persist])

  const connect = useCallback(() => {
    if (!aliveRef.current) return
    let ws
    try {
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      ws = new WebSocket(`${proto}//${window.location.host}/mesh/ws`)
    } catch {
      // Construction itself can throw (bad URL / blocked) — treat as offline.
      setMeshStatus('offline')
      scheduleReconnect()
      return
    }
    wsRef.current = ws

    ws.onopen = () => {
      backoffRef.current = BACKOFF_MIN
      setMeshStatus('live')
    }
    ws.onmessage = (ev) => {
      try { applyFrame(JSON.parse(ev.data)) } catch { /* ignore a bad frame */ }
    }
    ws.onerror = () => { /* onclose will follow and handle reconnect */ }
    ws.onclose = () => {
      wsRef.current = null
      if (!aliveRef.current) return
      setMeshStatus('offline')   // keep showing last-known; just mark stale
      scheduleReconnect()
    }
  }, [applyFrame]) // eslint-disable-line react-hooks/exhaustive-deps

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimerRef.current) return
    const delay = backoffRef.current
    backoffRef.current = Math.min(backoffRef.current * 2, BACKOFF_MAX)
    reconnectTimerRef.current = setTimeout(() => {
      reconnectTimerRef.current = null
      connect()
    }, delay)
  }, [connect])

  useEffect(() => {
    if (!enabled) return undefined
    aliveRef.current = true
    connect()
    return () => {
      aliveRef.current = false
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
      persist(true)
      const ws = wsRef.current
      wsRef.current = null
      if (ws) { try { ws.onclose = null; ws.close() } catch { /* noop */ } }
    }
  }, [enabled, connect, persist])

  return { meshNodes, meshDetections, meshStatus, meshStats }
}
