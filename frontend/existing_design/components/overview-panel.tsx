'use client'

import { useMemo } from 'react'
import { ChevronDown, LifeBuoy } from 'lucide-react'
import { formatClock, formatDuration } from '@/lib/time'
import { cn } from '@/lib/utils'
import { useVisStore } from '@/store/vis-store'
import { useDataset, useFocusEvent } from './dataset-context'
import { EventChip, LabelTag, MissingValue } from './common/primitives'

export function OverviewPanel() {
  const ds = useDataset()
  const focus = useFocusEvent()
  const open = useVisStore((s) => s.overviewOpen)
  const setOpen = useVisStore((s) => s.setOverviewOpen)
  const setTimeRange = useVisStore((s) => s.setTimeRange)

  const faultGroups = useMemo(() => {
    const groups = new Map<string, { name: string; code: string; ids: string[]; nodes: Set<string> }>()
    for (const e of ds.events) {
      if (e.family !== 'Fault') continue
      const key = `${e.code}|${e.name}`
      const g = groups.get(key) ?? { name: e.name, code: e.code, ids: [], nodes: new Set<string>() }
      g.ids.push(e.id)
      g.nodes.add(e.node)
      groups.set(key, g)
    }
    return [...groups.values()].sort((a, b) => ds.indexById.get(a.ids[0])! - ds.indexById.get(b.ids[0])!)
  }, [ds])

  const duration = ds.endSec - ds.startSec

  return (
    <section aria-labelledby="overview-title" className="border-b">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-controls="overview-body"
        className="flex w-full items-center gap-3 px-4 py-2 text-left hover:bg-accent/50"
      >
        <h2 id="overview-title" className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          Flight overview
        </h2>
        <span className="font-mono text-xs text-muted-foreground">
          {formatClock(ds.startSec)} – {formatClock(ds.endSec)} · {formatDuration(duration)} · {faultGroups.length}{' '}
          fault types · {ds.reboots.length} reboots
        </span>
        <ChevronDown className={cn('ml-auto size-4 text-muted-foreground transition-transform', open && 'rotate-180')} aria-hidden />
      </button>

      {open && (
        <div id="overview-body" className="grid gap-4 px-4 pt-1 pb-4 md:grid-cols-3">
          <div className="flex flex-col gap-2">
            <h3 className="text-xs font-medium text-muted-foreground">Phases</h3>
            {ds.phases.length ? (
              <ol className="flex flex-wrap gap-1.5">
                {ds.phases.map((p) => (
                  <li key={p.eventId}>
                    <button
                      type="button"
                      onClick={() => focus(p.eventId)}
                      className="rounded-md border px-2 py-1 text-left text-[11px] hover:border-primary hover:bg-accent"
                    >
                      <span className="block font-medium">{p.name}</span>
                      <span className="block font-mono text-muted-foreground">{formatClock(p.startSec, false)}</span>
                    </button>
                  </li>
                ))}
              </ol>
            ) : (
              <MissingValue>No phase changes in data</MissingValue>
            )}
          </div>

          <div className="flex flex-col gap-2">
            <h3 className="text-xs font-medium text-muted-foreground">Significant faults</h3>
            {faultGroups.length ? (
              <ul className="flex flex-col gap-1">
                {faultGroups.map((g) => (
                  <li key={`${g.code}${g.name}`}>
                    <button
                      type="button"
                      onClick={() => focus(g.ids[0])}
                      className="flex w-full items-center gap-2 rounded-md px-1.5 py-1 text-left text-xs hover:bg-accent"
                    >
                      <span className="size-1.5 shrink-0 rounded-full bg-fam-fault" aria-hidden />
                      <span className="font-mono text-muted-foreground">{ds.byId.get(g.ids[0])!.time24}</span>
                      <span className="truncate font-medium">{g.name}</span>
                      <span className="ml-auto shrink-0 font-mono text-[11px] text-muted-foreground">
                        {[...g.nodes].join(' ')}
                        {g.ids.length > 1 && ` ×${g.ids.length}`}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-muted-foreground">No Fault-family events.</p>
            )}
          </div>

          <div className="flex flex-col gap-2">
            <h3 className="text-xs font-medium text-muted-foreground">Incidents &amp; recovery</h3>
            {ds.incidents === null ? (
              <MissingValue>incidents.json not supplied</MissingValue>
            ) : ds.incidents.length === 0 ? (
              <p className="text-xs text-muted-foreground">No incidents identified.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {ds.incidents.map((inc) => {
                  const recovery = inc.recoveryEventId ? ds.byId.get(inc.recoveryEventId) : undefined
                  const label = recovery ? 'confirmed' : inc.eventIds.length ? 'probable' : 'missing'
                  return (
                    <li key={inc.id} className="flex flex-col gap-1">
                      <button
                        type="button"
                        onClick={() =>
                          inc.eventIds[0] ? focus(inc.eventIds[0], 'inference') : setTimeRange([inc.startSec, inc.endSec])
                        }
                        className="flex items-start gap-2 rounded-md px-1.5 py-1 text-left text-xs hover:bg-accent"
                      >
                        <span className="font-mono text-muted-foreground">{formatClock(inc.startSec, false)}</span>
                        <span className="font-medium text-pretty">{inc.title}</span>
                      </button>
                      <div className="flex flex-wrap items-center gap-1.5 pl-1.5 text-[11px] text-muted-foreground">
                        <LabelTag label={label} />
                        {recovery ? (
                          <>
                            <LifeBuoy className="size-3" aria-hidden />
                            recovered in {formatDuration(recovery.tsSec - inc.startSec)}
                            <EventChip id={recovery.id} />
                          </>
                        ) : (
                          <span>No recovery event recorded</span>
                        )}
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
