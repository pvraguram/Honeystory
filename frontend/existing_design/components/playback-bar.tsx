'use client'

import { Pause, Play, RotateCcw } from 'lucide-react'
import { phaseAt } from '@/lib/derive'
import { formatClock } from '@/lib/time'
import { cn } from '@/lib/utils'
import { SPEEDS, useVisStore } from '@/store/vis-store'
import { useClock, useDataset } from './dataset-context'

export function PlaybackBar() {
  const ds = useDataset()
  const clock = useClock()
  const playing = useVisStore((s) => s.playing)
  const speed = useVisStore((s) => s.speed)
  const setPlaying = useVisStore((s) => s.setPlaying)
  const setSpeed = useVisStore((s) => s.setSpeed)
  const setClock = useVisStore((s) => s.setClock)
  const atEnd = clock >= ds.endSec
  const phase = phaseAt(ds, clock)

  return (
    <div className="flex flex-wrap items-center gap-3 border-b px-4 py-2">
      <button
        type="button"
        onClick={() => setPlaying(!playing)}
        className="flex size-9 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform hover:scale-105 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background focus-visible:outline-none"
        aria-label={playing ? 'Pause replay' : atEnd ? 'Replay from start' : 'Play replay'}
      >
        {playing ? <Pause className="size-4" /> : atEnd ? <RotateCcw className="size-4" /> : <Play className="size-4 translate-x-px" />}
      </button>

      <div role="radiogroup" aria-label="Replay speed" className="flex rounded-lg border p-0.5">
        {SPEEDS.map((s) => (
          <button
            key={s}
            type="button"
            role="radio"
            aria-checked={speed === s}
            onClick={() => setSpeed(s)}
            className={cn(
              'rounded-md px-2 py-0.5 font-mono text-xs transition-colors',
              speed === s ? 'bg-secondary text-foreground' : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {s}×
          </button>
        ))}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="font-mono text-lg font-semibold tabular-nums">{formatClock(clock)}</span>
        <span className="text-xs text-muted-foreground">{phase?.name ?? 'Phase not in data'}</span>
      </div>

      <label className="flex min-w-40 flex-1 items-center gap-2">
        <span className="sr-only">Scrub replay position</span>
        <input
          type="range"
          min={ds.startSec}
          max={ds.endSec}
          step={1}
          value={Math.round(clock)}
          onChange={(e) => {
            const v = Number(e.target.value)
            setClock(v >= ds.endSec ? null : v)
          }}
          className="w-full accent-primary"
        />
      </label>

      <span className={cn('flex items-center gap-1.5 text-xs', atEnd ? 'text-confirmed' : 'text-muted-foreground')}>
        <span className={cn('size-2 rounded-full', atEnd ? 'bg-confirmed' : playing ? 'animate-pulse bg-primary' : 'bg-muted-foreground')} aria-hidden />
        {atEnd ? 'All events loaded' : playing ? 'Replaying' : 'Paused'}
      </span>
    </div>
  )
}
