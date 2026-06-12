import React from 'react'

const TIME_RANGES = [
  { label: '15m',  ms: 15 * 60 * 1000 },
  { label: '1h',   ms: 60 * 60 * 1000 },
  { label: '6h',   ms: 6 * 60 * 60 * 1000 },
  { label: '24h',  ms: 24 * 60 * 60 * 1000 },
]

function fmt(enc) {
  const t = new Date(enc.peak_ts_ms)
  return `${t.toLocaleTimeString()} · ${enc.rssi_max?.toFixed(0)} dBm · ${enc.hit_count} hits`
}

export default function Sidebar({
  running, loading, timeRange, setTimeRange,
  showMarkers, setShowMarkers,
  onToggle, heatCells, encounters, api,
}) {
  const watcherCount = encounters.filter(e => e.label === 'Fun-Watcher').length
  const stopperCount = encounters.filter(e => e.label === 'Fun-Stopper').length

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1>Invincible.Inc</h1>
        <p>Authorized target scanner</p>
      </div>

      <div className="sidebar-body">
        {/* Scan control */}
        <button
          className={`btn-scan${running ? ' running' : ''}${loading ? ' loading' : ''}`}
          onClick={onToggle}
          disabled={loading}
        >
          {loading ? 'WAIT...' : running ? '⬛ STOP SCANNING' : '▶ START SCANNING'}
        </button>

        {/* Time range */}
        <div>
          <div className="section-label">Time Range</div>
          <div className="range-row">
            {TIME_RANGES.map(r => (
              <button
                key={r.ms}
                className={`range-btn${timeRange === r.ms ? ' active' : ''}`}
                onClick={() => setTimeRange(r.ms)}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>

        {/* Toggles */}
        <div>
          <div className="section-label">Display</div>
          <div className="toggle-row">
            <label htmlFor="markers-toggle">Encounter markers</label>
            <div
              id="markers-toggle"
              className={`toggle${showMarkers ? ' on' : ''}`}
              onClick={() => setShowMarkers(v => !v)}
              role="switch"
              aria-checked={showMarkers}
            />
          </div>
        </div>

        {/* Stats */}
        <div>
          <div className="section-label">Stats</div>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="val">{heatCells.length}</div>
              <div className="lbl">Heat Cells</div>
            </div>
            <div className="stat-card">
              <div className="val">{encounters.length}</div>
              <div className="lbl">Encounters</div>
            </div>
            <div className="stat-card" style={{ borderLeftColor: 'var(--watcher)', borderLeftWidth: 3 }}>
              <div className="val" style={{ color: 'var(--watcher)' }}>{watcherCount}</div>
              <div className="lbl">Fun-Watcher</div>
            </div>
            <div className="stat-card" style={{ borderLeftColor: 'var(--stopper)', borderLeftWidth: 3 }}>
              <div className="val" style={{ color: 'var(--stopper)' }}>{stopperCount}</div>
              <div className="lbl">Fun-Stopper</div>
            </div>
          </div>
        </div>

        {/* Recent encounters */}
        {encounters.length > 0 && (
          <div>
            <div className="section-label">Recent Encounters</div>
            <div className="enc-list">
              {encounters.slice(0, 12).map(enc => (
                <div
                  key={enc.id}
                  className={`enc-item${enc.label === 'Fun-Watcher' ? ' watcher' : enc.label === 'Fun-Stopper' ? ' stopper' : ''}`}
                >
                  <div className="enc-label">{enc.label || 'Target'}</div>
                  <div className="enc-meta">{fmt(enc)}</div>
                  {enc.show_timestamp && (
                    <div className="enc-meta" style={{ color: 'var(--stopper)' }}>
                      {new Date(enc.peak_ts_ms).toLocaleString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Exports */}
        <div>
          <div className="section-label">Export</div>
          <div className="export-row">
            <a href={`${api}/export/csv`} className="btn-export" download>RAW CSV</a>
            <a href={`${api}/export/encounters`} className="btn-export" download>ENC CSV</a>
            <a href={`${api}/export/geojson`} className="btn-export" download>GEOJSON</a>
          </div>
        </div>
      </div>
    </aside>
  )
}
