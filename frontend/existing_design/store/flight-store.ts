import { create } from 'zustand'

export type FlightViewMode = 'node' | 'story' | 'correlation'

interface FlightStoreState {
  activeAircraftId: string
  activeView: FlightViewMode
  selectedNode: string // "Node A" | "Node B" | "Node C" | "All Nodes"
  selectedFamilyKey: string // "fam1" | "fam2" | "fam3" | "fam4" | "fam5" | "all"
  selectedEventId: string | null
  expandedRowId: string | null
  searchQuery: string
  
  // Modals
  isIngestModalOpen: boolean
  isAddNodeModalOpen: boolean
  isDeleteModalOpen: boolean
  targetUploadFlightId: string
  targetDeleteFlightId: string
  deletedAircraftIds: Record<string, boolean>

  // Tree folder expansion states
  openAircraftFolders: Record<string, boolean>

  // Actions
  setActiveAircraft: (id: string) => void
  setActiveView: (view: FlightViewMode) => void
  setSelectedNode: (node: string) => void
  setSelectedFamilyKey: (famKey: string) => void
  setSelectedEventId: (id: string | null) => void
  setExpandedRowId: (id: string | null) => void
  setSearchQuery: (query: string) => void
  
  setIngestModalOpen: (open: boolean) => void
  openIngestModalForFlight: (flightId: string) => void
  setAddNodeModalOpen: (open: boolean) => void
  setDeleteModalOpen: (open: boolean) => void
  openDeleteModalForFlight: (flightId: string) => void
  confirmDeleteAircraft: (flightId: string) => void
  toggleAircraftFolder: (id: string) => void
  
  // Quick jump from Story citation to specific Event in Node View
  jumpToEventInNodeView: (eventId: string, nodeName?: string, familyKey?: string) => void
}

export const useFlightStore = create<FlightStoreState>((set) => ({
  activeAircraftId: 'AA100',
  activeView: 'node',
  selectedNode: 'Node A',
  selectedFamilyKey: 'fam1',
  selectedEventId: null,
  expandedRowId: null,
  searchQuery: '',

  isIngestModalOpen: false,
  isAddNodeModalOpen: false,
  isDeleteModalOpen: false,
  targetUploadFlightId: 'AA100',
  targetDeleteFlightId: 'AA100',
  deletedAircraftIds: {},
  openAircraftFolders: {
    AA100: true,
    AA101: false,
    AA102: false,
  },

  setActiveAircraft: (id) => set({ activeAircraftId: id, selectedEventId: null, expandedRowId: null }),
  setActiveView: (view) => set({ activeView: view }),
  setSelectedNode: (node) => set({ selectedNode: node }),
  setSelectedFamilyKey: (famKey) => set({ selectedFamilyKey: famKey }),
  setSelectedEventId: (id) => set({ selectedEventId: id }),
  setExpandedRowId: (id) => set((s) => ({ expandedRowId: s.expandedRowId === id ? null : id })),
  setSearchQuery: (query) => set({ searchQuery: query }),

  setIngestModalOpen: (open) => set({ isIngestModalOpen: open }),
  openIngestModalForFlight: (flightId) =>
    set({ isIngestModalOpen: true, targetUploadFlightId: flightId }),
  setAddNodeModalOpen: (open) => set({ isAddNodeModalOpen: open }),
  setDeleteModalOpen: (open) => set({ isDeleteModalOpen: open }),
  openDeleteModalForFlight: (flightId) =>
    set({ isDeleteModalOpen: true, targetDeleteFlightId: flightId }),
  confirmDeleteAircraft: (flightId) =>
    set((s) => ({
      deletedAircraftIds: { ...s.deletedAircraftIds, [flightId]: true },
      isDeleteModalOpen: false,
      selectedEventId: null,
      expandedRowId: null,
    })),
  toggleAircraftFolder: (id) =>
    set((s) => ({
      openAircraftFolders: {
        ...s.openAircraftFolders,
        [id]: !s.openAircraftFolders[id],
      },
    })),

  jumpToEventInNodeView: (eventId, nodeName, familyKey) =>
    set({
      activeView: 'node',
      selectedEventId: eventId,
      expandedRowId: eventId,
      ...(nodeName ? { selectedNode: nodeName } : {}),
      ...(familyKey ? { selectedFamilyKey: familyKey } : {}),
    }),
}))
