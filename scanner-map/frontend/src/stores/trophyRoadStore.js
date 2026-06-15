// trophyRoadStore.js — trophy-road client store.
//
// ⚠️ AUTO-GENERATED PLACEHOLDER (created during Linux server setup, 2026-06-12).
// `../stores/trophyRoadStore` is imported by components/DevAssetOps.jsx but the
// file (and the whole src/stores dir) was never committed to the repo. This
// minimal hook satisfies the used shape `{ assets, milestones, hydrate, connect }`
// so the frontend builds. Replace with the real store.
// See scanner-map/SETUP_NOTES.md.
import { useMemo, useState } from 'react'

export function useTrophyRoadStore() {
  const [assets] = useState([])
  const [milestones] = useState([])
  // Stable no-op callbacks so effects depending on them don't loop.
  return useMemo(
    () => ({
      assets,
      milestones,
      hydrate: () => {},
      connect: () => {},
    }),
    [assets, milestones],
  )
}

export default useTrophyRoadStore
