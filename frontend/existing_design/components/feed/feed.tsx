'use client'

import { useCallback, useEffect, useLayoutEffect, useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { ArrowDown, Download, SearchX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { translationFor } from '@/lib/derive'
import { toCsv, toJson, downloadText } from '@/lib/export'
import { burstKeyFor, rowIndexFor } from '@/lib/feed'
import { useVisStore } from '@/store/vis-store'
import { useDataset, useFeedView } from '../dataset-context'
import { BurstCard, SessionDivider } from './feed-rows'
import { LogCard } from './log-card'

const BOTTOM_THRESHOLD_PX = 48

export function Feed() {
  const ds = useDataset()
  const { rows, filtered, visible, query } = useFeedView()
  const selectedId = useVisStore((s) => s.selectedId)
  const selectEvent = useVisStore((s) => s.selectEvent)
  const toggleBurst = useVisStore((s) => s.toggleBurst)
  const following = useVisStore((s) => s.following)
  const setFollowing = useVisStore((s) => s.setFollowing)
  const scrollRequest = useVisStore((s) => s.scrollRequest)
  const clearFilters = useVisStore((s) => s.clearFilters)

  const scrollRef = useRef<HTMLDivElement>(null)
  const seenIds = useRef<Set<string> | null>(null)
  const programmaticScroll = useRef(false)

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: (i) => (rows[i].kind === 'divider' ? 44 : rows[i].kind === 'burst' ? 48 : 120),
    getItemKey: (i) => rows[i].key,
    overscan: 8,
    paddingStart: 12,
    paddingEnd: 12,
    gap: 8,
  })

  // Cards that appear after the first render get an entry animation.
  if (seenIds.current === null) seenIds.current = new Set(rows.map((r) => r.key))
  const isNew = (key: string) => !seenIds.current!.has(key)
  useEffect(() => {
    for (const r of rows) seenIds.current!.add(r.key)
  }, [rows])

  const scrollToIndex = useCallback(
    (index: number, align: 'center' | 'end') => {
      programmaticScroll.current = true
      virtualizer.scrollToIndex(index, { align })
      requestAnimationFrame(() => {
        programmaticScroll.current = false
      })
    },
    [virtualizer],
  )

  useLayoutEffect(() => {
    if (following && rows.length) scrollToIndex(rows.length - 1, 'end')
  }, [following, rows.length, scrollToIndex])

  const handledNonce = useRef(0)
  useEffect(() => {
    if (!scrollRequest || scrollRequest.nonce === handledNonce.current) return
    const burst = burstKeyFor(rows, scrollRequest.id)
    if (burst && !rows.some((r) => r.kind === 'burst' && r.key === burst && r.expanded)) {
      toggleBurst(burst, true)
      return
    }
    const index = rowIndexFor(rows, scrollRequest.id)
    handledNonce.current = scrollRequest.nonce
    if (index >= 0) scrollToIndex(index, 'center')
  }, [scrollRequest, rows, toggleBurst, scrollToIndex])

  const onScroll = () => {
    const el = scrollRef.current
    if (!el || programmaticScroll.current) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < BOTTOM_THRESHOLD_PX
    if (atBottom !== following) setFollowing(atBottom)
  }

  const selectedHidden = selectedId !== null && !filtered.some((e) => e.id === selectedId)
  const hasQuery = !query.isEmpty

  return (
    <section aria-label="Event feed" className="relative flex min-h-0 flex-1 flex-col">
      <div className="flex flex-wrap items-center gap-2 border-b px-4 py-1.5 text-xs">
        <span className="text-muted-foreground">
          Showing <span className="font-mono text-foreground tabular-nums">{visible.length}</span> of{' '}
          <span className="font-mono tabular-nums">{filtered.length}</span> matching
          {filtered.length !== ds.events.length && (
            <>
              {' '}
              (<span className="font-mono tabular-nums">{ds.events.length}</span> total)
            </>
          )}
        </span>
        {query.errors.length > 0 && <span className="text-destructive">{query.errors.join(' · ')}</span>}
        {selectedHidden && <span className="text-probable">Selected event is hidden by current filters</span>}
        <div className="ml-auto flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1 px-2 text-xs"
            onClick={() => downloadText('fms-events.csv', toCsv(filtered, ds.translations), 'text/csv')}
            disabled={!filtered.length}
          >
            <Download className="size-3.5" aria-hidden /> CSV
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1 px-2 text-xs"
            onClick={() => downloadText('fms-events.json', toJson(filtered, ds.translations), 'application/json')}
            disabled={!filtered.length}
          >
            <Download className="size-3.5" aria-hidden /> JSON
          </Button>
        </div>
      </div>

      <div ref={scrollRef} onScroll={onScroll} className="min-h-0 flex-1 overflow-y-auto px-3 sm:px-4" role="feed" aria-busy={false}>
        {rows.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 p-8 text-center">
            <SearchX className="size-8 text-muted-foreground" aria-hidden />
            <p className="text-sm font-medium">
              {filtered.length === 0 ? 'No events match these filters' : 'No events yet at this replay time'}
            </p>
            {(filtered.length === 0 || hasQuery) && (
              <Button variant="outline" size="sm" onClick={clearFilters}>
                Clear filters
              </Button>
            )}
          </div>
        ) : (
          <div className="relative w-full" style={{ height: virtualizer.getTotalSize() }}>
            {virtualizer.getVirtualItems().map((item) => {
              const row = rows[item.index]
              return (
                <div
                  key={item.key}
                  data-index={item.index}
                  ref={virtualizer.measureElement}
                  className="absolute top-0 left-0 w-full"
                  style={{ transform: `translateY(${item.start}px)` }}
                >
                  {row.kind === 'divider' ? (
                    <SessionDivider reboot={row.reboot} onSelect={selectEvent} />
                  ) : row.kind === 'burst' ? (
                    <BurstCard
                      burstKey={row.key}
                      events={row.events}
                      expanded={row.expanded}
                      selected={!row.expanded && row.events.some((e) => e.id === selectedId)}
                      onToggle={toggleBurst}
                      onSelect={selectEvent}
                    />
                  ) : (
                    <LogCard
                      event={row.event}
                      translation={translationFor(ds, row.event.id)}
                      selected={row.event.id === selectedId}
                      isNew={isNew(row.key)}
                      incidentCount={ds.incidentsByEvent.get(row.event.id)?.length ?? 0}
                      indented={!!row.inBurst}
                      onSelect={selectEvent}
                    />
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {!following && rows.length > 0 && (
        <Button
          size="sm"
          onClick={() => setFollowing(true)}
          className="absolute bottom-4 left-1/2 -translate-x-1/2 gap-1.5 rounded-full shadow-lg"
        >
          <ArrowDown className="size-4" aria-hidden />
          Jump to latest
        </Button>
      )}
    </section>
  )
}
