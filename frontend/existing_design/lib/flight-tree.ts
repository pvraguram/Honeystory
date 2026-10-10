/**
 * FlightStory AI — Tree Data Structure & Indexing Engine.
 * 
 * Implements:
 * 1. N-ary Hierarchical Tree for Flight / Node / Family / Event navigation
 * 2. O(log N) Binary Search for time-window and correlation queries
 * 3. O(1) Hash Map index for instant citation / event lookup
 */

import type { LogEvent, RawDataset, Incident, Claim } from '@/data/schemas'

export interface EventRecordNode {
  id: string
  number: number
  node: string
  family: string
  familyKey: 'fam1' | 'fam2' | 'fam3' | 'fam4' | 'fam5' | string
  familyDisplayName: string
  timestampRaw: string
  timestampNormalized: string
  time24: string
  tsSec: number
  eventName: string
  eventCode: string
  category: string
  fields: Record<string, any>
  flags: string[]
  rawHtml: string
  translation: string | null
  searchTokens: string
  // Teammate's Dedicated Avionics Columns:
  pilotInput: string
  navData: string
  phase: string
  altitude: string
  coords: string
  machineCode: string
  domain: string
}

export interface FamilyTreeNode {
  id: string
  key: string
  label: string
  description: string
  recordCount: number
  records: EventRecordNode[]
}

export interface AvionicsNodeTreeNode {
  id: string // "Node A", "Node B", "Node C"
  rawNodeKey: string // "NODE_A", "FMS1"
  description: string
  status: 'nominal' | 'degraded' | 'rebooted'
  recordCount: number
  families: Map<string, FamilyTreeNode>
}

export interface StoryIncidentNode {
  id: string
  title: string
  severity: string
  startSec: number
  endSec: number
  timeRangeFormatted: string
  eventIds: string[]
  impact: string | null
  recoveryEventId: string | null
  recoveryDurationSec: number | null
  inferences: Claim[]
  hypotheses: Claim[]
}

export interface AircraftTreeNode {
  id: string // "AA100"
  description: string
  tailNumber: string
  route: string
  durationFormatted: string
  startSec: number
  endSec: number
  totalRecords: number
  nodes: Map<string, AvionicsNodeTreeNode>
  allRecordsSorted: EventRecordNode[]
  recordMapById: Map<string, EventRecordNode>
  storyIncidents: StoryIncidentNode[]
}

export const FAMILIES_CANONICAL = [
  { key: 'fam1', id: 'STATE', label: 'Fam 1 : Aircraft State Buffer', desc: 'Flight telemetry, altitude, autopilot modes' },
  { key: 'fam2', id: 'Fault', label: 'Fam 2 : Fault Repository', desc: 'Hardware & software BITE fault registers' },
  { key: 'fam3', id: 'CI_BPQ', label: 'Fam 3 : FM CI BPQ', desc: 'Cross-talk bus queues & sync packets' },
  { key: 'fam4', id: 'LBPQ', label: 'Fam 4 : FM LBPQ', desc: 'Lateral flight plan & waypoint queues' },
  { key: 'fam5', id: 'State_Transition', label: 'Fam 5 : State Transition Buffer', desc: 'Dual/Single mode transitions & handoffs' },
] as const

/**
 * Maps raw family/filename identifiers to canonical 1-to-5 family keys.
 */
export function mapToCanonicalFamily(rawFamily: string): { key: string; label: string; desc: string } {
  const norm = rawFamily.toUpperCase()
  if (norm.includes('TRANSITION') || norm === 'SYS') {
    return { key: 'fam5', label: FAMILIES_CANONICAL[4].label, desc: FAMILIES_CANONICAL[4].desc }
  }
  if (norm.includes('AIRCRAFT_STATE') || norm === 'STATE') {
    return { key: 'fam1', label: FAMILIES_CANONICAL[0].label, desc: FAMILIES_CANONICAL[0].desc }
  }
  if (norm.includes('FAULT')) {
    return { key: 'fam2', label: FAMILIES_CANONICAL[1].label, desc: FAMILIES_CANONICAL[1].desc }
  }
  if (norm.includes('CI_BPQ') || norm === 'CI') {
    return { key: 'fam3', label: FAMILIES_CANONICAL[2].label, desc: FAMILIES_CANONICAL[2].desc }
  }
  if (norm.includes('LBPQ')) {
    return { key: 'fam4', label: FAMILIES_CANONICAL[3].label, desc: FAMILIES_CANONICAL[3].desc }
  }
  return { key: 'fam1', label: rawFamily, desc: 'Decoded log buffer' }
}

/**
 * Maps node string to display name: NODE_A -> Node A, FMS1 -> Node A, etc.
 */
export function normalizeNodeDisplayName(rawNode: string): string {
  const upper = rawNode.toUpperCase()
  if (upper === 'NODE_A' || upper === 'FMS1') return 'Node A'
  if (upper === 'NODE_B' || upper === 'FMS2') return 'Node B'
  if (upper === 'NODE_C' || upper === 'FMS3') return 'Node C'
  return rawNode
}

/**
 * Builds the complete N-ary Tree from loaded dataset.
 */
export function buildFlightTree(
  raw: RawDataset,
  aircraftId = 'AA100',
  description = 'Transcontinental Cruise & Approach (SFO → JFK)',
  route = 'KSFO → KJFK'
): AircraftTreeNode {
  const sortedRaw = [...raw.events].sort((a, b) => a.tsSec - b.tsSec || a.seq - b.seq)
  const recordMapById = new Map<string, EventRecordNode>()
  const nodesMap = new Map<string, AvionicsNodeTreeNode>()

  // Initialize canonical nodes
  const defaultNodes = ['Node A', 'Node B', 'Node C']
  defaultNodes.forEach((nodeName) => {
    const families = new Map<string, FamilyTreeNode>()
    FAMILIES_CANONICAL.forEach((f) => {
      families.set(f.key, {
        id: f.id,
        key: f.key,
        label: f.label,
        description: f.desc,
        recordCount: 0,
        records: [],
      })
    })

    nodesMap.set(nodeName, {
      id: nodeName,
      rawNodeKey: nodeName.replace(' ', '_').toUpperCase(),
      description: `${nodeName} — Redundant Flight Management System`,
      status: 'nominal',
      recordCount: 0,
      families,
    })
  })

  // Populate records into tree
  const allRecordsSorted: EventRecordNode[] = []

  sortedRaw.forEach((evt, idx) => {
    const nodeDisplayName = normalizeNodeDisplayName(evt.node)
    const famInfo = mapToCanonicalFamily(evt.family)

    if (!nodesMap.has(nodeDisplayName)) {
      const families = new Map<string, FamilyTreeNode>()
      FAMILIES_CANONICAL.forEach((f) => {
        families.set(f.key, {
          id: f.id,
          key: f.key,
          label: f.label,
          description: f.desc,
          recordCount: 0,
          records: [],
        })
      })
      nodesMap.set(nodeDisplayName, {
        id: nodeDisplayName,
        rawNodeKey: evt.node,
        description: `${nodeDisplayName} Subsystem`,
        status: 'nominal',
        recordCount: 0,
        families,
      })
    }

    const avionicsNode = nodesMap.get(nodeDisplayName)!
    const famNode = avionicsNode.families.get(famInfo.key) || avionicsNode.families.get('fam1')!

    const recordNode: EventRecordNode = {
      id: evt.id,
      number: idx + 1,
      node: nodeDisplayName,
      family: evt.family,
      familyKey: famInfo.key,
      familyDisplayName: famInfo.label,
      timestampRaw: evt.time24,
      timestampNormalized: evt.time24,
      time24: evt.time24,
      tsSec: evt.tsSec,
      eventName: evt.name,
      eventCode: evt.code || '',
      category: evt.category,
      fields: evt.fields,
      flags: evt.flags,
      rawHtml: evt.rawHtml,
      translation: raw.translations[evt.id] || null,
      pilotInput: (evt as any).pilotInput || '-',
      navData: (evt as any).navData || '-',
      phase: (evt as any).phase || 'Pre-Flight Gate',
      altitude: (evt as any).altitude || '0 ft (Ground)',
      coords: (evt as any).coords || '-',
      machineCode: (evt as any).machineCode || (evt.family === 'Fault' ? `BITE ${evt.code}` : 'Nominal'),
      domain: (evt as any).domain || (evt.family === 'Fault' ? 'SYSTEM_ERROR' : 'TELEMETRY'),
      searchTokens: `${idx + 1} ${evt.name} ${evt.code || ''} ${evt.time24} ${nodeDisplayName} ${evt.family} ${(evt as any).pilotInput || ''} ${(evt as any).navData || ''} ${(evt as any).phase || ''} ${(evt as any).coords || ''} ${(evt as any).machineCode || ''} ${raw.translations[evt.id] || ''} ${Object.entries(evt.fields || {}).map(([k, v]) => `${k} ${v}`).join(' ')}`.toLowerCase(),
    }

    famNode.records.push(recordNode)
    famNode.recordCount++
    avionicsNode.recordCount++

    if (evt.family === 'Fault' || (evt.flags && evt.flags.length > 0)) {
      if (avionicsNode.status === 'nominal') avionicsNode.status = 'degraded'
    }

    recordMapById.set(recordNode.id, recordNode)
    allRecordsSorted.push(recordNode)
  })

  // Build story incidents
  const storyIncidents: StoryIncidentNode[] = (raw.incidents || []).map((inc) => {
    const startM = Math.floor(inc.startSec / 60)
    const startS = Math.floor(inc.startSec % 60)
    const endM = Math.floor(inc.endSec / 60)
    const endS = Math.floor(inc.endSec % 60)
    const formatTime = (m: number, s: number) =>
      `${String(Math.floor(m / 60) + 11).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}:${String(s).padStart(2, '0')}`

    const recEvt = inc.recoveryEventId ? recordMapById.get(inc.recoveryEventId) : null

    return {
      id: inc.id,
      title: inc.title,
      severity: inc.severity || 'major',
      startSec: inc.startSec,
      endSec: inc.endSec,
      timeRangeFormatted: `${formatTime(startM, startS)} – ${formatTime(endM, endS)}`,
      eventIds: inc.eventIds,
      impact: inc.impact || null,
      recoveryEventId: inc.recoveryEventId || null,
      recoveryDurationSec: recEvt ? Math.max(0, recEvt.tsSec - inc.startSec) : null,
      inferences: inc.inference || [],
      hypotheses: inc.hypothesis || [],
    }
  })

  const startSec = allRecordsSorted[0]?.tsSec || 0
  const endSec = allRecordsSorted[allRecordsSorted.length - 1]?.tsSec || startSec
  const totalSec = Math.max(1, endSec - startSec)
  const durationHours = Math.floor(totalSec / 3600)
  const durationMins = Math.floor((totalSec % 3600) / 60)

  return {
    id: aircraftId,
    description,
    tailNumber: 'N842AA',
    route,
    durationFormatted: `${durationHours > 0 ? `${durationHours}h ` : ''}${durationMins}m flight time`,
    startSec,
    endSec,
    totalRecords: allRecordsSorted.length,
    nodes: nodesMap,
    allRecordsSorted,
    recordMapById,
    storyIncidents,
  }
}

/**
 * Creates an empty isolated flight tree for a new or uningested flight.
 */
export function createEmptyFlightTree(
  aircraftId: string,
  description: string,
  route: string
): AircraftTreeNode {
  const nodesMap = new Map<string, AvionicsNodeTreeNode>()
  const defaultNodes = ['Node A', 'Node B', 'Node C']
  defaultNodes.forEach((nodeName) => {
    const families = new Map<string, FamilyTreeNode>()
    FAMILIES_CANONICAL.forEach((f) => {
      families.set(f.key, {
        id: f.id,
        key: f.key,
        label: f.label,
        description: f.desc,
        recordCount: 0,
        records: [],
      })
    })

    nodesMap.set(nodeName, {
      id: nodeName,
      rawNodeKey: nodeName.replace(' ', '_').toUpperCase(),
      description: `${nodeName} — Redundant Flight Management System`,
      status: 'nominal',
      recordCount: 0,
      families,
    })
  })

  return {
    id: aircraftId,
    description,
    tailNumber: aircraftId === 'AA101' ? 'G-XWBA' : 'JA882A',
    route,
    durationFormatted: 'No flight time recorded',
    startSec: 0,
    endSec: 0,
    totalRecords: 0,
    nodes: nodesMap,
    allRecordsSorted: [],
    recordMapById: new Map(),
    storyIncidents: [],
  }
}

/**
 * Binary search range query over sorted timestamp events: O(log N).
 */
export function queryEventsInTimeRange(
  records: EventRecordNode[],
  startSec: number,
  endSec: number
): EventRecordNode[] {
  if (!records.length) return []

  let low = 0
  let high = records.length - 1
  let firstIdx = -1

  while (low <= high) {
    const mid = (low + high) >> 1
    if (records[mid].tsSec >= startSec) {
      firstIdx = mid
      high = mid - 1
    } else {
      low = mid + 1
    }
  }

  if (firstIdx === -1) return []

  const results: EventRecordNode[] = []
  for (let i = firstIdx; i < records.length && records[i].tsSec <= endSec; i++) {
    results.push(records[i])
  }
  return results
}

/**
 * Correlates multiple nodes side-by-side into synchronized time buckets.
 */
export interface CorrelatedTimeBucket {
  bucketIndex: number
  time24: string
  startSec: number
  endSec: number
  hasAnomaly: boolean
  eventsByNode: Record<string, EventRecordNode[]>
}

export function buildCorrelationMatrix(
  tree: AircraftTreeNode,
  bucketWindowSec = 2.0
): CorrelatedTimeBucket[] {
  const records = tree.allRecordsSorted
  if (!records.length) return []

  const startSec = tree.startSec
  const endSec = tree.endSec
  const totalSpan = Math.max(1, endSec - startSec)
  const bucketCount = Math.min(500, Math.ceil(totalSpan / bucketWindowSec))
  const buckets: CorrelatedTimeBucket[] = []

  // Pre-allocate buckets with events
  const nodeNames = Array.from(tree.nodes.keys())

  for (let b = 0; b < bucketCount; b++) {
    const bStart = startSec + b * bucketWindowSec
    const bEnd = bStart + bucketWindowSec

    const eventsInBucket = queryEventsInTimeRange(records, bStart, bEnd)
    if (!eventsInBucket.length) continue

    const eventsByNode: Record<string, EventRecordNode[]> = {}
    nodeNames.forEach((n) => {
      eventsByNode[n] = []
    })

    let hasAnomaly = false
    eventsInBucket.forEach((e) => {
      if (!eventsByNode[e.node]) eventsByNode[e.node] = []
      eventsByNode[e.node].push(e)
      if (e.family === 'Fault' || (e.flags && e.flags.length > 0)) {
        hasAnomaly = true
      }
    })

    buckets.push({
      bucketIndex: b,
      time24: eventsInBucket[0].time24,
      startSec: bStart,
      endSec: bEnd,
      hasAnomaly,
      eventsByNode,
    })
  }

  return buckets
}
