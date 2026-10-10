'use client'

import { forwardRef } from 'react'
import { Moon, Plane, Search, SlidersHorizontal, Sun, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { activeFilterCount, useVisStore } from '@/store/vis-store'
import { useDataset, useFocusEvent } from './dataset-context'

export const TopBar = forwardRef<HTMLInputElement>(function TopBar(_, searchRef) {
  const ds = useDataset()
  const focus = useFocusEvent()
  const query = useVisStore((s) => s.query)
  const setQuery = useVisStore((s) => s.setQuery)
  const filters = useVisStore((s) => s.filters)
  const setDrawer = useVisStore((s) => s.setFilterDrawerOpen)
  const theme = useVisStore((s) => s.theme)
  const toggleTheme = useVisStore((s) => s.toggleTheme)
  const filterCount = activeFilterCount(filters)

  return (
    <header className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b bg-card/60 px-4 py-2.5 backdrop-blur">
      <div className="flex items-center gap-2.5">
        <span className="flex size-8 items-center justify-center rounded-lg bg-primary/15 text-primary">
          <Plane className="size-4" aria-hidden />
        </span>
        <div className="leading-tight">
          <h1 className="text-sm font-semibold">FMS Log Visualiser</h1>
          {ds.route ? (
            <button
              type="button"
              onClick={() => focus(ds.route!.eventId)}
              className="font-mono text-xs text-muted-foreground hover:text-foreground"
            >
              {ds.route.origin} → {ds.route.destination}
            </button>
          ) : (
            <p className="text-xs text-muted-foreground">Route not in data</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1 rounded-lg border bg-muted/30 p-0.5 text-xs">
        <button
          type="button"
          onClick={() => useVisStore.setState((s) => ({ filters: { ...s.filters, nodes: [] } }))}
          className={cn(
            "rounded px-2.5 py-1 font-mono text-xs transition-colors",
            filters.nodes.length === 0
              ? "bg-primary font-semibold text-primary-foreground shadow-xs"
              : "text-muted-foreground hover:bg-accent hover:text-foreground"
          )}
        >
          ALL NODES
        </button>
        {ds.nodes.map((n) => {
          const isSelected = filters.nodes.length === 1 && filters.nodes[0] === n
          return (
            <button
              key={n}
              type="button"
              onClick={() => useVisStore.setState((s) => ({ filters: { ...s.filters, nodes: [n] } }))}
              className={cn(
                "rounded px-2.5 py-1 font-mono text-xs transition-colors",
                isSelected
                  ? "bg-primary font-semibold text-primary-foreground shadow-xs"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
            >
              {n}
            </button>
          )
        })}
      </div>

      <div className="relative order-last w-full sm:order-none sm:w-auto sm:flex-1">
        <label htmlFor="log-search" className="sr-only">
          Search or query the log
        </label>
        <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
        <input
          ref={searchRef}
          id="log-search"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder='Search… e.g. family:fault code:"Dual State Trans Timeout" time:11:40-11:50'
          className="h-9 w-full rounded-lg border bg-background pr-16 pl-9 font-mono text-[13px] placeholder:font-sans placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          autoComplete="off"
          spellCheck={false}
        />
        <div className="absolute top-1/2 right-2 flex -translate-y-1/2 items-center gap-1">
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="rounded p-1 text-muted-foreground hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="size-3.5" />
            </button>
          )}
          <kbd className="hidden rounded border px-1.5 font-mono text-[10px] text-muted-foreground sm:inline">/</kbd>
        </div>
      </div>

      <div className="ml-auto flex items-center gap-2 sm:ml-0">
        <Button variant="outline" size="sm" onClick={() => setDrawer(true)} className="gap-1.5">
          <SlidersHorizontal className="size-4" aria-hidden />
          Filters
          {filterCount > 0 && (
            <span className="rounded-full bg-primary px-1.5 text-[10px] font-semibold text-primary-foreground">
              {filterCount}
            </span>
          )}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          {theme === 'dark' ? <Sun className="size-4" /> : <Moon className="size-4" />}
        </Button>
      </div>
    </header>
  )
})
