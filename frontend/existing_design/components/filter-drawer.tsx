'use client'

import { useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { familyStyle } from '@/lib/families'
import { formatClock, parseClock } from '@/lib/time'
import { cn } from '@/lib/utils'
import { useVisStore } from '@/store/vis-store'
import { useDataset } from './dataset-context'

type FilterKey = 'nodes' | 'families' | 'categories'

function countBy(values: string[]) {
  const m = new Map<string, number>()
  for (const v of values) m.set(v, (m.get(v) ?? 0) + 1)
  return m
}

export function FilterDrawer() {
  const ds = useDataset()
  const open = useVisStore((s) => s.filterDrawerOpen)
  const setOpen = useVisStore((s) => s.setFilterDrawerOpen)
  const filters = useVisStore((s) => s.filters)
  const toggle = useVisStore((s) => s.toggleFilterValue)
  const clear = useVisStore((s) => s.clearFilters)

  const counts = useMemo(
    () => ({
      nodes: countBy(ds.events.map((e) => e.node)),
      families: countBy(ds.events.map((e) => e.family)),
      categories: countBy(ds.events.map((e) => e.category)),
    }),
    [ds],
  )

  const groups: { key: FilterKey; title: string; values: string[] }[] = [
    { key: 'nodes', title: 'Nodes', values: ds.nodes },
    { key: 'families', title: 'Families', values: ds.families },
    { key: 'categories', title: 'Categories', values: ds.categories },
  ]

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetContent side="left" className="w-[min(360px,100vw)] gap-0 overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Filters</SheetTitle>
          <SheetDescription>Nothing selected in a group means all values are shown.</SheetDescription>
        </SheetHeader>

        <div className="flex flex-col gap-6 px-4 pb-4">
          {groups.map((g) => (
            <fieldset key={g.key} className="flex flex-col gap-2">
              <legend className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                {g.title}
              </legend>
              <div className="flex flex-wrap gap-1.5">
                {g.values.map((v) => {
                  const active = filters[g.key].includes(v)
                  const color = g.key === 'families' ? familyStyle(v).color : undefined
                  return (
                    <button
                      key={v}
                      type="button"
                      aria-pressed={active}
                      onClick={() => toggle(g.key, v)}
                      className={cn(
                        'inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs transition-colors hover:bg-accent',
                        g.key === 'categories' && 'capitalize',
                        g.key === 'nodes' && 'font-mono',
                        active && 'border-primary bg-primary/10 text-foreground',
                      )}
                    >
                      {color && <span className="size-2 rounded-full" style={{ backgroundColor: color }} aria-hidden />}
                      {v}
                      <span className="font-mono text-muted-foreground tabular-nums">{counts[g.key].get(v) ?? 0}</span>
                    </button>
                  )
                })}
              </div>
            </fieldset>
          ))}

          <TimeRangeFields />

          <section className="rounded-lg border bg-muted/40 p-3 text-xs">
            <h3 className="mb-2 font-semibold">Query syntax</h3>
            <ul className="flex flex-col gap-1 font-mono text-[11px] text-muted-foreground">
              <li>family:fault</li>
              <li>node:FMS2</li>
              <li>cat:operator</li>
              <li>code:&quot;Dual State Trans Timeout&quot;</li>
              <li>time:11:40-11:50</li>
              <li>flag:invalid · flag:na</li>
            </ul>
            <p className="mt-2 text-muted-foreground">Same key twice means OR; different keys mean AND. Plain words search text.</p>
          </section>
        </div>

        <SheetFooter className="border-t">
          <Button variant="outline" onClick={clear}>
            Clear all filters and search
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

function TimeRangeFields() {
  const ds = useDataset()
  const range = useVisStore((s) => s.filters.timeRange)
  const setRange = useVisStore((s) => s.setTimeRange)
  const [from, setFrom] = useState(range ? formatClock(range[0]) : '')
  const [to, setTo] = useState(range ? formatClock(range[1]) : '')
  const [error, setError] = useState<string | null>(null)

  const apply = () => {
    if (!from && !to) {
      setRange(null)
      setError(null)
      return
    }
    const a = from ? parseClock(from) : ds.startSec
    const b = to ? parseClock(to) : ds.endSec
    if (a == null || b == null) {
      setError('Use HH:MM or HH:MM:SS')
      return
    }
    setError(null)
    setRange([Math.min(a, b), Math.max(a, b)])
  }

  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Time range</legend>
      <div className="flex items-end gap-2">
        <label className="flex flex-1 flex-col gap-1 text-xs">
          From
          <input
            value={from}
            onChange={(e) => setFrom(e.target.value)}
            onBlur={apply}
            placeholder={formatClock(ds.startSec)}
            className="h-8 rounded-md border bg-background px-2 font-mono text-xs"
          />
        </label>
        <label className="flex flex-1 flex-col gap-1 text-xs">
          To
          <input
            value={to}
            onChange={(e) => setTo(e.target.value)}
            onBlur={apply}
            placeholder={formatClock(ds.endSec)}
            className="h-8 rounded-md border bg-background px-2 font-mono text-xs"
          />
        </label>
      </div>
      {error && <p className="text-xs text-destructive">{error}</p>}
      <p className="text-[11px] text-muted-foreground">You can also drag across the time strip.</p>
    </fieldset>
  )
}
