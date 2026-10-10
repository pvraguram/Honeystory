// Generates fictional, public-safe mock inputs that follow the agreed schema.
// Replace the files in data/mock/ with the real ingestion/translator outputs when they arrive.
import { writeFileSync, mkdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const outDir = join(dirname(fileURLToPath(import.meta.url)), '..', 'data', 'mock')
mkdirSync(outDir, { recursive: true })

let seed = 7
const rand = () => {
  seed = (seed * 16807) % 2147483647
  return (seed - 1) / 2147483646
}

const BASE = 11 * 3600 + 40 * 60 // 11:40:00
const pad = (n) => String(n).padStart(2, '0')
const time24 = (t) => {
  const s = Math.floor(t)
  return `${pad(Math.floor(s / 3600))}:${pad(Math.floor((s % 3600) / 60))}:${pad(s % 60)}`
}

const events = []
const translations = {}
const seqByNode = { FMS1: 1000, FMS2: 2000, FMS3: 3000 }
const sessionByNode = { FMS1: 1, FMS2: 1, FMS3: 1 }

const familyTag = { Fault: 'flt', CI_BPQ: 'ci', LBPQ: 'lb', STATE: 'st', SYS: 'sys' }

function add({ t, node, family, category, name, code = null, fields = {}, flags = [], parseNotes = [], tr }) {
  seqByNode[node] += 1
  const id = `${node}-${sessionByNode[node]}-${seqByNode[node]}`
  const ms = Math.floor((t % 1) * 1000)
  const fieldText = Object.entries(fields)
    .map(([k, v]) => `${k}=${v === null ? 'N/A' : v}`)
    .join(' ')
  const rawHtml = `<tr class="${familyTag[family]}"><td>${time24(t)}.${String(ms).padStart(3, '0')}</td><td>${node}</td><td>${code ?? ''}</td><td>${name}</td><td>${fieldText}</td></tr>`
  events.push({
    id,
    family,
    node,
    session: sessionByNode[node],
    seq: seqByNode[node],
    time24: time24(t),
    tsSec: Math.round(t * 1000) / 1000,
    category,
    name,
    code,
    fields,
    flags,
    rawHtml,
    parseNotes,
  })
  if (tr) translations[id] = tr
  return id
}

const NODES = ['FMS1', 'FMS2', 'FMS3']
const roles = { FMS1: 'master', FMS2: 'co-master', FMS3: 'standby' }

// Session 1 boot for all nodes
NODES.forEach((node, i) => {
  add({
    t: BASE + i * 0.4,
    node,
    family: 'SYS',
    category: 'boot',
    name: 'Cold start',
    code: 'SYS-001',
    fields: { bootType: 'cold', swVersion: 'FMS 7.4.2', role: roles[node] },
    tr: `${node} powered up from cold and loaded software 7.4.2 as ${roles[node]}.`,
  })
})

const ids = {}
ids.phasePre = add({
  t: BASE + 3,
  node: 'FMS1',
  family: 'STATE',
  category: 'state',
  name: 'Flight phase change',
  code: 'ST-PH',
  fields: { from: 'POWER_ON', phase: 'PREFLIGHT' },
  tr: 'The flight phase became Preflight.',
})
add({
  t: BASE + 4,
  node: 'FMS1',
  family: 'STATE',
  category: 'state',
  name: 'Sync mode',
  code: 'ST-SYNC',
  fields: { mode: 'Dual', oppositeFmsOk: true, peer: 'FMS2' },
  tr: 'FMS1 and FMS2 are running in Dual mode and each sees the other as healthy.',
})
add({
  t: BASE + 4.2,
  node: 'FMS2',
  family: 'STATE',
  category: 'state',
  name: 'Sync mode',
  code: 'ST-SYNC',
  fields: { mode: 'Dual', oppositeFmsOk: true, peer: 'FMS1' },
  tr: 'FMS2 confirms Dual mode with FMS1.',
})
add({
  t: BASE + 4.5,
  node: 'FMS3',
  family: 'STATE',
  category: 'state',
  name: 'Sync mode',
  code: 'ST-SYNC',
  fields: { mode: 'Standby', oppositeFmsOk: true, peer: 'FMS1' },
  tr: 'FMS3 is on standby and listening to FMS1.',
})

ids.routeEntry = add({
  t: BASE + 62,
  node: 'FMS1',
  family: 'CI_BPQ',
  category: 'operator',
  name: 'Route entry',
  code: 'CI-RTE',
  fields: { origin: 'EDDF', destination: 'EDDL', flightNo: 'DEMO123' },
  tr: 'The operator entered the route Frankfurt (EDDF) to Düsseldorf (EDDL).',
})
add({
  t: BASE + 64,
  node: 'FMS2',
  family: 'CI_BPQ',
  category: 'planning',
  name: 'Route crossload',
  code: 'CI-XLD',
  fields: { from: 'FMS1', legs: 14 },
  tr: 'FMS2 received a copy of the 14-leg route from FMS1.',
})
add({
  t: BASE + 95,
  node: 'FMS1',
  family: 'CI_BPQ',
  category: 'operator',
  name: 'Perf init',
  code: 'CI-PRF',
  fields: { zfw: 61.2, costIndex: 30, crzFl: 240 },
  tr: 'The operator entered performance data: cost index 30, cruise level FL240.',
})
add({
  t: BASE + 140,
  node: 'FMS1',
  family: 'LBPQ',
  category: 'planning',
  name: 'Flight plan activated',
  code: 'LB-ACT',
  fields: { legs: 14, sid: 'TOBAK7F' },
  tr: 'The flight plan was activated with departure procedure TOBAK7F.',
})

ids.phaseTo = add({
  t: BASE + 240,
  node: 'FMS1',
  family: 'STATE',
  category: 'state',
  name: 'Flight phase change',
  code: 'ST-PH',
  fields: { from: 'PREFLIGHT', phase: 'TAKEOFF' },
  tr: 'The flight phase became Takeoff.',
})
add({
  t: BASE + 360,
  node: 'FMS1',
  family: 'STATE',
  category: 'state',
  name: 'Flight phase change',
  code: 'ST-PH',
  fields: { from: 'TAKEOFF', phase: 'CLIMB' },
  tr: 'The flight phase became Climb.',
})

// Incident 1: FMS2 watchdog reset and reboot (~11:47)
const t1 = BASE + 430
ids.wd = add({
  t: t1,
  node: 'FMS2',
  family: 'Fault',
  category: 'fault',
  name: 'Watchdog reset',
  code: 'F-1107',
  fields: { task: 'NAV_DB', lastHeartbeatMs: 2400 },
  tr: 'FMS2 stopped answering its internal watchdog and was forced to reset.',
})
ids.single1 = add({
  t: t1 + 0.6,
  node: 'FMS1',
  family: 'STATE',
  category: 'state',
  name: 'Sync mode',
  code: 'ST-SYNC',
  fields: { mode: 'Single', oppositeFmsOk: false, peer: 'FMS2' },
  tr: 'FMS1 lost contact with FMS2 and switched to Single mode.',
})
add({
  t: t1 + 1.2,
  node: 'FMS3',
  family: 'STATE',
  category: 'state',
  name: 'Opposite FMS status',
  code: 'ST-OPP',
  fields: { watching: 'FMS2', oppositeFmsOk: false },
  tr: 'FMS3 noticed FMS2 is no longer healthy.',
})
add({
  t: t1 + 8,
  node: 'FMS1',
  family: 'CI_BPQ',
  category: 'operator',
  name: 'Message acknowledged',
  code: 'CI-ACK',
  fields: { message: 'FMS2 INOP' },
  tr: 'The operator acknowledged the "FMS2 INOP" message.',
})
sessionByNode.FMS2 = 2
ids.boot2 = add({
  t: t1 + 30,
  node: 'FMS2',
  family: 'SYS',
  category: 'boot',
  name: 'Cold start',
  code: 'SYS-001',
  fields: { bootType: 'cold', swVersion: 'FMS 7.4.2', role: 'co-master', reason: 'watchdog' },
  tr: 'FMS2 restarted from cold after the watchdog reset.',
})
add({
  t: t1 + 52,
  node: 'FMS2',
  family: 'CI_BPQ',
  category: 'planning',
  name: 'Route crossload',
  code: 'CI-XLD',
  fields: { from: 'FMS1', legs: 14 },
  tr: 'FMS2 reloaded the 14-leg route from FMS1.',
})
ids.dual1 = add({
  t: t1 + 80,
  node: 'FMS1',
  family: 'STATE',
  category: 'recovery',
  name: 'Sync mode',
  code: 'ST-SYNC',
  fields: { mode: 'Dual', oppositeFmsOk: true, peer: 'FMS2' },
  tr: 'FMS1 and FMS2 are back in Dual mode.',
})
add({
  t: t1 + 80.3,
  node: 'FMS2',
  family: 'STATE',
  category: 'recovery',
  name: 'Sync mode',
  code: 'ST-SYNC',
  fields: { mode: 'Dual', oppositeFmsOk: true, peer: 'FMS1' },
  tr: 'FMS2 confirms Dual mode with FMS1 again.',
})

// Incident 2: Dual State Trans Timeout (~11:50)
const t2 = BASE + 620
ids.dstt = add({
  t: t2,
  node: 'FMS1',
  family: 'Fault',
  category: 'fault',
  name: 'Dual State Trans Timeout',
  code: 'F-2041',
  fields: { peer: 'FMS2', timeoutMs: 5000, pendingState: 'DUAL_SYNC' },
  tr: 'FMS1 waited 5 seconds for FMS2 to confirm a shared state change and gave up.',
})
for (let i = 0; i < 22; i++) {
  add({
    t: t2 + 1 + i * 0.045,
    node: 'FMS2',
    family: 'CI_BPQ',
    category: 'state',
    name: 'Sync message retry',
    code: 'CI-SYR',
    fields: { attempt: i + 1, target: 'FMS1' },
    tr: `FMS2 resent a sync message to FMS1 (attempt ${i + 1}).`,
  })
}
ids.single2 = add({
  t: t2 + 2.5,
  node: 'FMS1',
  family: 'STATE',
  category: 'state',
  name: 'Sync mode',
  code: 'ST-SYNC',
  fields: { mode: 'Single', oppositeFmsOk: true, peer: 'FMS2' },
  tr: 'FMS1 dropped to Single mode while still seeing FMS2 as alive.',
})
add({
  t: t2 + 2.5,
  node: 'FMS2',
  family: 'STATE',
  category: 'state',
  name: 'Sync mode',
  code: 'ST-SYNC',
  fields: { mode: 'Single', oppositeFmsOk: true, peer: 'FMS1' },
  tr: 'FMS2 also dropped to Single mode.',
})
ids.dsttOp = add({
  t: t2 + 14,
  node: 'FMS1',
  family: 'CI_BPQ',
  category: 'operator',
  name: 'Resync requested',
  code: 'CI-RSY',
  fields: { target: 'FMS2' },
  tr: 'The operator asked FMS1 to resynchronise with FMS2.',
})
ids.dual2 = add({
  t: t2 + 28,
  node: 'FMS1',
  family: 'STATE',
  category: 'recovery',
  name: 'Sync mode',
  code: 'ST-SYNC',
  fields: { mode: 'Dual', oppositeFmsOk: true, peer: 'FMS2' },
  tr: 'Dual mode was restored between FMS1 and FMS2.',
})

// Cruise and periodic guidance
add({
  t: BASE + 900,
  node: 'FMS1',
  family: 'STATE',
  category: 'state',
  name: 'Flight phase change',
  code: 'ST-PH',
  fields: { from: 'CLIMB', phase: 'CRUISE' },
  tr: 'The flight phase became Cruise.',
})

const waypoints = ['TOBAK', 'RID', 'NOR', 'BOMBI', 'KUMIK', 'ERSIL', 'LMA', 'DOMUX', 'PODIP', 'DL450', 'RONAD', 'DUS']
let wp = 0
for (let t = BASE + 180; t < BASE + 3300; t += 150 + Math.floor(rand() * 80)) {
  const node = NODES[Math.floor(rand() * 2)] // FMS1/FMS2 drive guidance
  const xte = Math.round((rand() - 0.5) * 40) / 100
  const isGap = t > BASE + 1500 && t < BASE + 1920
  if (isGap) continue
  const flagged = wp === 5
  const naFlag = wp === 8
  if (wp < waypoints.length - 1) {
    add({
      t,
      node,
      family: 'LBPQ',
      category: 'guidance',
      name: 'Leg sequenced',
      code: 'LB-SEQ',
      fields: {
        from: waypoints[wp],
        to: waypoints[wp + 1],
        crossTrackNm: naFlag ? null : xte,
        fuelKg: flagged ? -999 : 6200 - wp * 180,
      },
      flags: [...(flagged ? ['invalid:fuelKg'] : []), ...(naFlag ? ['na:crossTrackNm'] : [])],
      parseNotes: flagged ? ['fuelKg below physical minimum; kept raw value'] : [],
      tr: wp === 3 ? undefined : `Guidance moved on from ${waypoints[wp]} to the next waypoint ${waypoints[wp + 1]}.`,
    })
    wp++
  }
  if (rand() > 0.55) {
    add({
      t: t + 20,
      node,
      family: 'LBPQ',
      category: 'guidance',
      name: 'VNAV mode',
      code: 'LB-VNV',
      fields: { mode: rand() > 0.5 ? 'VNAV PTH' : 'VNAV SPD' },
      tr: 'Vertical guidance mode was updated.',
    })
  }
}

// Standby heartbeats (FMS3) with a data gap 12:05-12:12
for (let t = BASE + 120; t < BASE + 3300; t += 240) {
  if (t > BASE + 1500 && t < BASE + 1920) continue
  add({
    t: t + 7,
    node: 'FMS3',
    family: 'STATE',
    category: 'state',
    name: 'Standby heartbeat',
    code: 'ST-HB',
    fields: { listeningTo: 'FMS1', lagMs: Math.floor(rand() * 40) + 5 },
    tr: 'FMS3 (standby) is still listening and in sync.',
  })
}

add({
  t: BASE + 2100,
  node: 'FMS1',
  family: 'STATE',
  category: 'state',
  name: 'Flight phase change',
  code: 'ST-PH',
  fields: { from: 'CRUISE', phase: 'DESCENT' },
  tr: 'The flight phase became Descent.',
})
add({
  t: BASE + 2140,
  node: 'FMS1',
  family: 'CI_BPQ',
  category: 'operator',
  name: 'Approach selected',
  code: 'CI-APP',
  fields: { approach: 'ILS 23R', star: 'DOMUX1G' },
  tr: 'The operator selected the ILS 23R approach.',
})
ids.minor = add({
  t: BASE + 2290,
  node: 'FMS2',
  family: 'Fault',
  category: 'fault',
  name: 'Nav DB checksum warning',
  code: 'F-0311',
  fields: { cycle: '2610', blocks: 'N/A' },
  flags: ['na:blocks'],
  parseNotes: ['blocks reported as N/A in source'],
})
add({
  t: BASE + 2700,
  node: 'FMS1',
  family: 'STATE',
  category: 'state',
  name: 'Flight phase change',
  code: 'ST-PH',
  fields: { from: 'DESCENT', phase: 'APPROACH' },
  tr: 'The flight phase became Approach.',
})
add({
  t: BASE + 3180,
  node: 'FMS1',
  family: 'STATE',
  category: 'state',
  name: 'Flight phase change',
  code: 'ST-PH',
  fields: { from: 'APPROACH', phase: 'LANDING' },
  tr: 'The flight phase became Landing.',
})
add({
  t: BASE + 3330,
  node: 'FMS1',
  family: 'STATE',
  category: 'state',
  name: 'Flight phase change',
  code: 'ST-PH',
  fields: { from: 'LANDING', phase: 'DONE' },
  tr: 'The flight is complete.',
})

events.sort((a, b) => a.tsSec - b.tsSec || a.seq - b.seq)

// Import report
const families = ['Fault', 'CI_BPQ', 'LBPQ', 'STATE', 'SYS']
const skipped = [
  { family: 'LBPQ', node: 'FMS1', line: 1182, reason: 'Unterminated <tr> element', raw: '<tr class="lb"><td>11:58:02.114</td><td>FMS1' },
  { family: 'LBPQ', node: 'FMS2', line: 1460, reason: 'Timestamp missing', raw: '<tr class="lb"><td></td><td>FMS2</td><td>LB-SEQ</td>' },
  { family: 'CI_BPQ', node: 'FMS2', line: 377, reason: 'Duplicate of seq 2031 (identical payload)', raw: '<tr class="ci"><td>11:50:21.090</td><td>FMS2</td><td>CI-SYR</td>…' },
  { family: 'STATE', node: 'FMS3', line: 812, reason: 'Unknown state code ST-??', raw: '<tr class="st"><td>12:05:11.000</td><td>FMS3</td><td>ST-??</td>' },
  { family: 'Fault', node: 'FMS2', line: 64, reason: 'Fault code not in dictionary', raw: '<tr class="flt"><td>11:47:10.950</td><td>FMS2</td><td>F-9X</td>' },
  { family: 'STATE', node: 'FMS3', line: 815, reason: 'Encoding error (non-UTF-8 bytes)', raw: '<tr class="st"><td>12:05:\\xff\\xfe' },
]
const byFamily = {}
for (const f of families) {
  const parsed = events.filter((e) => e.family === f).length
  const sk = skipped.filter((s) => s.family === f).length
  byFamily[f] = { rowsIn: parsed + sk, parsed, skipped: sk }
}
const report = {
  generatedAt: '2026-10-09T09:00:00Z',
  source: 'MOCK – fictional sample generated by scripts/generate-mock.mjs',
  totals: { rowsIn: events.length + skipped.length, events: events.length, skipped: skipped.length },
  byFamily,
  skipped,
}

const incidents = {
  incidents: [
    {
      id: 'INC-1',
      title: 'FMS2 watchdog reset and cold start',
      severity: 'major',
      startSec: events.find((e) => e.id === ids.wd).tsSec,
      endSec: events.find((e) => e.id === ids.dual1).tsSec,
      eventIds: events.filter((e) => e.tsSec >= t1 && e.tsSec <= t1 + 81).map((e) => e.id),
      impact: 'System ran in Single mode on FMS1 for about 80 s.',
      recoveryEventId: ids.dual1,
      inference: [
        { text: 'FMS2 reset because its watchdog expired.', label: 'confirmed', citations: [ids.wd] },
        { text: 'FMS1 fell back to Single mode within one second of the reset.', label: 'confirmed', citations: [ids.wd, ids.single1] },
        { text: 'Dual mode was restored after FMS2 completed its cold start.', label: 'confirmed', citations: [ids.boot2, ids.dual1] },
      ],
      hypothesis: [
        { text: 'The NAV_DB task stalling may have triggered the watchdog.', label: 'probable', citations: [ids.wd] },
        { text: 'No log shows what the NAV_DB task was doing before the stall.', label: 'missing', citations: [] },
      ],
    },
    {
      id: 'INC-2',
      title: 'Dual State Trans Timeout between FMS1 and FMS2',
      severity: 'major',
      startSec: events.find((e) => e.id === ids.dstt).tsSec,
      endSec: events.find((e) => e.id === ids.dual2).tsSec,
      eventIds: events.filter((e) => e.tsSec >= t2 && e.tsSec <= t2 + 29).map((e) => e.id),
      impact: 'Both units ran in Single mode for about 26 s; 22 sync retries in 1 s.',
      recoveryEventId: ids.dual2,
      inference: [
        { text: 'FMS1 timed out waiting 5000 ms for FMS2 to confirm a state change.', label: 'confirmed', citations: [ids.dstt] },
        { text: 'FMS2 kept retrying the sync message, suggesting the link was up but replies were lost.', label: 'probable', citations: [ids.dstt, ids.single2] },
        { text: 'An operator resync preceded recovery to Dual mode.', label: 'confirmed', citations: [ids.dsttOp, ids.dual2] },
      ],
      hypothesis: [
        { text: 'FMS2 may not have fully settled after its earlier cold start at 11:47.', label: 'probable', citations: [ids.boot2, ids.dstt] },
        { text: 'There is no bus-level log to confirm whether replies were dropped.', label: 'missing', citations: [] },
      ],
    },
    {
      id: 'INC-3',
      title: 'FMS3 log gap during cruise',
      severity: 'minor',
      startSec: BASE + 1500,
      endSec: BASE + 1920,
      eventIds: [],
      impact: 'About 7 minutes without standby heartbeats.',
      recoveryEventId: null,
      inference: [
        { text: 'No FMS3 records exist between 12:05 and 12:12.', label: 'confirmed', citations: [] },
      ],
      hypothesis: [
        { text: 'Two FMS3 STATE rows from this window were skipped at import, so the gap may be a parsing loss rather than a silent unit.', label: 'probable', citations: [] },
        { text: 'The raw file for this window was not supplied.', label: 'missing', citations: [] },
      ],
    },
  ],
}

writeFileSync(join(outDir, 'events.json'), JSON.stringify(events, null, 2))
writeFileSync(join(outDir, 'translations.json'), JSON.stringify(translations, null, 2))
writeFileSync(join(outDir, 'import_report.json'), JSON.stringify(report, null, 2))
writeFileSync(join(outDir, 'incidents.json'), JSON.stringify(incidents, null, 2))
console.log(`events=${events.length} translations=${Object.keys(translations).length} skipped=${skipped.length}`)
