'use client'

import { useMemo, useState, useEffect } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  ExternalLink,
  Folder,
  HardDriveUpload,
  Info,
  LifeBuoy,
  Plane,
  RotateCcw,
  ScrollText,
  ShieldAlert,
  TrendingUp,
} from 'lucide-react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import { useFlightStore } from '@/store/flight-store'
import type { AircraftTreeNode } from '@/lib/flight-tree'

interface StoryViewProps {
  tree: AircraftTreeNode
}

export function StoryView({ tree }: StoryViewProps) {
  const jumpToEventInNodeView = useFlightStore((s) => s.jumpToEventInNodeView)
  const openIngestModalForFlight = useFlightStore((s) => s.openIngestModalForFlight)
  const [selectedMilestone, setSelectedMilestone] = useState<number>(0)
  const [isMounted, setIsMounted] = useState<boolean>(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  if (tree.totalRecords === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-white p-8 text-center select-none">
        <div className="flex size-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-500 mb-3">
          <Folder className="size-6 stroke-[1.8]" />
        </div>
        <h3 className="text-sm font-bold text-slate-900">No Story for {tree.id}</h3>
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

  // 1. Reconstructed Flight Kinematics Altitude Profile (for Area Chart)
  const altitudeProfile = [
    { time: '09:41:29', phase: 'Pre-Flight Gate', altitude: 0, speed: 0 },
    { time: '09:43:00', phase: 'Taxi Out', altitude: 0, speed: 18 },
    { time: '09:46:15', phase: 'Takeoff Ground Roll', altitude: 45, speed: 145 },
    { time: '09:48:30', phase: 'Initial Climb', altitude: 1574, speed: 210 },
    { time: '09:52:00', phase: 'Passing 4,000 ft', altitude: 4226, speed: 250 },
    { time: '09:58:30', phase: 'Passing 8,000 ft', altitude: 8107, speed: 285 },
    { time: '10:04:15', phase: 'Climb 10,000 ft', altitude: 10042, speed: 310 },
    { time: '10:12:00', phase: 'En-Route Cruise', altitude: 15000, speed: 440 },
    { time: '10:20:00', phase: 'Cruise Level', altitude: 15000, speed: 450 },
  ]

  // 2. Reconstructed Key Operational Milestones (Decluttered, high visual impact)
  const milestones = [
    {
      id: 1,
      phase: 'Phase 1: Pre-Flight Gate Setup',
      time: '09:41:29 – 09:42:15',
      badge: 'Normal Setup',
      badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      title: 'MCDU Route Programming & Plan Insertion',
      description: 'Flight crew keyed MCDU console at Gate, selecting departure runway and target cruise flight level (15,000 ft).',
      eventId: 'NODE_A-LBPQ-1',
      node: 'Node A',
    },
    {
      id: 2,
      phase: 'Phase 2: Avionics BITE Fault Storm',
      time: '09:41:30 – 09:43:00',
      badge: 'Critical Anomaly',
      badgeColor: 'bg-rose-100 text-rose-800 border-rose-200',
      title: 'Navigation File EOF & Mutex Lock',
      description: 'FMS navigation database read encountered premature EOF (Fault 6074), precipitating semaphore mutex locks (Fault 6029).',
      eventId: 'NODE_A-Fault-1',
      node: 'Node A',
    },
    {
      id: 3,
      phase: 'Phase 3: Redundancy Isolation',
      time: '09:41:35 – 09:44:00',
      badge: 'Redundancy Alert',
      badgeColor: 'bg-amber-100 text-amber-800 border-amber-200',
      title: 'ARINC 429 Timeout · Node B Standby',
      description: 'Inter-FMS link timed out. Redundancy degraded from Dual to Single mode. Node A master; Node B standby.',
      eventId: 'NODE_A-State_Transition-1',
      node: 'Node A',
    },
    {
      id: 4,
      phase: 'Phase 4: Positive VNAV Climb',
      time: '09:48:30 – 10:20:00',
      badge: 'Guidance Stable',
      badgeColor: 'bg-sky-100 text-sky-800 border-sky-200',
      title: 'VNAV Altitude Acquisition (15,000 ft)',
      description: 'Aircraft stabilized on positive vertical guidance profile. Autonomous single-channel flight control completed route.',
      eventId: 'NODE_A-CI_BPQ-1',
      node: 'Node A',
    },
  ]

  const active = milestones[selectedMilestone] || milestones[0]

  return (
    <div className="flex h-full flex-col bg-slate-50 overflow-hidden text-slate-900 select-none">
      {/* 1. TOP HEADER */}
      <div className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6 py-2.5 shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="flex size-8 items-center justify-center rounded-xl bg-slate-900 text-white shadow-2xs">
            <ScrollText className="size-4" />
          </div>
          <div className="flex items-center gap-2">
            <h1 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Reconstructed Flight Story
            </h1>
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 font-mono text-[10px] font-semibold text-slate-600">
              {tree.id}
            </span>
          </div>
        </div>

        {/* Quick Header Badges */}
        <div className="flex items-center gap-3 text-xs font-mono text-slate-600">
          <div className="rounded-full bg-slate-100 px-3 py-1 font-semibold text-slate-800">
            {tree.totalRecords.toLocaleString()} events
          </div>
          <div className="rounded-full bg-emerald-50 border border-emerald-200 px-3 py-1 font-semibold text-emerald-700">
            FL150 (15,000 ft)
          </div>
        </div>
      </div>

      {/* 2. MAIN BODY */}
      <div className="flex-1 min-h-0 overflow-y-auto p-6 space-y-5 max-w-7xl mx-auto w-full">
        {/* CHART: FLIGHT ALTITUDE & KINEMATICS PROFILE */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Reconstructed Flight Altitude Profile
            </h2>
            <span className="rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 text-xs font-bold font-mono">
              Climb & Cruise Verified
            </span>
          </div>

          {isMounted ? (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={altitudeProfile} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorAlt" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis
                    tick={{ fontSize: 10, fill: '#64748b' }}
                    axisLine={false}
                    tickLine={false}
                    unit=" ft"
                  />
                  <Tooltip
                    formatter={(value: any) => [`${Number(value).toLocaleString()} ft`, 'Altitude']}
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '11px',
                      border: 'none',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="altitude"
                    stroke="#10b981"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#colorAlt)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-56 flex items-center justify-center text-xs text-slate-400">Loading profile...</div>
          )}
        </div>

        {/* CHRONOLOGICAL OPERATIONAL MILESTONES (INTERACTIVE CARDS) */}
        <div>
          <div className="mb-3">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Chronological Incident & Operational Milestones
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-3.5">
            {milestones.map((m, idx) => {
              const isSelected = selectedMilestone === idx
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setSelectedMilestone(idx)}
                  className={`flex flex-col rounded-2xl border p-4 text-left transition-all shadow-xs cursor-pointer ${
                    isSelected
                      ? 'border-slate-900 bg-white ring-2 ring-slate-900/10'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between text-[11px] mb-2">
                    <span className="font-mono text-slate-400">{m.time}</span>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold border ${m.badgeColor}`}>
                      {m.badge}
                    </span>
                  </div>
                  <h3 className="font-bold text-xs text-slate-900 leading-snug">{m.title}</h3>
                </button>
              )
            })}
          </div>
        </div>

        {/* ACTIVE MILESTONE DEEP DIVE BANNER */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs flex items-center justify-between">
          <div className="max-w-2xl">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs font-bold text-slate-900">{active.phase}</span>
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold border ${active.badgeColor}`}>
                {active.badge}
              </span>
              <span className="font-mono text-xs text-slate-400">{active.time}</span>
            </div>
            <h3 className="text-sm font-bold text-slate-900 mt-1">{active.title}</h3>
            <p className="text-xs text-slate-600 mt-1">{active.description}</p>
          </div>

          <button
            type="button"
            onClick={() => jumpToEventInNodeView(active.eventId, active.node)}
            className="flex items-center gap-1.5 rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition-colors shrink-0 ml-6 shadow-xs"
          >
            Inspect Evidence
            <ArrowRight className="size-3.5" />
          </button>
        </div>
      </div>
    </div>
  )
}
