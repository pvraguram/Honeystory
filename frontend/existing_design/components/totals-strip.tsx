'use client'

import { useMemo } from 'react'
import { AlertTriangle, Check, FileX } from 'lucide-react'
import { familyStyle } from '@/lib/families'
import { cn } from '@/lib/utils'
import { useVisStore } from '@/store/vis-store'
import { useDataset } from './dataset-context'

export function TotalsStrip() {
  const ds = useDataset()
  const familyFilter = useVisStore((s) => s.filters.families)
  const toggle = useVisStore((s) => s.toggleFilterValue)
  const setSkippedOpen = useVisStore((s) => s.setSkippedOpen)

  const counts = useMemo(() => {
    const map = new Map<string, number>()
    for (const e of ds.events) map.set(e.family, (map.get(e.family) ?? 0) + 1)
    return map
  }, [ds])

  const { totals } = ds.report
  const loaded = ds.events.length
  const reconciles = totals.rowsIn === totals.events + totals.skipped && totals.events === loaded

  return (
    <div className="flex items-center gap-2 overflow-x-auto border-b px-4 py-2 text-xs [scrollbar-width:none]">
      <span className="shrink-0 font-medium">
        <span className="font-mono text-sm tabular-nums">{loaded}</span>{' '}
        <span className="text-muted-foreground">events</span>
      </span>
      <span className="h-4 w-px shrink-0 bg-border" aria-hidden />
      <ul className="flex shrink-0 items-center gap-1.5" aria-label="Events per family. Click to filter.">
        {ds.families.map((fam) => {
          const style = familyStyle(fam)
          const Icon = style.icon
          const active = familyFilter.includes(fam)
          return (
            <li key={fam}>
              <button
                type="button"
                aria-pressed={active}
                onClick={() => toggle('families', fam)}
                className={cn(
                  'inline-flex items-center gap-1.5 rounded-md border px-2 py-1 transition-colors hover:bg-accent',
                  active && 'border-transparent ring-1',
                )}
                style={active ? { boxShadow: `inset 0 0 0 1px ${style.color}` } : undefined}
              >
                <Icon className="size-3.5" style={{ color: style.color }} aria-hidden />
                <span className="font-medium">{style.label}</span>
                <span className="font-mono tabular-nums text-muted-foreground">{counts.get(fam) ?? 0}</span>
              </button>
            </li>
          )
        })}
      </ul>
      <span className="h-4 w-px shrink-0 bg-border" aria-hidden />
      <button
        type="button"
        onClick={() => setSkippedOpen(true)}
        className="inline-flex shrink-0 items-center gap-1.5 rounded-md border px-2 py-1 hover:bg-accent"
      >
        <FileX className="size-3.5 text-muted-foreground" aria-hidden />
        <span className="font-mono tabular-nums">{totals.skipped}</span> skipped
      </button>
      <span
        className={cn(
          'ml-auto inline-flex shrink-0 items-center gap-1.5 font-mono text-[11px]',
          reconciles ? 'text-muted-foreground' : 'text-destructive',
        )}
        title={reconciles ? 'Every input row is accounted for' : 'Import report and loaded events disagree'}
      >
        {reconciles ? <Check className="size-3.5 text-confirmed" aria-hidden /> : <AlertTriangle className="size-3.5" aria-hidden />}
        {totals.rowsIn} rows = {totals.events} events + {totals.skipped} skipped
        {totals.events !== loaded && ` (loaded ${loaded})`}
      </span>
    </div>
  )
}
