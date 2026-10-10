'use client'

import { useMemo } from 'react'
import type { RawDataset } from '@/data/schemas'
import { buildFlightTree, createEmptyFlightTree, type AircraftTreeNode } from '@/lib/flight-tree'
import { useFlightStore } from '@/store/flight-store'
import { FlightTreeSidebar } from './sidebar/flight-tree-sidebar'
import { NodeView } from './views/node-view'
import { StoryView } from './views/story-view'
import { CorrelationView } from './views/correlation-view'
import { Flight3DVisualization } from './views/flight-3d-visualization'
import { IngestModal } from './modals/ingest-modal'
import { AddNodeModal } from './modals/add-node-modal'
import { DeleteAircraftModal } from './modals/delete-aircraft-modal'

export function Visualiser({ raw }: { raw: RawDataset }) {
  const deletedAircraftIds = useFlightStore((s) => s.deletedAircraftIds)

  // Build isolated Flight Trees strictly restricted per flight
  const flightTrees = useMemo<Record<string, AircraftTreeNode>>(() => {
    const isAA100Deleted = !!deletedAircraftIds['AA100'] || !raw.events || raw.events.length === 0
    const aa100 = isAA100Deleted
      ? createEmptyFlightTree('AA100', 'Transcontinental Flight · San Francisco (KSFO) → New York (KJFK)', 'KSFO → KJFK')
      : buildFlightTree(raw, 'AA100', 'Transcontinental Flight · San Francisco (KSFO) → New York (KJFK)')
    const aa101 = createEmptyFlightTree('AA101', 'Long-haul Flight · London Heathrow (EGLL) → Singapore (WSSS)', 'EGLL → WSSS')
    const aa102 = createEmptyFlightTree('AA102', 'Pacific Flight · Tokyo Haneda (RJTT) → San Francisco (KSFO)', 'RJTT → KSFO')

    return {
      AA100: aa100,
      AA101: aa101,
      AA102: aa102,
    }
  }, [raw, deletedAircraftIds])

  const activeAircraftId = useFlightStore((s) => s.activeAircraftId)
  const activeView = useFlightStore((s) => s.activeView)

  const activeTree = flightTrees[activeAircraftId] || flightTrees.AA100

  const hasRecords = activeTree.totalRecords > 0

  return (
    <div className="flex h-dvh w-screen overflow-hidden bg-slate-50 text-slate-900 select-none antialiased">
      {/* 1. Compact Navigation Rail Sidebar */}
      <FlightTreeSidebar tree={activeTree} />

      {/* 2. Main Center Workspace */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden bg-white">
        {/* Single Unified Header Bar */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6">
          {/* Left: Aircraft ID, Flight Route, Tail Number */}
          <div className="flex items-center gap-3">
            <span className="text-base font-bold text-slate-900 tracking-tight">
              {activeTree.id}
            </span>
            <span className="text-slate-300">/</span>
            <span className="text-xs font-semibold text-slate-700">
              {activeTree.route}
            </span>
            <span className="text-slate-300">·</span>
            <span className="font-mono text-[11px] text-slate-500">
              Tail: {activeTree.tailNumber}
            </span>
          </div>

          {/* Right: Ingestion Status, Total Records & Active View Indicator */}
          <div className="flex items-center gap-4 text-xs">
            {/* Ingestion Status Indicator */}
            <div className="flex items-center gap-1.5 font-medium">
              <span
                className={`size-2 rounded-full ${
                  hasRecords ? 'bg-emerald-500' : 'bg-slate-300'
                }`}
              />
              <span className={hasRecords ? 'text-slate-700' : 'text-slate-400'}>
                {hasRecords ? 'Ingestion Ready' : 'Pending Ingest'}
              </span>
            </div>

            <span className="text-slate-200">|</span>

            {/* Total Records Badge */}
            <div className="font-mono text-xs">
              <span className="text-slate-400 mr-1.5">Total Records:</span>
              <span className="font-bold text-slate-900 bg-slate-100 rounded-full px-2.5 py-0.5">
                {hasRecords ? '5,257' : '0'}
              </span>
            </div>

            <span className="text-slate-200">|</span>

            {/* Active View Badge */}
            <span className="rounded-full bg-slate-900 px-3 py-1 text-[11px] font-semibold text-white capitalize shadow-2xs">
              {activeView === 'node'
                ? 'Node View'
                : activeView === 'story'
                ? 'Story View'
                : activeView === 'correlation'
                ? 'Co-relation'
                : '3D Visualization'}
            </span>
          </div>
        </header>

        {/* 3. Main Workspace Container */}
        <main className="flex min-h-0 flex-1 flex-col overflow-hidden bg-white">
          {activeView === 'node' && <NodeView tree={activeTree} />}
          {activeView === 'story' && <StoryView tree={activeTree} />}
          {activeView === 'correlation' && <CorrelationView tree={activeTree} />}
          {activeView === 'visualization' && <Flight3DVisualization tree={activeTree} />}
        </main>
      </div>

      {/* 4. Global Modals (Ingest Data, Add Node & Delete Aircraft) */}
      <IngestModal />
      <AddNodeModal />
      <DeleteAircraftModal />
    </div>
  )
}
