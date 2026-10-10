import { create } from 'zustand'
import type { Filters } from '@/lib/feed'

export type DetailTab = 'backdrop' | 'inference' | 'hypothesis' | 'source'
export const SPEEDS = [1, 5, 20] as const
export type Speed = (typeof SPEEDS)[number]

interface VisState {
  filters: Filters
  query: string
  selectedId: string | null
  panelOpen: boolean
  activeTab: DetailTab
  scrollRequest: { id: string; nonce: number } | null
  expandedBursts: string[]

  playing: boolean
  speed: Speed
  /** null means "caught up to the end of the log". */
  clockSec: number | null
  following: boolean

  filterDrawerOpen: boolean
  skippedOpen: boolean
  overviewOpen: boolean
  theme: 'dark' | 'light'

  toggleFilterValue: (key: 'nodes' | 'families' | 'categories', value: string) => void
  setTimeRange: (range: [number, number] | null) => void
  setQuery: (query: string) => void
  clearFilters: () => void

  focusEvent: (id: string, opts?: { tab?: DetailTab; tsSec?: number }) => void
  selectEvent: (id: string) => void
  closePanel: () => void
  setTab: (tab: DetailTab) => void
  toggleBurst: (key: string, open?: boolean) => void

  setPlaying: (playing: boolean) => void
  setSpeed: (speed: Speed) => void
  setClock: (sec: number | null) => void
  setFollowing: (following: boolean) => void

  setFilterDrawerOpen: (open: boolean) => void
  setSkippedOpen: (open: boolean) => void
  setOverviewOpen: (open: boolean) => void
  toggleTheme: () => void
}

const emptyFilters: Filters = { nodes: [], families: [], categories: [], timeRange: null }

export const useVisStore = create<VisState>((set) => ({
  filters: emptyFilters,
  query: '',
  selectedId: null,
  panelOpen: false,
  activeTab: 'backdrop',
  scrollRequest: null,
  expandedBursts: [],

  playing: false,
  speed: 20,
  clockSec: null,
  following: true,

  filterDrawerOpen: false,
  skippedOpen: false,
  overviewOpen: true,
  theme: 'dark',

  toggleFilterValue: (key, value) =>
    set((s) => {
      const list = s.filters[key]
      const next = list.includes(value) ? list.filter((v) => v !== value) : [...list, value]
      return { filters: { ...s.filters, [key]: next } }
    }),
  setTimeRange: (timeRange) => set((s) => ({ filters: { ...s.filters, timeRange } })),
  setQuery: (query) => set({ query }),
  clearFilters: () => set({ filters: emptyFilters, query: '' }),

  focusEvent: (id, opts) =>
    set((s) => ({
      selectedId: id,
      panelOpen: true,
      activeTab: opts?.tab ?? s.activeTab,
      scrollRequest: { id, nonce: (s.scrollRequest?.nonce ?? 0) + 1 },
      following: false,
      clockSec:
        s.clockSec !== null && opts?.tsSec !== undefined && opts.tsSec > s.clockSec ? opts.tsSec : s.clockSec,
    })),
  selectEvent: (id) => set({ selectedId: id, panelOpen: true }),
  closePanel: () => set({ panelOpen: false }),
  setTab: (activeTab) => set({ activeTab }),
  toggleBurst: (key, open) =>
    set((s) => {
      const isOpen = s.expandedBursts.includes(key)
      const shouldOpen = open ?? !isOpen
      if (shouldOpen === isOpen) return {}
      return {
        expandedBursts: shouldOpen ? [...s.expandedBursts, key] : s.expandedBursts.filter((k) => k !== key),
      }
    }),

  setPlaying: (playing) => set(playing ? { playing, following: true } : { playing }),
  setSpeed: (speed) => set({ speed }),
  setClock: (clockSec) => set({ clockSec }),
  setFollowing: (following) => set({ following }),

  setFilterDrawerOpen: (filterDrawerOpen) => set({ filterDrawerOpen }),
  setSkippedOpen: (skippedOpen) => set({ skippedOpen }),
  setOverviewOpen: (overviewOpen) => set({ overviewOpen }),
  toggleTheme: () => set((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' })),
}))

export function activeFilterCount(filters: Filters): number {
  return filters.nodes.length + filters.families.length + filters.categories.length + (filters.timeRange ? 1 : 0)
}
