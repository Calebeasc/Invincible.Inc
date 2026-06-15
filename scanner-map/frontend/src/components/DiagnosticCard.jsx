// DiagnosticCard.jsx — self-test / diagnostics card.
//
// ⚠️ AUTO-GENERATED PLACEHOLDER (created during Linux server setup, 2026-06-12).
// Imported by components/DevPanel.jsx (`<DiagnosticCard variant="dev"
// title="Run Self-Test" />`) but never committed to the repo. This minimal
// component renders a labeled card so the frontend builds. Replace with the
// real implementation. See scanner-map/SETUP_NOTES.md.
import React from 'react'

export default function DiagnosticCard({ variant = 'default', title = 'Diagnostics' }) {
  return (
    <div
      data-variant={variant}
      style={{
        border: '1px solid rgba(255,255,255,0.12)',
        background: 'rgba(8,12,20,0.88)',
        color: '#E8EDF5',
        borderRadius: 10,
        padding: 12,
        margin: '8px 0',
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{title}</div>
      <div style={{ fontSize: 12, opacity: 0.7 }}>
        Diagnostics placeholder — not yet implemented.
      </div>
    </div>
  )
}
