'use client'

import { useEffect } from 'react'
import { useVisStore } from '@/store/vis-store'

const TICK_MS = 100

/** Advances the replay clock while playing. Updates are throttled so the feed is not rebuilt every frame. */
export function usePlayback(startSec: number, endSec: number) {
  const playing = useVisStore((s) => s.playing)

  useEffect(() => {
    if (!playing) return
    const { clockSec, setClock } = useVisStore.getState()
    if (clockSec === null || clockSec >= endSec) setClock(startSec)

    let last = performance.now()
    const id = window.setInterval(() => {
      const now = performance.now()
      const dt = (now - last) / 1000
      last = now
      const s = useVisStore.getState()
      const next = (s.clockSec ?? startSec) + dt * s.speed
      if (next >= endSec) {
        s.setClock(null)
        s.setPlaying(false)
      } else {
        s.setClock(next)
      }
    }, TICK_MS)
    return () => window.clearInterval(id)
  }, [playing, startSec, endSec])
}
