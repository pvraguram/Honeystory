'use client'

import {
  AlertTriangle,
  LifeBuoy,
  Map as MapIcon,
  Navigation,
  Power,
  Tag,
  ToggleRight,
  User,
  type LucideIcon,
} from 'lucide-react'
import type { Claim } from '@/data/schemas'
import { familyStyle } from '@/lib/families'
import { cn } from '@/lib/utils'
import { useDataset, useFocusEvent } from '../dataset-context'
import type { DetailTab } from '@/store/vis-store'

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  fault: AlertTriangle,
  operator: User,
  state: ToggleRight,
  guidance: Navigation,
  planning: MapIcon,
  boot: Power,
  recovery: LifeBuoy,
}

export function CategoryBadge({ category, className }: { category: string; className?: string }) {
  const Icon = CATEGORY_ICONS[category] ?? Tag
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[11px] font-medium capitalize text-muted-foreground',
        className,
      )}
    >
      <Icon className="size-3" aria-hidden />
      {category}
    </span>
  )
}

export function NodeBadge({ node, session }: { node: string; session?: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 font-mono text-[11px] font-medium text-secondary-foreground">
      {node}
      {session && <span className="text-muted-foreground">·s{session}</span>}
    </span>
  )
}

export function FamilyBadge({ family }: { family: string }) {
  const style = familyStyle(family)
  const Icon = style.icon
  return (
    <span
      className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-semibold"
      style={{ color: style.color, backgroundColor: `color-mix(in oklab, ${style.color} 14%, transparent)` }}
    >
      <Icon className="size-3" aria-hidden />
      {style.label}
    </span>
  )
}

const LABEL_STYLES: Record<Claim['label'], { text: string; color: string }> = {
  confirmed: { text: 'Confirmed', color: 'var(--label-confirmed)' },
  probable: { text: 'Probable', color: 'var(--label-probable)' },
  missing: { text: 'Missing', color: 'var(--label-missing)' },
}

export function LabelTag({ label }: { label: Claim['label'] }) {
  const s = LABEL_STYLES[label]
  return (
    <span
      className={cn(
        'inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide',
        label === 'missing' && 'border-dashed',
      )}
      style={{ color: s.color, borderColor: `color-mix(in oklab, ${s.color} 45%, transparent)` }}
    >
      {s.text}
    </span>
  )
}

/** Clickable reference to a log event. Every claim and related-event list uses this. */
export function EventChip({ id, tab, className }: { id: string; tab?: DetailTab; className?: string }) {
  const ds = useDataset()
  const focus = useFocusEvent()
  const event = ds.byId.get(id)
  if (!event) {
    return (
      <span
        className="inline-flex items-center gap-1 rounded-md border border-dashed px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground"
        title="This citation does not match any loaded event"
      >
        {id} · not found
      </span>
    )
  }
  const color = familyStyle(event.family).color
  return (
    <button
      type="button"
      onClick={() => focus(id, tab)}
      className={cn(
        'inline-flex max-w-full items-center gap-1.5 rounded-md border bg-card px-1.5 py-0.5 text-left text-[11px] transition-colors hover:border-primary hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
        className,
      )}
      title={`Go to ${event.node} ${event.time24} ${event.name}`}
    >
      <span className="size-1.5 shrink-0 rounded-full" style={{ backgroundColor: color }} aria-hidden />
      <span className="font-mono text-muted-foreground">{event.time24}</span>
      <span className="font-mono">{event.node}</span>
      <span className="truncate">{event.name}</span>
    </button>
  )
}

export function MissingValue({ children = 'Not in data' }: { children?: React.ReactNode }) {
  return <span className="text-missing italic">{children}</span>
}
