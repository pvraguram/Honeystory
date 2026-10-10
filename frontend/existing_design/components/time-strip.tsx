'use client'

import { useMemo, useRef, useState } from 'react'
import { X } from 'lucide-react'
import { familyStyle } from '@/lib/families'
import { formatClock } from '@/lib/time'
import { useVisStore } from '@/store/vis-store'
import { useClock, useDataset, useFocusEvent } from './dataset-context'

const BINS = 96
const DRAG_THRESHOLD_PX = 4

export function TimeStrip() {
  const ds = useDataset()
  const focus = useFocusEvent()
  const clock = useClock()
  const range = useVisStore((s) => s.filters.timeRange)
  const setRange = useVisStore((s) => s.setTimeRange)
  const setClock = useVisStore((s) => s.setClock)
  const trackRef = useRef<HTMLDivElement>(null)
  const [drag, setDrag] = useState<{ startX: number; a: number; b: number } | null>(null)

  const span = Math.max(1, ds.endSec - ds.startSec)
  const pct = (sec: number) => `${((sec - ds.startSec) / span) * 100}%`

  const bins = useMemo(() => {
    const result = Array.from({ length: BINS }, () => new Map<string, number>())
    for (const e of ds.events) {
      const i = Math.min(BINS - 1, Math.floor(((e.tsSec - ds.startSec) / span) * BINS))
      result[i].set(e.family, (result[i].get(e.family) ?? 0) + 1)
    }
    return result
  }, [ds, span])
  const maxBin = Math.max(1, ...bins.map((b) => [...b.values()].reduce((x, y) => x + y, 0)))

  const secAt = (clientX: number) => {
    const rect = trackRef.current!.getBoundingClientRect()
    const f = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width))
    return ds.startSec + f * span
  }

  const onPointerDown = (e: React.PointerEvent) => {
    if (e.button !== 0) return
    e.currentTarget.setPointerCapture(e.pointerId)
    const s = secAt(e.clientX)
    setDrag({ startX: e.clientX, a: s, b: s })
  }
  const onPointerMove = (e: React.PointerEvent) => {
    if (drag) setDrag({ ...drag, b: secAt(e.clientX) })
  }
  const onPointerUp = (e: React.PointerEvent) => {
    if (!drag) return
    if (Math.abs(e.clientX - drag.startX) < DRAG_THRESHOLD_PX) {
      const s = secAt(e.clientX)
      setClock(s >= ds.endSec ? null : s)
    } else {
      setRange([Math.floor(Math.min(drag.a, drag.b)), Math.ceil(Math.max(drag.a, drag.b))])
    }
    setDrag(null)
  }

  const shownRange = drag && Math.abs(drag.b - drag.a) > 0 ? [Math.min(drag.a, drag.b), Math.max(drag.a, drag.b)] : range

  return (
    <section aria-label="Flight timeline" className="border-b px-4 pt-2 pb-1">
      <div className="mb-1 flex items-center gap-3 text-[11px] text-muted-foreground">
        <span className="font-medium tracking-wide uppercase">Timeline</span>
        <span className="hidden sm:inline">Click to seek · drag to filter a time window</span>
        {range && (
          <button
            type="button"
            onClick={() => setRange(null)}
            className="ml-auto inline-flex items-center gap-1 rounded-md border border-primary/50 bg-primary/10 px-1.5 py-0.5 font-mono text-foreground"
          >
            {formatClock(range[0])}–{formatClock(range[1])}
            <X className="size-3" aria-label="Clear time window" />
          </button>
        )}
      </div>

      <div
        ref={trackRef}
        role="slider"
        aria-label="Replay position"
        aria-valuemin={ds.startSec}
        aria-valuemax={ds.endSec}
        aria-valuenow={Math.round(clock)}
        aria-valuetext={formatClock(clock)}
        tabIndex={0}
        onKeyDown={(e) => {
          const step = e.shiftKey ? 300 : 30
          if (e.key === 'ArrowRight') setClock(Math.min(ds.endSec, clock + step) >= ds.endSec ? null : clock + step)
          if (e.key === 'ArrowLeft') setClock(Math.max(ds.startSec, clock - step))
        }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        className="relative h-20 cursor-crosshair touch-none rounded-md bg-muted/50 select-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
      >
        {ds.phases.map((p, i) => (
          <div
            key={p.eventId}
            className="absolute inset-y-0 border-l border-border"
            style={{ left: pct(p.startSec), width: `calc(${pct(p.endSec)} - ${pct(p.startSec)})`, backgroundColor: i % 2 ? 'transparent' : 'color-mix(in oklab, var(--foreground) 3%, transparent)' }}
          >
            <span className="absolute top-1 left-1 truncate text-[9px] font-semibold tracking-wide text-muted-foreground uppercase">
              {p.name}
            </span>
          </div>
        ))}

        {ds.gaps.map((g) => (
          <div
            key={`${g.node}-${g.startSec}`}
            className="bg-hatch absolute bottom-0 h-1/2 opacity-80"
            style={{ left: pct(g.startSec), width: `calc(${pct(g.endSec)} - ${pct(g.startSec)})` }}
            title={`No ${g.node} logs ${formatClock(g.startSec)}–${formatClock(g.endSec)}`}
          >
            <span className="absolute -top-3.5 left-0 font-mono text-[9px] text-muted-foreground">{g.node} gap</span>
          </div>
        ))}

        <div className="absolute inset-x-0 bottom-0 flex h-[55%] items-end gap-px px-px" aria-hidden>
          {bins.map((bin, i) => {
            const total = [...bin.values()].reduce((a, b) => a + b, 0)
            return (
              <div key={i} className="flex flex-1 flex-col-reverse overflow-hidden rounded-t-[1px]" style={{ height: `${(total / maxBin) * 100}%` }}>
                {[...bin.entries()].map(([fam, n]) => (
                  <div key={fam} style={{ height: `${(n / total) * 100}%`, backgroundColor: familyStyle(fam).color }} />
                ))}
              </div>
            )
          })}
        </div>

        {ds.reboots.map((r) => (
          <button
            key={r.eventId}
            type="button"
            onPointerDown={(e) => e.stopPropagation()}
            onClick={() => focus(r.eventId)}
            className="group absolute inset-y-0 w-3 -translate-x-1/2"
            style={{ left: pct(r.tsSec) }}
            aria-label={`${r.node} reboot at ${r.time24}`}
          >
            <span className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 border-l border-dashed border-fam-fault" />
            <span className="absolute top-1 left-1/2 -translate-x-1/2 rounded bg-fam-fault px-1 font-mono text-[9px] font-semibold text-background">
              {r.node}
            </span>
          </button>
        ))}

        {shownRange && (
          <div
            className="pointer-events-none absolute inset-y-0 border-x-2 border-primary bg-primary/15"
            style={{ left: pct(shownRange[0]), width: `calc(${pct(shownRange[1])} - ${pct(shownRange[0])})` }}
          />
        )}

        <div className="pointer-events-none absolute inset-y-0 w-0.5 -translate-x-1/2 bg-foreground" style={{ left: pct(clock) }}>
          <span className="absolute -top-0.5 left-1/2 size-2 -translate-x-1/2 rotate-45 bg-foreground" />
        </div>
      </div>

      <div className="mt-1 flex justify-between font-mono text-[10px] text-muted-foreground">
        <span>{formatClock(ds.startSec, false)}</span>
        <span>{formatClock(ds.startSec + span / 2, false)}</span>
        <span>{formatClock(ds.endSec, false)}</span>
      </div>
    </section>
  )
}
