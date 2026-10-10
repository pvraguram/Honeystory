'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import {
  AlertCircle,
  Download,
  Folder,
  HardDriveUpload,
  Search,
  SlidersHorizontal,
} from 'lucide-react'
import { useFlightStore } from '@/store/flight-store'
import {
  FAMILIES_CANONICAL,
  type AircraftTreeNode,
  type EventRecordNode,
} from '@/lib/flight-tree'
import { EventInspector } from './event-inspector'

interface NodeViewProps {
  tree: AircraftTreeNode
}

/**
 * Cleanly formats a readable event description when raw data or translations are presented.
 */
function formatEventDescription(r: EventRecordNode): string {
  if (r.translation && r.translation.trim()) {
    return r.translation
  }

  const fields = r.fields || {}
  const descriptors: string[] = []

  if (fields['Dual mode']) descriptors.push(`Redundancy: ${fields['Dual mode']}`)
  if (fields['Master status']) descriptors.push(`Status: ${fields['Master status']}`)
  if (fields['Altitude'] && fields['Altitude'] !== '-') descriptors.push(`Altitude: ${fields['Altitude']} ft`)
  if (fields['Functional position']) descriptors.push(`Station: ${fields['Functional position']}`)

  if (fields['Message']) {
    const raw = String(fields['Message'])
    const cleaned = raw
      .replace(/Fault identifier code:0Fault identifier subcode:0Active flight leg record:0Sequence:0Date:0Time:0/g, '')
      .replace(/Master status current1:0Dual mode current1:0Opposite fms ok current1:0/g, '')
      .replace(/FMS button push\d+:\d+/g, '')
      .replace(/:/g, ': ')
      .trim()

    if (cleaned && cleaned.length > 4) {
      descriptors.push(cleaned.slice(0, 95) + (cleaned.length > 95 ? '...' : ''))
    }
  }

  if (descriptors.length > 0) {
    return descriptors.join(' · ')
  }

  if (r.eventCode) {
    return `Avionics register code ${r.eventCode}`
  }

  return `Telemetry registered for ${r.node} · ${r.familyDisplayName}`
}

export function NodeView({ tree }: NodeViewProps) {
  const selectedNode = useFlightStore((s) => s.selectedNode)
  const setSelectedNode = useFlightStore((s) => s.setSelectedNode)
  const selectedFamilyKey = useFlightStore((s) => s.selectedFamilyKey)
  const setSelectedFamilyKey = useFlightStore((s) => s.setSelectedFamilyKey)
  const searchQuery = useFlightStore((s) => s.searchQuery)
  const setSearchQuery = useFlightStore((s) => s.setSearchQuery)
  const openIngestModalForFlight = useFlightStore((s) => s.openIngestModalForFlight)

  // Right-hand inspector state
  const [inspectedEvent, setInspectedEvent] = useState<EventRecordNode | null>(null)

  // Virtualizer parent scroll reference
  const parentRef = useRef<HTMLDivElement>(null)

  // Local debounced search state
  const [localSearch, setLocalSearch] = useState(searchQuery)

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(localSearch)
    }, 120)
    return () => clearTimeout(timer)
  }, [localSearch, setSearchQuery])

  useEffect(() => {
    setLocalSearch(searchQuery)
  }, [searchQuery])

  // Main filter tabs: All Nodes, Node A, Node B, Node C
  const nodeOptions = ['All Nodes', 'Node A', 'Node B', 'Node C']

  // Empty state if flight has no records yet (data restricted strictly per flight)
  if (tree.totalRecords === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-white p-8 text-center select-none">
        <div className="flex size-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-500 mb-3">
          <Folder className="size-6 stroke-[1.8]" />
        </div>
        <h3 className="text-sm font-bold text-slate-900">No Records for {tree.id}</h3>
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

  // Gather records according to selected Node & Compact Family Filter
  const filteredRecords = useMemo(() => {
    let list: EventRecordNode[] = []

    if (selectedNode === 'All Nodes') {
      if (selectedFamilyKey === 'all') {
        list = tree.allRecordsSorted
      } else {
        list = tree.allRecordsSorted.filter((r) => r.familyKey === selectedFamilyKey)
      }
    } else {
      const nodeObj = tree.nodes.get(selectedNode)
      if (nodeObj) {
        if (selectedFamilyKey === 'all') {
          nodeObj.families.forEach((fam) => {
            list.push(...fam.records)
          })
          list.sort((a, b) => a.tsSec - b.tsSec || a.number - b.number)
        } else {
          const famObj = nodeObj.families.get(selectedFamilyKey)
          list = famObj ? famObj.records : []
        }
      }
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim()
      list = list.filter((r) =>
        r.searchTokens ? r.searchTokens.includes(q) : r.eventName.toLowerCase().includes(q)
      )
    }

    return list
  }, [tree, selectedNode, selectedFamilyKey, searchQuery])

  // Virtual scrolling engine: renders only ~25-30 visible rows at any millisecond
  const rowVirtualizer = useVirtualizer({
    count: filteredRecords.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 54,
    overscan: 12,
  })

  const exportCurrentTable = (format: 'csv' | 'json') => {
    if (!filteredRecords.length) return
    let content = ''
    let mime = ''
    let filename = `flightstory-${selectedNode.toLowerCase().replace(' ', '-')}-${selectedFamilyKey}.${format}`

    if (format === 'json') {
      content = JSON.stringify(filteredRecords, null, 2)
      mime = 'application/json'
    } else {
      const headers = ['Number', 'Timestamp', 'Node', 'Family', 'Event', 'Code', 'Description']
      const rows = filteredRecords.map((r) => [
        r.number,
        r.time24,
        `"${r.node}"`,
        `"${r.family}"`,
        `"${r.eventName.replace(/"/g, '""')}"`,
        `"${r.eventCode}"`,
        `"${formatEventDescription(r).replace(/"/g, '""')}"`,
      ])
      content = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
      mime = 'text/csv'
    }

    const blob = new Blob([content], { type: mime })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  const compactFamilyPills = [
    { key: 'all', label: 'All Families' },
    { key: 'fam1', label: 'Aircraft State' },
    { key: 'fam2', label: 'Faults' },
    { key: 'fam3', label: 'FM CI BPQ' },
    { key: 'fam4', label: 'FM LBPQ' },
    { key: 'fam5', label: 'Transitions' },
  ]

  return (
    <div className="flex h-full min-h-0 flex-1 overflow-hidden bg-white">
      {/* Main Table Column (Takes Wide Full Screen Width) */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden bg-white">
        {/* 1. Main Node Navigation Tabs (Prominent Top Filter) */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-2.5 bg-slate-50/50">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mr-2">
              Node Filter:
            </span>
            <div className="flex rounded-full bg-slate-200/70 p-0.5">
              {nodeOptions.map((nodeName) => {
                const isSelected = selectedNode === nodeName

                return (
                  <button
                    key={nodeName}
                    type="button"
                    onClick={() => setSelectedNode(nodeName)}
                    className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${
                      isSelected
                        ? 'bg-slate-900 text-white font-semibold shadow-xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
                    }`}
                  >
                    {nodeName}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Quick Search & Export */}
          <div className="flex items-center gap-2">
            <div className="relative w-64">
              <Search className="pointer-events-none absolute top-1/2 left-3 size-3.5 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={localSearch}
                onChange={(e) => setLocalSearch(e.target.value)}
                placeholder="Search events, codes..."
                className="h-8 w-full rounded-full border border-slate-200 bg-white pr-3 pl-8 text-xs text-slate-900 placeholder:text-slate-400 focus:border-slate-400 focus:outline-none"
              />
            </div>
            <button
              type="button"
              onClick={() => exportCurrentTable('csv')}
              title="Export CSV"
              className="flex h-8 items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
            >
              <Download className="size-3 text-slate-500" />
              CSV
            </button>
          </div>
        </div>

        {/* 2. Compact Family Selector Bar (Replaced Permanent 256px Column) */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-2 bg-white text-xs">
          <div className="flex items-center gap-1.5 overflow-x-auto">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1.5">
              Family:
            </span>
            {compactFamilyPills.map((fam) => {
              const isActive = selectedFamilyKey === fam.key

              return (
                <button
                  key={fam.key}
                  type="button"
                  onClick={() => setSelectedFamilyKey(fam.key)}
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-900 text-white font-semibold'
                      : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  {fam.label}
                </button>
              )
            })}
          </div>

          <div className="text-[11px] font-mono text-slate-500 shrink-0 ml-4">
            Showing <span className="font-semibold text-slate-900">{filteredRecords.length.toLocaleString()}</span> rows
          </div>
        </div>

        {/* 3. Wide High-Readability Events Table (Virtualized for 60fps Scrolling) */}
        <div ref={parentRef} className="flex-1 overflow-y-auto">
          {filteredRecords.length === 0 ? (
            <div className="flex h-64 flex-col items-center justify-center text-slate-400">
              <Search className="size-8 stroke-1 text-slate-300" />
              <p className="mt-2 text-sm font-medium text-slate-600">No events found</p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-white border-b border-slate-200 text-[11px] font-semibold text-slate-400 uppercase tracking-wider select-none z-10 shadow-2xs">
                <tr>
                  <th className="py-2.5 pl-6 pr-2 w-16 text-right font-mono">Seq</th>
                  <th className="py-2.5 px-4 w-28 font-mono">Timestamp</th>
                  <th className="py-2.5 px-3 w-24">Node</th>
                  <th className="py-2.5 px-3 w-32">Family</th>
                  <th className="py-2.5 px-4">Event Description</th>
                  <th className="py-2.5 pr-6 pl-2 w-20 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {rowVirtualizer.getVirtualItems().length > 0 && rowVirtualizer.getVirtualItems()[0].start > 0 && (
                  <tr style={{ height: `${rowVirtualizer.getVirtualItems()[0].start}px` }}>
                    <td colSpan={6} />
                  </tr>
                )}
                {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                  const r = filteredRecords[virtualRow.index]
                  if (!r) return null
                  const isSelected = inspectedEvent?.id === r.id
                  const isFault = r.family === 'Fault' || r.flags.length > 0
                  const descriptionText = formatEventDescription(r)

                  return (
                    <tr
                      key={r.id}
                      onClick={() => setInspectedEvent(r)}
                      className={`group cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-slate-100/90 font-medium'
                          : isFault
                          ? 'bg-red-50/20 hover:bg-slate-50'
                          : 'hover:bg-slate-50/80'
                      }`}
                    >
                      {/* Sequence # */}
                      <td className="py-3.5 pl-6 pr-2 font-mono text-slate-400 text-[11px] text-right">
                        #{r.number}
                      </td>

                      {/* Timestamp */}
                      <td className="py-3.5 px-4 font-mono font-medium text-slate-800 tabular-nums">
                        {r.time24}
                      </td>

                      {/* Node */}
                      <td className="py-3.5 px-3">
                        <span className="inline-block rounded bg-slate-100 px-2 py-0.5 font-mono text-[10px] font-medium text-slate-700">
                          {r.node}
                        </span>
                      </td>

                      {/* Family */}
                      <td className="py-3.5 px-3 text-slate-500 font-mono text-[11px] truncate">
                        {r.family}
                      </td>

                      {/* Bold Title & Smaller Description with Breathing Room */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900 text-xs truncate">
                            {r.eventName}
                          </span>
                          {r.eventCode && (
                            <span className="font-mono text-[10px] text-slate-400">
                              [{r.eventCode}]
                            </span>
                          )}
                        </div>
                        <p className="mt-0.5 text-slate-500 text-[11px] leading-relaxed line-clamp-1">
                          {descriptionText}
                        </p>
                      </td>

                      {/* Status Dot / Indicator */}
                      <td className="py-3.5 pr-6 pl-2 text-right">
                        {isFault ? (
                          <span className="inline-flex items-center gap-1 rounded bg-red-100/80 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-red-700">
                            <span className="size-1.5 rounded-full bg-red-600" />
                            Fault
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] font-medium text-slate-600">
                            <span className="size-1.5 rounded-full bg-emerald-500" />
                            Valid
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })}
                {rowVirtualizer.getVirtualItems().length > 0 &&
                  rowVirtualizer.getTotalSize() -
                    rowVirtualizer.getVirtualItems()[rowVirtualizer.getVirtualItems().length - 1].end >
                    0 && (
                    <tr
                      style={{
                        height: `${
                          rowVirtualizer.getTotalSize() -
                          rowVirtualizer.getVirtualItems()[rowVirtualizer.getVirtualItems().length - 1].end
                        }px`,
                      }}
                    >
                      <td colSpan={6} />
                    </tr>
                  )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Right-Hand Event Inspector Drawer (Opens Only When Requested) */}
      {inspectedEvent && (
        <EventInspector event={inspectedEvent} onClose={() => setInspectedEvent(null)} />
      )}
    </div>
  )
}
