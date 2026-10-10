'use client'

import { useEffect, useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  Database,
  Folder,
  FolderOpen,
  GitCompare,
  HardDriveUpload,
  LayoutGrid,
  MoreVertical,
  Orbit,
  Plane,
  ScrollText,
  Server,
  Trash2,
} from 'lucide-react'
import { useFlightStore, type FlightViewMode } from '@/store/flight-store'
import type { AircraftTreeNode } from '@/lib/flight-tree'

interface FlightTreeSidebarProps {
  tree: AircraftTreeNode
}

export function FlightTreeSidebar({ tree }: FlightTreeSidebarProps) {
  const activeAircraftId = useFlightStore((s) => s.activeAircraftId)
  const activeView = useFlightStore((s) => s.activeView)
  const setActiveAircraft = useFlightStore((s) => s.setActiveAircraft)
  const setActiveView = useFlightStore((s) => s.setActiveView)
  const openAircraftFolders = useFlightStore((s) => s.openAircraftFolders)
  const toggleAircraftFolder = useFlightStore((s) => s.toggleAircraftFolder)
  const openIngestModalForFlight = useFlightStore((s) => s.openIngestModalForFlight)
  const setAddNodeModalOpen = useFlightStore((s) => s.setAddNodeModalOpen)
  const openDeleteModalForFlight = useFlightStore((s) => s.openDeleteModalForFlight)
  const deletedAircraftIds = useFlightStore((s) => s.deletedAircraftIds)

  const [activeFlightMenu, setActiveFlightMenu] = useState<string | null>(null)
  const [backendRecords, setBackendRecords] = useState<number>(5257)

  // Query live DuckDB status
  useEffect(() => {
    fetch('http://localhost:8000/api/status')
      .then((res) => res.json())
      .then((data) => {
        if (data.total_records) {
          setBackendRecords(data.total_records)
        }
      })
      .catch(() => {
        setBackendRecords(5257)
      })
  }, [])

  const aircraftList = [
    {
      id: 'AA100',
      label: 'AA100',
      route: 'SFO → JFK',
      records: deletedAircraftIds['AA100'] ? 0 : backendRecords,
    },
    {
      id: 'AA101',
      label: 'AA101',
      route: 'LHR → SIN',
      records: deletedAircraftIds['AA101'] ? 0 : 0,
    },
    {
      id: 'AA102',
      label: 'AA102',
      route: 'HND → SFO',
      records: deletedAircraftIds['AA102'] ? 0 : 0,
    },
  ]

  const navItems: { view: FlightViewMode; label: string; icon: any }[] = [
    {
      view: 'node',
      label: 'Node View',
      icon: LayoutGrid,
    },
    {
      view: 'story',
      label: 'Story View',
      icon: ScrollText,
    },
    {
      view: 'correlation',
      label: 'Co-relation',
      icon: GitCompare,
    },
    {
      view: 'visualization',
      label: 'Visualization',
      icon: Orbit,
    },
  ]

  return (
    <aside className="flex h-full w-52 shrink-0 flex-col border-r border-slate-200 bg-white select-none text-slate-800">
      {/* Brand Header */}
      <div className="flex h-14 items-center gap-2 border-b border-slate-200 px-3.5">
        <div className="flex size-7 items-center justify-center rounded bg-slate-900 text-white">
          <Plane className="size-3.5" />
        </div>
        <div className="flex flex-col">
          <span className="text-xs font-bold tracking-tight text-slate-900">FlightStory</span>
          <span className="text-[10px] text-slate-400">Avionics Console</span>
        </div>
      </div>

      {/* Compact Navigation Rail */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="mb-2 px-1 text-[9px] font-bold tracking-wider text-slate-400 uppercase">
          Flights
        </div>

        <nav className="flex flex-col gap-1">
          {aircraftList.map((ac) => {
            const isOpen = !!openAircraftFolders[ac.id]
            const isSelectedAircraft = activeAircraftId === ac.id
            const isMenuOpen = activeFlightMenu === ac.id

            return (
              <div key={ac.id} className="relative flex flex-col">
                {/* Aircraft Item Header */}
                <div
                  className={`group/flight flex h-8 items-center justify-between rounded px-1.5 text-xs font-medium transition-colors cursor-pointer ${
                    isSelectedAircraft ? 'bg-slate-100 text-slate-900 font-semibold' : 'text-slate-700 hover:bg-slate-50'
                  }`}
                  onClick={() => {
                    setActiveAircraft(ac.id)
                    toggleAircraftFolder(ac.id)
                  }}
                >
                  <div className="flex items-center gap-1.5 truncate">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleAircraftFolder(ac.id)
                      }}
                      className="p-0.5 text-slate-400 hover:text-slate-700"
                    >
                      {isOpen ? <ChevronDown className="size-3" /> : <ChevronRight className="size-3" />}
                    </button>

                    {isOpen ? (
                      <FolderOpen className="size-3.5 text-slate-600 shrink-0" />
                    ) : (
                      <Folder className="size-3.5 text-slate-400 shrink-0" />
                    )}

                    <span className="text-xs">{ac.label}</span>
                  </div>

                  {/* Cool Three Dots Action Menu */}
                  <div className="relative">
                    <button
                      type="button"
                      title={`Options for ${ac.label}`}
                      onClick={(e) => {
                        e.stopPropagation()
                        setActiveFlightMenu(isMenuOpen ? null : ac.id)
                      }}
                      className="flex size-5 items-center justify-center rounded text-slate-400 hover:bg-slate-200 hover:text-slate-900 transition-colors"
                    >
                      <MoreVertical className="size-3" />
                    </button>

                    {/* Compact Dropdown Menu */}
                    {isMenuOpen && (
                      <div
                        onClick={(e) => e.stopPropagation()}
                        className="absolute right-0 top-6 z-30 w-36 rounded-2xl border border-slate-100 bg-white p-1 shadow-xl text-xs"
                      >
                        <button
                          type="button"
                          onClick={() => {
                            setActiveFlightMenu(null)
                            openIngestModalForFlight(ac.id)
                          }}
                          className="flex w-full items-center gap-2 rounded-xl px-2.5 py-1.5 text-left text-slate-700 hover:bg-slate-50 transition-colors"
                        >
                          <HardDriveUpload className="size-3 text-slate-500" />
                          <span>Ingest Logs</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setActiveFlightMenu(null)
                            setAddNodeModalOpen(true)
                          }}
                          className="flex w-full items-center gap-2 rounded-xl px-2.5 py-1.5 text-left text-slate-700 hover:bg-slate-50 transition-colors"
                        >
                          <Server className="size-3 text-slate-500" />
                          <span>Add Node</span>
                        </button>
                        <div className="my-1 border-t border-slate-100" />
                        <button
                          type="button"
                          onClick={() => {
                            setActiveFlightMenu(null)
                            openDeleteModalForFlight(ac.id)
                          }}
                          className="flex w-full items-center gap-2 rounded-xl px-2.5 py-1.5 text-left text-rose-600 hover:bg-rose-50 transition-colors font-semibold"
                        >
                          <Trash2 className="size-3 text-rose-500" />
                          <span>Delete Aircraft</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Sub-items (Node View, Story View, Co-relation) */}
                {isOpen && (
                  <div className="ml-3.5 flex flex-col gap-0.5 border-l border-slate-200 pl-1.5 my-1">
                    {navItems.map((item) => {
                      const isActive = isSelectedAircraft && activeView === item.view
                      const Icon = item.icon

                      return (
                        <button
                          key={item.view}
                          type="button"
                          onClick={() => {
                            setActiveAircraft(ac.id)
                            setActiveView(item.view)
                          }}
                          className={`flex h-6 items-center rounded px-2 text-xs transition-colors text-left ${
                            isActive
                              ? 'bg-slate-900 font-semibold text-white'
                              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                          }`}
                        >
                          <div className="flex items-center gap-1.5">
                            <Icon className={`size-3 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                            <span className="text-[11px]">{item.label}</span>
                          </div>
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </nav>
      </div>

      {/* Footer System Status */}
      <div className="border-t border-slate-200 p-2.5 bg-white text-[10px] text-slate-500">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="size-1.5 rounded-full bg-emerald-500" />
            <span>DuckDB</span>
          </div>
          <span className="font-mono text-slate-700 font-semibold">{backendRecords.toLocaleString()} rows</span>
        </div>
      </div>
    </aside>
  )
}
