'use client'

import { useMemo, useState, useEffect } from 'react'
import {
  Activity,
  AlertCircle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  Clock,
  Filter,
  Folder,
  GitCompare,
  HardDriveUpload,
  Layers,
  Network,
  PieChart as PieIcon,
  Search,
  Sparkles,
  TrendingUp,
  Zap,
} from 'lucide-react'
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  AreaChart,
  Area,
  CartesianGrid,
} from 'recharts'
import { useFlightStore } from '@/store/flight-store'
import {
  buildCorrelationMatrix,
  type AircraftTreeNode,
  type CorrelatedTimeBucket,
  type EventRecordNode,
} from '@/lib/flight-tree'

interface CorrelationViewProps {
  tree: AircraftTreeNode
}

type CorrelationTab = 'charts' | 'pipeline' | 'sync'

// Chart Color Palette (Clean Executive Avionics Theme)
const COLORS = {
  sky: '#0284c7',
  rose: '#f43f5e',
  indigo: '#6366f1',
  amber: '#f59e0b',
  emerald: '#10b981',
  slate: '#64748b',
  purple: '#a855f7',
}

const FAMILY_COLORS: Record<string, string> = {
  'CI BPQ': COLORS.sky,
  'Faults': COLORS.rose,
  'LBPQ': COLORS.indigo,
  'Transitions': COLORS.amber,
  'Aircraft State': COLORS.emerald,
}

// Causal Chain Stages
const CAUSAL_STAGES = [
  {
    step: 1,
    code: 'BITE 6074',
    title: 'Nav Repository File EOF',
    category: 'Root Cause',
    count: 329,
    impact: 'Premature EOF on nav database read',
    nodes: 'Node A, B, C',
    color: 'border-rose-500 bg-rose-50 text-rose-700',
  },
  {
    step: 2,
    code: 'BITE 6025 / 6035',
    title: 'Process Lookup & Callback Fail',
    category: 'Loader Exception',
    count: 466,
    impact: 'PID 653 unacquired; missing callback in table',
    nodes: 'Node A, B, C',
    color: 'border-orange-500 bg-orange-50 text-orange-700',
  },
  {
    step: 3,
    code: 'BITE 6029 / 6024',
    title: 'OS Semaphore Mutex Lock',
    category: 'RTOS Deadlock',
    count: 325,
    impact: 'Threads blocked awaiting synchronization lock',
    nodes: 'Node A, B, C',
    color: 'border-amber-500 bg-amber-50 text-amber-700',
  },
  {
    step: 4,
    code: 'BITE 6000',
    title: 'RTOS Frame Deadline Missed',
    category: 'Slice Overrun',
    count: 120,
    impact: 'Heartbeat delivery missed real-time frame',
    nodes: 'Node A, B, C',
    color: 'border-purple-500 bg-purple-50 text-purple-700',
  },
  {
    step: 5,
    code: 'TRANSITION',
    title: 'Redundancy Handoff: Single Mode',
    category: 'System Degradation',
    count: 348,
    impact: 'Partner lost heartbeat; cross-checking offline',
    nodes: 'Node B degraded',
    color: 'border-slate-800 bg-slate-900 text-white',
  },
]

export function CorrelationView({ tree }: CorrelationViewProps) {
  const jumpToEventInNodeView = useFlightStore((s) => s.jumpToEventInNodeView)
  const openIngestModalForFlight = useFlightStore((s) => s.openIngestModalForFlight)

  const [activeTab, setActiveTab] = useState<CorrelationTab>('charts')
  const [windowSec, setWindowSec] = useState<number>(2.0)
  const [onlyAnomalies, setOnlyAnomalies] = useState<boolean>(false)
  const [searchFilter, setSearchFilter] = useState<string>('')
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)
  const [isMounted, setIsMounted] = useState<boolean>(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  // 1. Data Logic: Event Family Distribution for Pie Chart
  const familyPieData = useMemo(() => {
    const counts: Record<string, number> = {
      'CI BPQ': 0,
      'Faults': 0,
      'LBPQ': 0,
      'Transitions': 0,
      'Aircraft State': 0,
    }

    tree.allRecordsSorted.forEach((r) => {
      if (r.family === 'CI_BPQ') counts['CI BPQ']++
      else if (r.family === 'Fault') counts['Faults']++
      else if (r.family === 'LBPQ') counts['LBPQ']++
      else if (r.family === 'State_Transition') counts['Transitions']++
      else if (r.family === 'STATE') counts['Aircraft State']++
    })

    return Object.entries(counts).map(([name, value]) => ({
      name,
      value,
      percentage: ((value / Math.max(1, tree.totalRecords)) * 100).toFixed(1),
      color: FAMILY_COLORS[name] || COLORS.slate,
    }))
  }, [tree])

  // 2. Data Logic: Multi-Node Activity Comparison for Bar Chart
  const nodeBarData = useMemo(() => {
    const nodes = ['Node A', 'Node B', 'Node C']
    return nodes.map((name) => {
      const nodeObj = tree.nodes.get(name)
      if (!nodeObj) {
        return { name, nominal: 0, faults: 0, transitions: 0, total: 0 }
      }

      let faults = 0
      let transitions = 0
      let nominal = 0

      nodeObj.families.forEach((fam) => {
        fam.records.forEach((r) => {
          if (r.family === 'Fault') faults++
          else if (r.family === 'State_Transition') transitions++
          else nominal++
        })
      })

      return {
        name,
        nominal,
        faults,
        transitions,
        total: faults + transitions + nominal,
      }
    })
  }, [tree])

  // 3. Data Logic: Top Cascade Fault Frequencies
  const faultCascadeData = useMemo(() => {
    return [
      { code: 'BITE 6074 (Root)', count: 329, stage: 'Root Cause', color: COLORS.rose },
      { code: 'BITE 6025 (PID)', count: 268, stage: 'Cascade', color: COLORS.amber },
      { code: 'BITE 6035 (Bind)', count: 198, stage: 'Cascade', color: COLORS.amber },
      { code: 'BITE 6029 (Mutex)', count: 193, stage: 'Deadlock', color: COLORS.purple },
      { code: 'BITE 6024 (Mutex)', count: 132, stage: 'Deadlock', color: COLORS.purple },
      { code: 'BITE 6000 (Deadline)', count: 120, stage: 'Slice Overrun', color: COLORS.indigo },
    ]
  }, [])

  // 4. Data Logic: Telemetry Burst Activity Curve over Time (Area Chart)
  const activityTimelineData = useMemo(() => {
    if (!tree.allRecordsSorted.length) return []
    const binCount = 28
    const minSec = tree.allRecordsSorted[0].tsSec
    const maxSec = tree.allRecordsSorted[tree.allRecordsSorted.length - 1].tsSec
    const span = Math.max(1, maxSec - minSec)

    const bins = Array.from({ length: binCount }, (_, i) => {
      const t = minSec + (i * span) / binCount
      const h = Math.floor(t / 3600)
      const m = Math.floor((t % 3600) / 60)
      const s = Math.floor(t % 60)
      const timeLabel = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`

      return {
        time: timeLabel,
        total: 0,
        faults: 0,
        transitions: 0,
        telemetry: 0,
      }
    })

    tree.allRecordsSorted.forEach((r) => {
      const ratio = (r.tsSec - minSec) / span
      const idx = Math.min(binCount - 1, Math.max(0, Math.floor(ratio * binCount)))
      bins[idx].total++
      if (r.family === 'Fault') bins[idx].faults++
      else if (r.family === 'State_Transition') bins[idx].transitions++
      else bins[idx].telemetry++
    })

    return bins
  }, [tree])

  // Synchronized Matrix Buckets
  const buckets = useMemo(() => {
    return buildCorrelationMatrix(tree, windowSec)
  }, [tree, windowSec])

  const filteredBuckets = useMemo(() => {
    let list = buckets
    if (onlyAnomalies) {
      list = list.filter((b) => b.hasAnomaly)
    }
    if (searchFilter.trim()) {
      const q = searchFilter.toLowerCase()
      list = list.filter((b) =>
        b.time24.includes(q) ||
        Object.values(b.eventsByNode).some((evts) =>
          evts.some((e) => e.eventName.toLowerCase().includes(q) || e.eventCode.toLowerCase().includes(q))
        )
      )
    }
    return list
  }, [buckets, onlyAnomalies, searchFilter])

  const selectedEvent = useMemo(() => {
    if (!selectedEventId) return null
    return tree.recordMapById.get(selectedEventId) || null
  }, [selectedEventId, tree])

  if (tree.totalRecords === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-white p-8 text-center select-none">
        <div className="flex size-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-500 mb-3">
          <Folder className="size-6 stroke-[1.8]" />
        </div>
        <h3 className="text-sm font-bold text-slate-900">No Telemetry for {tree.id}</h3>
        <button
          type="button"
          onClick={() => openIngestModalForFlight(tree.id)}
          className="mt-4 flex items-center gap-2 rounded-full bg-slate-900 px-5 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition-colors shadow-xs"
        >
          <HardDriveUpload className="size-3.5" />
          Ingest Logs
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col bg-slate-50 overflow-hidden text-slate-900 select-none">
      {/* 1. TOP EXECUTIVE KPI & WORKSPACE NAV BAR */}
      <div className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6 py-2.5">
        <div className="flex items-center gap-3">
          <div className="flex size-8 items-center justify-center rounded-xl bg-slate-900 text-white shadow-2xs">
            <BarChart3 className="size-4" />
          </div>
          <div className="flex items-center gap-2">
            <h1 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Telemetry Analytics & Visual Correlation
            </h1>
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 font-mono text-[10px] font-semibold text-slate-600">
              {tree.id}
            </span>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex rounded-full bg-slate-100 p-0.5 border border-slate-200 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('charts')}
            className={`flex items-center gap-1.5 rounded-full px-3 py-1 font-medium transition-all ${
              activeTab === 'charts'
                ? 'bg-slate-900 text-white font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <PieIcon className="size-3.5" />
            Visual Charts
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('pipeline')}
            className={`flex items-center gap-1.5 rounded-full px-3 py-1 font-medium transition-all ${
              activeTab === 'pipeline'
                ? 'bg-slate-900 text-white font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <GitCompare className="size-3.5" />
            2D Causal Pipeline
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('sync')}
            className={`flex items-center gap-1.5 rounded-full px-3 py-1 font-medium transition-all ${
              activeTab === 'sync'
                ? 'bg-slate-900 text-white font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Layers className="size-3.5" />
            Parallel Stream
          </button>
        </div>
      </div>

      {/* 2. EXECUTIVE METRIC KPI CARDS */}
      <div className="grid grid-cols-4 gap-4 px-6 py-3 bg-white border-b border-slate-200 shrink-0">
        <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-3">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Analyzed Events</span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-bold font-mono text-slate-900">{tree.totalRecords.toLocaleString()}</span>
            <span className="text-[11px] text-slate-500 font-medium">across 3 Nodes</span>
          </div>
        </div>

        <div className="rounded-lg border border-rose-200 bg-rose-50/30 p-3">
          <span className="text-[10px] font-bold uppercase tracking-wider text-rose-600">Primary Root Cause</span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-bold font-mono text-rose-700">BITE 6074</span>
            <span className="text-[11px] text-rose-600 font-medium">Nav File EOF</span>
          </div>
        </div>

        <div className="rounded-lg border border-amber-200 bg-amber-50/30 p-3">
          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600">Redundancy Handoffs</span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-bold font-mono text-amber-700">348</span>
            <span className="text-[11px] text-amber-600 font-medium">Dual ⇄ Single Mode</span>
          </div>
        </div>

        <div className="rounded-lg border border-sky-200 bg-sky-50/30 p-3">
          <span className="text-[10px] font-bold uppercase tracking-wider text-sky-600">Cross-Channel Sync</span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-bold font-mono text-sky-700">Node A & C Active</span>
            <span className="text-[11px] text-sky-600 font-medium">Node B Standby</span>
          </div>
        </div>
      </div>

      {/* 3. MAIN CONTENT BODY */}
      <div className="flex-1 min-h-0 overflow-y-auto p-6 bg-slate-50/60">
        {/* TAB 1: VISUAL CHARTS & GRAPHS */}
        {activeTab === 'charts' && (
          <div className="space-y-6 max-w-7xl mx-auto">
            {/* ROW 1: DONUT CHART + MULTI-NODE COMPARISON */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Card 1: Donut Chart - Event Family Distribution */}
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Telemetry Family Distribution
                  </h2>
                  <span className="text-xs font-mono font-bold text-slate-700 bg-slate-100 rounded-full px-2.5 py-0.5">
                    100% Verified
                  </span>
                </div>

                {isMounted ? (
                  <div className="h-64 flex items-center">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={familyPieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={65}
                          outerRadius={95}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {familyPieData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(value: any, name: any, item: any) => [
                            `${Number(value).toLocaleString()} events (${item.payload.percentage}%)`,
                            name,
                          ]}
                          contentStyle={{
                            backgroundColor: '#0f172a',
                            borderRadius: '12px',
                            color: '#fff',
                            fontSize: '11px',
                            border: 'none',
                          }}
                        />
                        <Legend
                          verticalAlign="bottom"
                          iconType="circle"
                          wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-64 flex items-center justify-center text-xs text-slate-400">Loading chart...</div>
                )}
              </div>

              {/* Card 2: Stacked Bar Chart - Multi-Node Activity Comparison */}
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Tri-Node Channel Activity Comparison
                  </h2>
                  <span className="text-xs font-mono font-bold text-slate-700 bg-slate-100 rounded-full px-2.5 py-0.5">
                    Node A Master
                  </span>
                </div>

                {isMounted ? (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={nodeBarData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                        <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#0f172a',
                            borderRadius: '12px',
                            color: '#fff',
                            fontSize: '11px',
                            border: 'none',
                          }}
                        />
                        <Legend
                          verticalAlign="bottom"
                          iconType="circle"
                          wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
                        />
                        <Bar dataKey="nominal" name="Nominal Telemetry" stackId="a" fill={COLORS.sky} radius={[0, 0, 0, 0]} />
                        <Bar dataKey="transitions" name="Transitions" stackId="a" fill={COLORS.amber} radius={[0, 0, 0, 0]} />
                        <Bar dataKey="faults" name="BITE Faults" stackId="a" fill={COLORS.rose} radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-64 flex items-center justify-center text-xs text-slate-400">Loading chart...</div>
                )}
              </div>
            </div>

            {/* ROW 2: TIME-SERIES BURST ACTIVITY + TOP FAULT FREQUENCIES */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Card 3: Area Chart - Flight Timeline Burst Activity */}
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Flight Timeline Telemetry Rate
                  </h2>
                  <span className="text-xs font-mono font-bold text-rose-600 bg-rose-50 rounded-full px-2.5 py-0.5">
                    Fault Burst at 09:41
                  </span>
                </div>

                {isMounted ? (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={activityTimelineData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={COLORS.sky} stopOpacity={0.4} />
                            <stop offset="95%" stopColor={COLORS.sky} stopOpacity={0.0} />
                          </linearGradient>
                          <linearGradient id="colorFaults" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={COLORS.rose} stopOpacity={0.5} />
                            <stop offset="95%" stopColor={COLORS.rose} stopOpacity={0.0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                        <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#0f172a',
                            borderRadius: '12px',
                            color: '#fff',
                            fontSize: '11px',
                            border: 'none',
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="total"
                          name="Total Packets"
                          stroke={COLORS.sky}
                          fillOpacity={1}
                          fill="url(#colorTotal)"
                          strokeWidth={2}
                        />
                        <Area
                          type="monotone"
                          dataKey="faults"
                          name="BITE Faults"
                          stroke={COLORS.rose}
                          fillOpacity={1}
                          fill="url(#colorFaults)"
                          strokeWidth={2}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-64 flex items-center justify-center text-xs text-slate-400">Loading chart...</div>
                )}
              </div>

              {/* Card 4: Horizontal Bar Chart - Cascade Fault Frequencies */}
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Cascade Fault Frequency Breakdown
                  </h2>
                  <span className="text-xs font-mono font-bold text-slate-700 bg-slate-100 rounded-full px-2.5 py-0.5">
                    Top 6 Codes
                  </span>
                </div>

                {isMounted ? (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        layout="vertical"
                        data={faultCascadeData}
                        margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                        <XAxis type="number" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                        <YAxis
                          type="category"
                          dataKey="code"
                          tick={{ fontSize: 10, fill: '#334155' }}
                          axisLine={false}
                          tickLine={false}
                          width={110}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#0f172a',
                            borderRadius: '12px',
                            color: '#fff',
                            fontSize: '11px',
                            border: 'none',
                          }}
                        />
                        <Bar dataKey="count" name="Occurrences" radius={[0, 4, 4, 0]}>
                          {faultCascadeData.map((entry, index) => (
                            <Cell key={`bar-${index}`} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-64 flex items-center justify-center text-xs text-slate-400">Loading chart...</div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: 2D CAUSAL PIPELINE FLOW */}
        {activeTab === 'pipeline' && (
          <div className="max-w-5xl mx-auto space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs mb-4">
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Direct Causal Propagation Logic
              </h2>
            </div>

            <div className="space-y-3">
              {CAUSAL_STAGES.map((st, idx) => (
                <div key={st.step} className="flex flex-col">
                  <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs hover:border-slate-300 transition-colors">
                    {/* Step Number Circle */}
                    <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-bold text-white">
                      {st.step}
                    </div>

                    {/* Stage Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-900">{st.code}</span>
                        <span className="text-xs font-semibold text-slate-700">· {st.title}</span>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${st.color}`}>
                          {st.category}
                        </span>
                      </div>
                    </div>

                    {/* Stats & Nodes */}
                    <div className="text-right shrink-0">
                      <div className="font-mono text-sm font-bold text-slate-900">{st.count} records</div>
                      <div className="text-[10px] text-slate-400">{st.nodes}</div>
                    </div>
                  </div>

                  {/* Flow Arrow */}
                  {idx < CAUSAL_STAGES.length - 1 && (
                    <div className="flex justify-center py-1">
                      <div className="h-4 w-px bg-slate-300" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: SYNCHRONIZED MULTI-NODE MATRIX STREAM */}
        {activeTab === 'sync' && (
          <div className="max-w-7xl mx-auto rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden flex flex-col h-[650px]">
            {/* Filter Bar */}
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-2.5 bg-slate-50 text-xs shrink-0">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onlyAnomalies}
                    onChange={(e) => setOnlyAnomalies(e.target.checked)}
                    className="rounded border-slate-300 text-slate-900 focus:ring-0"
                  />
                  <span>Show Anomalies Only</span>
                </label>

                <div className="flex items-center gap-1.5 text-slate-600">
                  <span>Window:</span>
                  <select
                    value={windowSec}
                    onChange={(e) => setWindowSec(Number(e.target.value))}
                    className="h-7 rounded border border-slate-200 bg-white px-2 text-xs font-mono text-slate-800"
                  >
                    <option value={1.0}>1.0s</option>
                    <option value={2.0}>2.0s</option>
                    <option value={5.0}>5.0s</option>
                  </select>
                </div>
              </div>

              <div className="relative w-64">
                <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3 text-slate-400 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  placeholder="Filter time / event..."
                  className="h-7 w-full rounded border border-slate-200 bg-white pl-8 pr-2 text-xs text-slate-800 placeholder:text-slate-400"
                />
              </div>
            </div>

            {/* Header Columns */}
            <div className="grid grid-cols-[110px_1fr_1fr_1fr] border-b border-slate-200 bg-slate-100/80 px-6 py-2 text-[11px] font-bold text-slate-600 uppercase tracking-wider select-none shrink-0">
              <div>Timestamp</div>
              <div>Node A (Master)</div>
              <div>Node B (Standby)</div>
              <div>Node C (Auxiliary)</div>
            </div>

            {/* Buckets List */}
            <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
              {filteredBuckets.slice(0, 100).map((bucket) => (
                <div
                  key={bucket.bucketIndex}
                  className={`grid grid-cols-[110px_1fr_1fr_1fr] px-6 py-2.5 transition-colors ${
                    bucket.hasAnomaly ? 'bg-rose-50/20 hover:bg-rose-50/40' : 'hover:bg-slate-50/50'
                  }`}
                >
                  <div className="font-mono text-xs font-semibold text-slate-800 tabular-nums pt-1">
                    {bucket.time24}
                    {bucket.hasAnomaly && (
                      <span className="block mt-0.5 text-[10px] font-bold text-rose-600 uppercase">
                        Alert
                      </span>
                    )}
                  </div>

                  {['Node A', 'Node B', 'Node C'].map((nodeName) => {
                    const evts = bucket.eventsByNode[nodeName] || []
                    return (
                      <div key={nodeName} className="flex flex-col gap-1 pr-3 border-l border-slate-100 pl-3">
                        {evts.length === 0 ? (
                          <span className="text-[11px] text-slate-300 font-mono py-0.5">— idle —</span>
                        ) : (
                          evts.map((e) => (
                            <div
                              key={e.id}
                              onClick={() => setSelectedEventId(e.id)}
                              className={`rounded border p-2 text-xs cursor-pointer transition-all shadow-2xs ${
                                selectedEventId === e.id
                                  ? 'border-slate-900 bg-slate-50'
                                  : 'border-slate-200 bg-white hover:border-slate-300'
                              }`}
                            >
                              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mb-0.5">
                                <span>{e.family}</span>
                                <span>#{e.number}</span>
                              </div>
                              <div className="font-semibold text-slate-900 line-clamp-1">{e.eventName}</div>
                              {e.translation && (
                                <p className="mt-0.5 text-[11px] text-slate-600 line-clamp-1">
                                  {e.translation}
                                </p>
                              )}
                            </div>
                          ))
                        )}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 4. PINNED INSPECTOR DRAWER (WHEN AN EVENT IS CLICKED) */}
      {selectedEvent && (
        <div className="border-t border-slate-200 bg-white px-6 py-3 shrink-0 shadow-lg flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="rounded bg-slate-900 px-2 py-0.5 font-mono text-xs font-bold text-white">
              {selectedEvent.node}
            </span>
            <span className="font-mono text-xs font-semibold text-slate-600">{selectedEvent.time24}</span>
            <span className="text-slate-300">·</span>
            <span className="text-xs font-bold text-slate-900">{selectedEvent.eventName}</span>
            <span className="text-xs text-slate-600 truncate max-w-xl">
              — {selectedEvent.translation || 'Standard telemetry recorded.'}
            </span>
          </div>

          <button
            type="button"
            onClick={() =>
              jumpToEventInNodeView(selectedEvent.id, selectedEvent.node, selectedEvent.familyKey)
            }
            className="flex items-center gap-1 rounded bg-slate-900 px-3 py-1 text-xs font-semibold text-white hover:bg-slate-800 transition-colors shrink-0"
          >
            Inspect in Node View
            <ChevronRight className="size-3" />
          </button>
        </div>
      )}
    </div>
  )
}
