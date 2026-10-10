'use client'

import { ChevronDown, Layers, RotateCw } from 'lucide-react'
import type { LogEvent } from '@/data/schemas'
import type { Reboot } from '@/lib/derive'
import { familyStyle } from '@/lib/families'
import { formatDuration } from '@/lib/time'
import { cn } from '@/lib/utils'
import { FamilyBadge, NodeBadge } from '../common/primitives'

export function SessionDivider({ reboot, onSelect }: { reboot: Reboot; onSelect: (id: string) => void }) {
  return (
    <div className="flex items-center gap-3 py-2" role="separator" aria-label={`${reboot.node} ${reboot.label}`}>
      <span className="h-px flex-1 bg-fam-fault/50" aria-hidden />
      <button
        type="button"
        onClick={() => onSelect(reboot.eventId)}
        className="inline-flex items-center gap-1.5 rounded-full border border-fam-fault/50 bg-fam-fault/10 px-3 py-1 text-xs font-medium text-fam-fault hover:bg-fam-fault/20"
      >
        <RotateCw className="size-3.5" aria-hidden />
        <span className="font-mono">{reboot.time24}</span>
        {reboot.node} {reboot.label} · session {reboot.session}
      </button>
      <span className="h-px flex-1 bg-fam-fault/50" aria-hidden />
    </div>
  )
}

export function BurstCard({
  burstKey,
  events,
  expanded,
  selected,
  onToggle,
  onSelect,
}: {
  burstKey: string
  events: LogEvent[]
  expanded: boolean
  selected: boolean
  onToggle: (key: string) => void
  onSelect: (id: string) => void
}) {
  const first = events[0]
  const last = events[events.length - 1]
  const color = familyStyle(first.family).color
  return (
    <div
      className={cn(
        'relative flex items-center gap-2 rounded-lg border border-dashed bg-card/60 py-2 pr-2 pl-4',
        selected && 'border-primary ring-1 ring-primary',
      )}
    >
      <span className="absolute inset-y-2 left-1.5 w-1 rounded-full" style={{ backgroundColor: color }} aria-hidden />
      <button type="button" onClick={() => onSelect(first.id)} className="flex min-w-0 flex-1 flex-wrap items-center gap-1.5 text-left">
        <Layers className="size-3.5 text-muted-foreground" aria-hidden />
        <span className="font-mono text-xs font-medium tabular-nums">{first.time24}</span>
        <NodeBadge node={first.node} session={first.session} />
        <FamilyBadge family={first.family} />
        <span className="truncate text-sm font-semibold">{first.name}</span>
        <span className="rounded-full bg-secondary px-2 py-0.5 font-mono text-[11px] font-semibold">×{events.length}</span>
        <span className="text-[11px] text-muted-foreground">within {formatDuration(last.tsSec - first.tsSec) || '<1 s'}</span>
      </button>
      <button
        type="button"
        onClick={() => onToggle(burstKey)}
        aria-expanded={expanded}
        className="inline-flex shrink-0 items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
      >
        {expanded ? 'Collapse' : 'Expand'}
        <ChevronDown className={cn('size-3.5 transition-transform', expanded && 'rotate-180')} aria-hidden />
      </button>
    </div>
  )
}
