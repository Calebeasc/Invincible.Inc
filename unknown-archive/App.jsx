import React, { useState, useEffect, useCallback } from 'react'
import MapView from './components/MapView'
import Sidebar from './components/Sidebar'
import StatusBar from './components/StatusBar'
import './App.css'

const API = ''  // same origin in production; vite proxy in dev

export default function App() {
  const [running, setRunning]       = useState(false)
  const [timeRange, setTimeRange]   = useState(3600000)   // 1 hour in ms
  const [heatCells, setHeatCells]   = useState([])
  const [encounters, setEncounters] = useState([])
  const [showMarkers, setShowMarkers] = useState(true)
  const [loading, setLoading]       = useState(false)
  const [lastPoll, setLastPoll]     = useState(null)

  // ── Poll backend ──────────────────────────────────────────────────────────
  const refresh = useCallback(async () => {
    const since = Date.now() - timeRange
    try {
      const [hRes, eRes] = await Promise.all([
        fetch(`${API}/heatmap?since=${since}`),
        fetch(`${API}/encounters?since=${since}&limit=20`),
      ])
      if (hRes.ok) setHeatCells((await hRes.json()).cells || [])
      if (eRes.ok) setEncounters((await eRes.json()).encounters || [])
      setLastPoll(new Date())
    } catch { /* backend not ready yet */ }
  }, [timeRange])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 3000)
    return () => clearInterval(id)
  }, [refresh])

  // ── Control ───────────────────────────────────────────────────────────────
  useEffect(() => {
    fetch(`${API}/control/status`)
      .then(r => r.json())
      .then(d => setRunning(d.running))
      .catch(() => {})
  }, [])

  const toggleScanning = async () => {
    setLoading(true)
    const endpoint = running ? '/control/stop' : '/control/start'
    try {
      await fetch(`${API}${endpoint}`, { method: 'POST' })
      setRunning(!running)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        running={running}
        loading={loading}
        timeRange={timeRange}
        setTimeRange={setTimeRange}
        showMarkers={showMarkers}
        setShowMarkers={setShowMarkers}
        onToggle={toggleScanning}
        heatCells={heatCells}
        encounters={encounters}
        api={API}
      />
      <div className="map-area">
        <MapView
          heatCells={heatCells}
          encounters={encounters}
          showMarkers={showMarkers}
        />
        <StatusBar running={running} lastPoll={lastPoll} cellCount={heatCells.length} />
      </div>
    </div>
  )
}
