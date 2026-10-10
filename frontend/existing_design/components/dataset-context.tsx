'use client'

import { createContext, useCallback, useContext, useMemo } from 'react'
import { useShallow } from 'zustand/react/shallow'
import type { LogEvent } from '@/data/schemas'
import type { Dataset } from '@/lib/derive'
import { buildRows, filterEvents, type FeedRow } from '@/lib/feed'
import { parseQuery, type ParsedQuery } from '@/lib/query'
import { useVisStore, type DetailTab } from '@/store/vis-store'

const DatasetContext = createContext<Dataset | null>(null)

export const DatasetProvider = DatasetContext.Provider

export function useDataset(): Dataset {
  const ds = useContext(DatasetContext)
  if (!ds) throw new Error('useDataset must be used inside DatasetProvider')
  return ds
}

/** The one central action: select a card, open the panel and scroll the feed to it. */
export function useFocusEvent() {
  const ds = useDataset()
  const focusEvent = useVisStore((s) => s.focusEvent)
  return useCallback(
    (id: string, tab?: DetailTab) => focusEvent(id, { tab, tsSec: ds.byId.get(id)?.tsSec }),
    [ds, focusEvent],
  )
}

export function useClock(): number {
  const ds = useDataset()
  const clock = useVisStore((s) => s.clockSec)
  return clock ?? ds.endSec
}

export interface FeedView {
  query: ParsedQuery
  filtered: LogEvent[]
  visible: LogEvent[]
  rows: FeedRow[]
}

const FeedViewContext = createContext<FeedView | null>(null)
export const FeedViewProvider = FeedViewContext.Provider

export function useFeedView(): FeedView {
  const view = useContext(FeedViewContext)
  if (!view) throw new Error('useFeedView must be used inside FeedViewProvider')
  return view
}

export function useComputeFeedView(): FeedView {
  const ds = useDataset()
  const { filters, queryText, expanded } = useVisStore(
    useShallow((s) => ({ filters: s.filters, queryText: s.query, expanded: s.expandedBursts })),
  )
  const clock = useClock()

  const query = useMemo(() => parseQuery(queryText), [queryText])
  const filtered = useMemo(() => filterEvents(ds, filters, query), [ds, filters, query])
  const visible = useMemo(() => {
    if (clock >= ds.endSec) return filtered
    let end = filtered.length
    while (end > 0 && filtered[end - 1].tsSec > clock) end--
    return filtered.slice(0, end)
  }, [filtered, clock, ds.endSec])
  const rows = useMemo(() => buildRows(ds, visible, new Set(expanded)), [ds, visible, expanded])

  return useMemo(() => ({ query, filtered, visible, rows }), [query, filtered, visible, rows])
}
