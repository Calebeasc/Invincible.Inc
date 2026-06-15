// VehicleModelPreview.jsx — preview pane for uploaded/builtin vehicle 3D models.
//
// ⚠️ AUTO-GENERATED PLACEHOLDER (created during Linux server setup, 2026-06-12).
// Lazy-imported by components/DevAssetOps.jsx
// (`lazy(() => import('./VehicleModelPreview'))`, used with props
// { modelUrl, builtinVehicleId, height }) but never committed to the repo.
// This stub renders a sized placeholder box so the frontend builds and the
// Suspense boundaries resolve. Replace with the real (likely three.js) preview.
// See scanner-map/SETUP_NOTES.md.
import React from 'react'

export default function VehicleModelPreview({ modelUrl = '', builtinVehicleId = '', height = 180 }) {
  const label = builtinVehicleId || modelUrl || 'No model'
  return (
    <div
      style={{
        height,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        border: '1px dashed rgba(255,255,255,0.18)',
        borderRadius: 8,
        background: 'rgba(8,12,20,0.6)',
        color: '#9aa7b8',
        fontSize: 12,
        gap: 4,
        padding: 8,
        textAlign: 'center',
        overflow: 'hidden',
      }}
    >
      <div style={{ fontWeight: 600 }}>3D preview unavailable</div>
      <div style={{ opacity: 0.7, wordBreak: 'break-all' }}>{label}</div>
    </div>
  )
}
