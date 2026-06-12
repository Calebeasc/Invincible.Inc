import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Leaflet.heat must be loaded after Leaflet
let heatPlugin = null

async function ensureHeatPlugin() {
  if (!heatPlugin) {
    // dynamically import so bundler doesn't complain
    await import('leaflet.heat')
    heatPlugin = true
  }
}

// Phoenix, AZ default center
const DEFAULT_CENTER = [33.4484, -112.074]
const DEFAULT_ZOOM   = 13

export default function MapView({ heatCells, encounters, showMarkers }) {
  const containerRef = useRef(null)
  const mapRef       = useRef(null)
  const heatLayerRef = useRef(null)
  const markerLayerRef = useRef(null)

  // ── Init map once ────────────────────────────────────────────────────────
  useEffect(() => {
    ensureHeatPlugin().then(() => {
      if (mapRef.current) return  // already initialised

      const map = L.map(containerRef.current, {
        center: DEFAULT_CENTER,
        zoom: DEFAULT_ZOOM,
        zoomControl: true,
        attributionControl: true,
      })

      // Dark OSM tile layer via CartoDB dark matter (free, no key)
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OSM contributors',
        subdomains: 'abcd',
        maxZoom: 19,
      }).addTo(map)

      mapRef.current = map

      // Force correct size after mount
      setTimeout(() => {
        if (mapRef.current) map.invalidateSize()
      }, 100)

      // Also handle window resize
      const resizeHandler = () => {
        if (mapRef.current) map.invalidateSize()
      }
      window.addEventListener('resize', resizeHandler)
      map._invincible_resize_handler = resizeHandler
    })

    return () => {
      if (mapRef.current) {
        if (mapRef.current._invincible_resize_handler) {
          window.removeEventListener('resize', mapRef.current._invincible_resize_handler)
        }
        mapRef.current.remove()
        mapRef.current = null
      }
    }
  }, [])

  // ── Update heat layer ────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current
    if (!map || !heatPlugin) return

    const points = heatCells
      .filter(c => c.lat && c.lon)
      .map(c => [c.lat, c.lon, c.intensity])

    if (heatLayerRef.current) {
      heatLayerRef.current.setLatLngs(points)
    } else {
      heatLayerRef.current = L.heatLayer(points, {
        radius: 35,
        blur: 25,
        maxZoom: 17,
        gradient: {
          0.0: '#0a1628',
          0.3: '#0d3b6e',
          0.5: '#0077cc',
          0.7: '#00d4ff',
          1.0: '#ffffff',
        },
      }).addTo(map)
    }
  }, [heatCells])

  // ── Update encounter markers ─────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    if (markerLayerRef.current) {
      markerLayerRef.current.clearLayers()
    } else {
      markerLayerRef.current = L.layerGroup().addTo(map)
    }

    if (!showMarkers) return

    // Show top-N by confidence (max 5 watcher, max 5 stopper)
    const watchers = encounters.filter(e => e.label === 'Fun-Watcher').slice(0, 5)
    const stoppers = encounters.filter(e => e.label === 'Fun-Stopper').slice(0, 5)
    const unlabeled = encounters.filter(e => !e.label).slice(0, 3)
    const toShow = [...watchers, ...stoppers, ...unlabeled]

    toShow.forEach(enc => {
      if (!enc.lat || !enc.lon) return
      const color = enc.color === 'red' ? '#ff4d6d' : enc.color === 'blue' ? '#2979ff' : '#00d4ff'

      const icon = L.divIcon({
        className: '',
        html: `<div style="
          width:12px;height:12px;
          border-radius:50%;
          background:${color};
          border:2px solid #fff;
          box-shadow:0 0 8px ${color};
        "></div>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6],
      })

      const ts = enc.show_timestamp
        ? `<br/><span style="color:#aaa;font-size:10px">${new Date(enc.peak_ts_ms).toLocaleString()}</span>`
        : ''

      const popup = `
        <div style="font-family:monospace;font-size:12px;color:#e0e0e0;background:#111820;padding:6px 8px;min-width:140px">
          <b style="color:${color}">${enc.label || 'Target'}</b><br/>
          RSSI: ${enc.rssi_max?.toFixed(1)} dBm<br/>
          Hits: ${enc.hit_count}${ts}
        </div>
      `

      L.marker([enc.lat, enc.lon], { icon })
        .bindPopup(popup, { className: 'dark-popup' })
        .addTo(markerLayerRef.current)
    })
  }, [encounters, showMarkers])

  return (
    <div
      ref={containerRef}
      className="map-container"
      style={{ flex: 1, width: '100%' }}
    />
  )
}
