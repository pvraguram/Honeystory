'use client'

import {
  BookOpen,
  GitCompare,
  HardDriveUpload,
  Orbit,
  ShieldAlert,
  Activity,
  Cpu,
  Server
} from 'lucide-react'
import { useFlightStore } from '@/store/flight-store'
import type { AircraftTreeNode } from '@/lib/flight-tree'

interface StoryViewProps {
  tree: AircraftTreeNode
}

export function StoryView({ tree }: StoryViewProps) {
  const setActiveView = useFlightStore((s) => s.setActiveView)
  const jumpToStoryIn3D = useFlightStore((s) => s.jumpToStoryIn3D)
  const openIngestModalForFlight = useFlightStore((s) => s.openIngestModalForFlight)

  if (tree.totalRecords === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-[#0d1117] p-8 text-center select-none text-slate-300">
        <div className="flex size-14 items-center justify-center rounded-2xl bg-[#161b22] border border-[#30363d] text-slate-400 mb-3">
          <BookOpen className="size-6 stroke-[1.8]" />
        </div>
        <h3 className="text-sm font-bold text-white">No Forensic Story for {tree.id}</h3>
        <p className="mt-1 text-xs text-slate-400">
          Upload and ingest aircraft telemetry logs to generate the incident storyboard.
        </p>
        <button
          type="button"
          onClick={() => openIngestModalForFlight(tree.id)}
          className="mt-4 flex items-center gap-2 rounded-full bg-[#58a6ff] px-5 py-2 text-xs font-semibold text-black hover:bg-[#79c0ff] transition-colors"
        >
          <HardDriveUpload className="size-3.5" />
          Ingest Flight Logs
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto bg-[#0d1117] text-[#c9d1d9] font-mono select-none antialiased">
      <div className="mx-auto w-full max-w-[960px] p-8 pb-20 flex flex-col gap-6">
        {/* Header Bar */}
        <header className="border-b-2 border-[#30363d] pb-6 flex flex-col gap-3">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <h1 className="text-xl md:text-2xl font-bold uppercase tracking-wider text-[#58a6ff]">
              3-Node Cross-Node Correlation & Incident Narrative Engine
            </h1>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => jumpToStoryIn3D(0)}
                className="flex items-center gap-1.5 rounded border border-[#30363d] bg-[#161b22] px-3 py-1.5 text-xs font-semibold text-[#58a6ff] hover:bg-[#1f242c] transition-colors"
              >
                <Orbit className="size-3.5" />
                <span>3D Flight Tracker</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveView('correlation')}
                className="flex items-center gap-1.5 rounded border border-[#30363d] bg-[#161b22] px-3 py-1.5 text-xs font-semibold text-[#d2a8ff] hover:bg-[#1f242c] transition-colors"
              >
                <GitCompare className="size-3.5" />
                <span>Correlation Matrix</span>
              </button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs text-[#8b949e]">
            <span className="rounded border border-[#30363d] bg-[#161b22] px-2.5 py-1 text-slate-300">
              NODES: <strong className="text-white">Node A, Node B, Node C</strong>
            </span>
            <span className="rounded border border-[#30363d] bg-[#161b22] px-2.5 py-1 text-slate-300">
              AIRCRAFT: <strong className="text-white">{tree.id} ({tree.tailNumber})</strong>
            </span>
            <span className="rounded border border-[#30363d] bg-[#161b22] px-2.5 py-1 text-emerald-400">
              DATA RECORDS: <strong className="text-white">{tree.totalRecords.toLocaleString()}</strong>
            </span>
          </div>
        </header>

        {/* SECTION 1: Parking & Ground Boot Phase */}
        <section className="rounded-lg border border-[#30363d] border-l-4 border-l-[#58a6ff] bg-[#161b22] p-5 leading-relaxed flex flex-col gap-3">
          <div className="flex items-center justify-between border-b border-dashed border-[#30363d] pb-2">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span className="size-2 rounded-full bg-[#58a6ff]" />
              1. Parking & Ground Boot Phase
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold text-[#58a6ff] bg-[#21262d] px-2 py-0.5 rounded border border-[#30363d]">
                Trigger: Node A (FMS Primary)
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
            <div className="flex flex-col gap-1.5 bg-[#0d1117] p-3 rounded border border-[#30363d]">
              <h3 className="text-[11px] font-bold text-slate-400 tracking-wider">PREDICTED WHAT CAN HAPPEN</h3>
              <p className="text-xs text-[#c9d1d9]">Minor power bus fluctuations during initial boot can introduce synchronization delays across secondary nodes.</p>
            </div>
            <div className="flex flex-col gap-1.5 bg-[#0d1117] p-3 rounded border border-[#3fb950]/30 border-l-2 border-l-[#3fb950]">
              <h3 className="text-[11px] font-bold text-[#3fb950] tracking-wider">ACTUAL WHAT HAPPENED</h3>
              <p className="text-xs text-[#c9d1d9]">Serial No 81 logs confirm normal pre-check boot sequence initialized successfully at 09:41:22 AM across all nodes with zero active faults.</p>
            </div>
          </div>

          <div className="mt-2">
            <h3 className="text-[11px] font-bold text-slate-400 mb-3 tracking-wider">INDEPENDENT NODE REACTIONS</h3>
            <div className="flex flex-col gap-3">
              <div className="flex gap-2.5 text-xs items-start">
                <Cpu className="size-4 shrink-0 text-[#d2a8ff]" />
                <div><strong className="text-[#d2a8ff]">NODE A (FMS Primary):</strong> Initialized successfully; baseline power stable at 36°C module temperature.</div>
              </div>
              <div className="flex gap-2.5 text-xs items-start">
                <Server className="size-4 shrink-0 text-[#79c0ff]" />
                <div><strong className="text-[#79c0ff]">NODE B (Avionics Bus Hub):</strong> Standby mode active; monitoring primary bus line with 0ms latency.</div>
              </div>
              <div className="flex gap-2.5 text-xs items-start">
                <Activity className="size-4 shrink-0 text-[#56d364]" />
                <div><strong className="text-[#56d364]">NODE C (GPS/Navigation Unit):</strong> Cold standby; awaiting ephemeris data upload from ground station.</div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 2: Ascent / Climb (Root Trigger Node) */}
        <section className="rounded-lg border border-[#30363d] border-l-4 border-l-[#ff7b72] bg-[#161b22] p-5 leading-relaxed flex flex-col gap-3">
          <div className="flex items-center justify-between border-b border-dashed border-[#30363d] pb-2">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span className="size-2 rounded-full bg-[#ff7b72]" />
              2. Ascent / Climb (Root Trigger Node)
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold text-[#ff7b72] bg-[#21262d] px-2 py-0.5 rounded border border-[#30363d]">
                Trigger: Node A (FMS Primary)
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
            <div className="flex flex-col gap-1.5 bg-[#0d1117] p-3 rounded border border-[#30363d]">
              <h3 className="text-[11px] font-bold text-slate-400 tracking-wider">PREDICTED WHAT CAN HAPPEN</h3>
              <p className="text-xs text-[#c9d1d9]">Unsynchronized repository data requests during rapid climb will trigger memory access blocks and force secondary channel fallback.</p>
            </div>
            <div className="flex flex-col gap-1.5 bg-[#2a1114] p-3 rounded border border-[#ff7b72]/30 border-l-2 border-l-[#ff7b72]">
              <h3 className="text-[11px] font-bold text-[#ff7b72] flex items-center gap-1.5 tracking-wider">
                <ShieldAlert className="size-3.5" /> ACTUAL WHAT HAPPENED
              </h3>
              <p className="text-xs text-[#ff7b72]">Fault Code 6074 triggered ('FMS Data Repository Access Failure') in Node A. This is the absolute Originating Root Cause.</p>
            </div>
          </div>

          <div className="mt-2">
            <h3 className="text-[11px] font-bold text-slate-400 mb-3 tracking-wider">INDEPENDENT NODE REACTIONS</h3>
            <div className="flex flex-col gap-3">
              <div className="flex gap-2.5 text-xs items-start">
                <Cpu className="size-4 shrink-0 text-[#d2a8ff]" />
                <div><strong className="text-[#d2a8ff]">NODE A (FMS Primary):</strong> CRITICAL FAULT CODE 6074: Primary software thread blocked reading repository memory.</div>
              </div>
              <div className="flex gap-2.5 text-xs items-start">
                <Server className="size-4 shrink-0 text-[#79c0ff]" />
                <div><strong className="text-[#79c0ff]">NODE B (Avionics Bus Hub):</strong> Detected bus timeout (Thunderbolt fault); attempted automatic re-routing but failed due to memory lock.</div>
              </div>
              <div className="flex gap-2.5 text-xs items-start">
                <Activity className="size-4 shrink-0 text-[#56d364]" />
                <div><strong className="text-[#56d364]">NODE C (GPS/Navigation Unit):</strong> Unaffected directly, but holding previous vertical speed vector awaiting clean FMS sync.</div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 3: Cruise Phase (Cascading Instability) */}
        <section className="rounded-lg border border-[#30363d] border-l-4 border-l-[#d2a8ff] bg-[#161b22] p-5 leading-relaxed flex flex-col gap-3">
          <div className="flex items-center justify-between border-b border-dashed border-[#30363d] pb-2">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span className="size-2 rounded-full bg-[#d2a8ff]" />
              3. Cruise Phase (Cascading Instability)
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold text-[#d2a8ff] bg-[#21262d] px-2 py-0.5 rounded border border-[#30363d]">
                Trigger: Node B (Avionics Bus Hub)
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
            <div className="flex flex-col gap-1.5 bg-[#0d1117] p-3 rounded border border-[#30363d]">
              <h3 className="text-[11px] font-bold text-slate-400 tracking-wider">PREDICTED WHAT CAN HAPPEN</h3>
              <p className="text-xs text-[#c9d1d9]">Memory addresses will overflow due to uninitialized float reads (-1.55e21), causing opposite channel bus flapping and single-mode degradation.</p>
            </div>
            <div className="flex flex-col gap-1.5 bg-[#1f1a24] p-3 rounded border border-[#d2a8ff]/30 border-l-2 border-l-[#d2a8ff]">
              <h3 className="text-[11px] font-bold text-[#d2a8ff] tracking-wider">ACTUAL WHAT HAPPENED</h3>
              <p className="text-xs text-[#e1c5ff]">Memory address 2050 uninitialized read overflow detected alongside rapid 1-second cross-channel bus synchronization flip-flop.</p>
            </div>
          </div>

          <div className="mt-2">
            <h3 className="text-[11px] font-bold text-slate-400 mb-3 tracking-wider">INDEPENDENT NODE REACTIONS</h3>
            <div className="flex flex-col gap-3">
              <div className="flex gap-2.5 text-xs items-start">
                <Cpu className="size-4 shrink-0 text-[#d2a8ff]" />
                <div><strong className="text-[#d2a8ff]">NODE A (FMS Primary):</strong> Dual mode degraded to Single mode; opposite channel status reported as Unstable.</div>
              </div>
              <div className="flex gap-2.5 text-xs items-start">
                <Server className="size-4 shrink-0 text-[#79c0ff]" />
                <div><strong className="text-[#79c0ff]">NODE B (Avionics Bus Hub):</strong> Bus flapping active; continuous re-transmission requests overloading buffer stack.</div>
              </div>
              <div className="flex gap-2.5 text-xs items-start">
                <Activity className="size-4 shrink-0 text-[#56d364]" />
                <div><strong className="text-[#56d364]">NODE C (GPS/Navigation Unit):</strong> Experiencing minor clock drift due to interrupted polling cycles from Node B.</div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 4: Descent & Approach (Endpoint Manifestation) */}
        <section className="rounded-lg border border-[#30363d] border-l-4 border-l-[#f2cc60] bg-[#161b22] p-5 leading-relaxed flex flex-col gap-3">
          <div className="flex items-center justify-between border-b border-dashed border-[#30363d] pb-2">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span className="size-2 rounded-full bg-[#f2cc60]" />
              4. Descent & Approach (Endpoint Manifestation)
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold text-[#f2cc60] bg-[#21262d] px-2 py-0.5 rounded border border-[#30363d]">
                Trigger: Node C (GPS/Navigation Unit)
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
            <div className="flex flex-col gap-1.5 bg-[#0d1117] p-3 rounded border border-[#30363d]">
              <h3 className="text-[11px] font-bold text-slate-400 tracking-wider">PREDICTED WHAT CAN HAPPEN</h3>
              <p className="text-xs text-[#c9d1d9]">Cumulative timing jitter will manifest as a complete GPS receiver position drop and barometric altitude sensor freeze during final touchdown.</p>
            </div>
            <div className="flex flex-col gap-1.5 bg-[#241f11] p-3 rounded border border-[#f2cc60]/30 border-l-2 border-l-[#f2cc60]">
              <h3 className="text-[11px] font-bold text-[#f2cc60] tracking-wider">ACTUAL WHAT HAPPENED</h3>
              <p className="text-xs text-[#f9e399]">GPS Receiver Cold Start Re-sync Reset drop occurred (0.000000 Lat/Lon) with barometric altitude sensor freeze at 2870.01 ft.</p>
            </div>
          </div>

          <div className="mt-2">
            <h3 className="text-[11px] font-bold text-slate-400 mb-3 tracking-wider">INDEPENDENT NODE REACTIONS</h3>
            <div className="flex flex-col gap-3">
              <div className="flex gap-2.5 text-xs items-start">
                <Cpu className="size-4 shrink-0 text-[#d2a8ff]" />
                <div><strong className="text-[#d2a8ff]">NODE A (FMS Primary):</strong> Issued FMS Service Restart command following total loss of valid position feedback.</div>
              </div>
              <div className="flex gap-2.5 text-xs items-start">
                <Server className="size-4 shrink-0 text-[#79c0ff]" />
                <div><strong className="text-[#79c0ff]">NODE B (Avionics Bus Hub):</strong> Logged extended record exceptions; bus locked awaiting manual override.</div>
              </div>
              <div className="flex gap-2.5 text-xs items-start">
                <Activity className="size-4 shrink-0 text-[#56d364]" />
                <div><strong className="text-[#56d364]">NODE C (GPS/Navigation Unit):</strong> ENDPOINT FAILURE: Receiver lost satellite lock; coordinates reset to 0.000000 and baro sensor frozen.</div>
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>
  )
}