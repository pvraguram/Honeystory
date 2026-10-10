import type { LogEvent } from '@/data/schemas'
import type { Dataset, Reboot } from './derive'
import { matchesQuery, type ParsedQuery } from './query'

export interface Filters {
  nodes: string[]
  families: string[]
  categories: string[]
  timeRange: [number, number] | null
}

export function filterEvents(ds: Dataset, filters: Filters, query: ParsedQuery): LogEvent[] {
  const { nodes, families, categories, timeRange } = filters
  return ds.events.filter(
    (e) =>
      (!nodes.length || nodes.includes(e.node)) &&
      (!families.length || families.includes(e.family)) &&
      (!categories.length || categories.includes(e.category)) &&
      (!timeRange || (e.tsSec >= timeRange[0] && e.tsSec <= timeRange[1])) &&
      matchesQuery(e, query, ds.translations[e.id] ?? null),
  )
}

export type FeedRow =
  | { kind: 'divider'; key: string; reboot: Reboot }
  | { kind: 'event'; key: string; event: LogEvent; inBurst?: string }
  | { kind: 'burst'; key: string; events: LogEvent[]; expanded: boolean }

const BURST_WINDOW_SEC = 1
const BURST_MIN = 3

const burstSignature = (e: LogEvent) => `${e.node}|${e.family}|${e.name}|${e.code}`

export function buildRows(ds: Dataset, events: LogEvent[], expanded: Set<string>): FeedRow[] {
  const rows: FeedRow[] = []
  const rebootById = new Map(ds.reboots.map((r) => [r.eventId, r]))
  let i = 0
  while (i < events.length) {
    const first = events[i]
    const sig = burstSignature(first)
    let j = i + 1
    while (
      j < events.length &&
      burstSignature(events[j]) === sig &&
      events[j].tsSec - first.tsSec <= BURST_WINDOW_SEC
    ) {
      j++
    }

    const reboot = rebootById.get(first.id)
    if (reboot) rows.push({ kind: 'divider', key: `div-${first.id}`, reboot })

    if (j - i >= BURST_MIN) {
      const group = events.slice(i, j)
      const key = `burst-${first.id}`
      const isOpen = expanded.has(key)
      rows.push({ kind: 'burst', key, events: group, expanded: isOpen })
      if (isOpen) {
        for (const e of group) rows.push({ kind: 'event', key: e.id, event: e, inBurst: key })
      }
      i = j
    } else {
      rows.push({ kind: 'event', key: first.id, event: first })
      i++
    }
  }
  return rows
}

export function burstKeyFor(rows: FeedRow[], eventId: string): string | null {
  for (const r of rows) {
    if (r.kind === 'burst' && r.events.some((e) => e.id === eventId)) return r.key
  }
  return null
}

export function rowIndexFor(rows: FeedRow[], eventId: string): number {
  return rows.findIndex(
    (r) =>
      (r.kind === 'event' && r.event.id === eventId) ||
      (r.kind === 'burst' && !r.expanded && r.events[0].id === eventId),
  )
}

/** Event ids in on-screen order, used for arrow-key navigation. */
export function navigableIds(rows: FeedRow[]): string[] {
  const ids: string[] = []
  for (const r of rows) {
    if (r.kind === 'event') ids.push(r.event.id)
    else if (r.kind === 'burst' && !r.expanded) ids.push(r.events[0].id)
  }
  return ids
}
