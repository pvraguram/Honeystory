import type { ImportReport, Incident, LogEvent, RawDataset, Translations } from '@/data/schemas'
import { sortFamilies } from './families'

export interface Phase {
  name: string
  startSec: number
  endSec: number
  eventId: string
}

export interface Reboot {
  node: string
  session: string
  tsSec: number
  time24: string
  label: string
  eventId: string
}

export interface Gap {
  node: string
  startSec: number
  endSec: number
}

export interface Dataset {
  events: LogEvent[]
  byId: Map<string, LogEvent>
  indexById: Map<string, number>
  translations: Translations
  report: ImportReport
  incidents: Incident[] | null
  incidentsByEvent: Map<string, Incident[]>
  nodes: string[]
  families: string[]
  categories: string[]
  startSec: number
  endSec: number
  phases: Phase[]
  reboots: Reboot[]
  rebootIds: Set<string>
  gaps: Gap[]
  route: { origin: string; destination: string; eventId: string } | null
}

const MIN_GAP_SEC = 420

export function compareEvents(a: LogEvent, b: LogEvent): number {
  return a.tsSec - b.tsSec || a.seq - b.seq || a.node.localeCompare(b.node)
}

const isBootName = (name: string) => /start|boot/i.test(name)

function median(values: number[]): number {
  if (!values.length) return 0
  const sorted = [...values].sort((a, b) => a - b)
  return sorted[Math.floor(sorted.length / 2)]
}

export function deriveDataset(raw: RawDataset): Dataset {
  const events = [...raw.events].sort(compareEvents)
  const byId = new Map(events.map((e) => [e.id, e]))
  const indexById = new Map(events.map((e, i) => [e.id, i]))

  const nodes = [...new Set(events.map((e) => e.node))].sort()
  const families = sortFamilies([...new Set(events.map((e) => e.family))])
  const categories = [...new Set(events.map((e) => e.category))].sort()

  const startSec = events[0]?.tsSec ?? 0
  const endSec = events.at(-1)?.tsSec ?? startSec

  const phaseEvents = events.filter((e) => typeof e.fields.phase === 'string')
  const phases: Phase[] = phaseEvents
    .map((e, i) => ({
      name: String(e.fields.phase),
      startSec: e.tsSec,
      endSec: phaseEvents[i + 1]?.tsSec ?? endSec,
      eventId: e.id,
    }))
    .filter((p) => p.endSec > p.startSec)

  const reboots: Reboot[] = []
  const lastSessionByNode = new Map<string, string>()
  const lastTsByNode = new Map<string, number>()
  const intervalsByNode = new Map<string, { from: number; to: number }[]>()

  for (const e of events) {
    const prevSession = lastSessionByNode.get(e.node)
    if (prevSession !== undefined && prevSession !== e.session) {
      reboots.push({
        node: e.node,
        session: e.session,
        tsSec: e.tsSec,
        time24: e.time24,
        label: isBootName(e.name) ? e.name : 'New session',
        eventId: e.id,
      })
    }
    lastSessionByNode.set(e.node, e.session)

    const prevTs = lastTsByNode.get(e.node)
    if (prevTs !== undefined) {
      const list = intervalsByNode.get(e.node) ?? []
      list.push({ from: prevTs, to: e.tsSec })
      intervalsByNode.set(e.node, list)
    }
    lastTsByNode.set(e.node, e.tsSec)
  }

  const gaps: Gap[] = []
  for (const [node, intervals] of intervalsByNode) {
    const threshold = Math.max(MIN_GAP_SEC, 2.5 * median(intervals.map((i) => i.to - i.from)))
    for (const i of intervals) {
      if (i.to - i.from > threshold) gaps.push({ node, startSec: i.from, endSec: i.to })
    }
  }
  gaps.sort((a, b) => a.startSec - b.startSec)

  const incidentsByEvent = new Map<string, Incident[]>()
  for (const inc of raw.incidents ?? []) {
    for (const id of inc.eventIds) {
      const list = incidentsByEvent.get(id) ?? []
      list.push(inc)
      incidentsByEvent.set(id, list)
    }
  }

  const routeEvent = events.find(
    (e) => typeof e.fields.origin === 'string' && typeof e.fields.destination === 'string',
  )

  return {
    events,
    byId,
    indexById,
    translations: raw.translations,
    report: raw.report,
    incidents: raw.incidents,
    incidentsByEvent,
    nodes,
    families,
    categories,
    startSec,
    endSec,
    phases,
    reboots,
    rebootIds: new Set(reboots.map((r) => r.eventId)),
    gaps,
    route: routeEvent
      ? {
          origin: String(routeEvent.fields.origin),
          destination: String(routeEvent.fields.destination),
          eventId: routeEvent.id,
        }
      : null,
  }
}

export function phaseAt(ds: Dataset, sec: number): Phase | null {
  for (let i = ds.phases.length - 1; i >= 0; i--) {
    if (ds.phases[i].startSec <= sec) return ds.phases[i]
  }
  return null
}

export interface NodeState {
  node: string
  mode: string | null
  oppositeFmsOk: boolean | null
  session: string | null
  lastEvent: LogEvent | null
  stateEvent: LogEvent | null
  bootEvent: LogEvent | null
}

export function nodeStateAt(ds: Dataset, node: string, sec: number): NodeState {
  let lastEvent: LogEvent | null = null
  let stateEvent: LogEvent | null = null
  let bootEvent: LogEvent | null = null
  let oppEvent: LogEvent | null = null
  for (const e of ds.events) {
    if (e.tsSec > sec) break
    if (e.node !== node) continue
    lastEvent = e
    if (typeof e.fields.mode === 'string') stateEvent = e
    if (typeof e.fields.oppositeFmsOk === 'boolean') oppEvent = e
    if (e.category === 'boot' || ds.rebootIds.has(e.id) || (isBootName(e.name) && e.family !== 'Fault'))
      bootEvent = e
  }
  return {
    node,
    mode: stateEvent ? String(stateEvent.fields.mode) : null,
    oppositeFmsOk: oppEvent ? Boolean(oppEvent.fields.oppositeFmsOk) : null,
    session: lastEvent?.session ?? null,
    lastEvent,
    stateEvent,
    bootEvent,
  }
}

export function eventsNear(
  ds: Dataset,
  sec: number,
  windowSec: number,
  predicate: (e: LogEvent) => boolean,
): LogEvent[] {
  return ds.events.filter((e) => Math.abs(e.tsSec - sec) <= windowSec && predicate(e))
}

export function translationFor(ds: Dataset, id: string): string | null {
  const t = ds.translations[id]
  return t && t.trim() ? t : null
}
