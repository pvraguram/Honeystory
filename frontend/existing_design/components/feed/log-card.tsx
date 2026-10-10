'use client'

import { memo } from 'react'
import { AlertCircle, Link2 } from 'lucide-react'
import type { FieldValue, LogEvent } from '@/data/schemas'
import { familyStyle } from '@/lib/families'
import { cn } from '@/lib/utils'
import { CategoryBadge, FamilyBadge, NodeBadge } from '../common/primitives'

export function fieldFlag(event: LogEvent, key: string): 'invalid' | 'na' | null {
  if (event.flags.includes(`invalid:${key}`)) return 'invalid'
  if (event.flags.includes(`na:${key}`)) return 'na'
  return null
}

export function FieldValueText({ event, k, value }: { event: LogEvent; k: string; value: FieldValue }) {
  const flag = fieldFlag(event, k)
  if (value === null || flag === 'na') return <span className="text-missing italic">N/A</span>
  return (
    <span className={cn(flag === 'invalid' && 'underline-invalid')} title={flag === 'invalid' ? 'Value flagged invalid by the parser' : undefined}>
      {String(value)}
    </span>
  )
}

interface LogCardProps {
  event: LogEvent
  translation: string | null
  selected: boolean
  isNew: boolean
  incidentCount: number
  indented?: boolean
  onSelect: (id: string) => void
}

export const LogCard = memo(function LogCard({
  event,
  translation,
  selected,
  isNew,
  incidentCount,
  indented,
  onSelect,
}: LogCardProps) {
  const color = familyStyle(event.family).color
  const fieldEntries = Object.entries(event.fields)
  const hasInvalid = event.flags.some((f) => f.startsWith('invalid:'))

  return (
    <article
      aria-selected={selected}
      className={cn(
        'group relative cursor-pointer rounded-lg border bg-card py-2.5 pr-3 pl-4 transition-colors hover:border-foreground/20',
        selected && 'border-primary ring-1 ring-primary',
        indented && 'ml-6',
        isNew && 'animate-in fade-in slide-in-from-bottom-1 duration-300',
      )}
      onClick={() => onSelect(event.id)}
    >
      <span className="absolute inset-y-2 left-1.5 w-1 rounded-full" style={{ backgroundColor: color }} aria-hidden />
      <header className="flex flex-wrap items-center gap-1.5">
        <time className="font-mono text-xs font-medium tabular-nums">{event.time24}</time>
        <NodeBadge node={event.node} session={event.session} />
        <FamilyBadge family={event.family} />
        <CategoryBadge category={event.category} />
        {event.code && <span className="font-mono text-[11px] text-muted-foreground">{event.code}</span>}
        <span className="ml-auto flex items-center gap-1.5">
          {hasInvalid && (
            <AlertCircle className="size-3.5 text-fam-fault" aria-label="Contains values flagged invalid" />
          )}
          {incidentCount > 0 && (
            <span className="inline-flex items-center gap-0.5 text-[11px] text-muted-foreground" title="Part of an incident">
              <Link2 className="size-3" aria-hidden />
              {incidentCount}
            </span>
          )}
        </span>
      </header>

      <h3 className="mt-1.5 text-sm font-semibold">
        <button
          type="button"
          className="text-left focus-visible:underline focus-visible:outline-none"
          onClick={(e) => {
            e.stopPropagation()
            onSelect(event.id)
          }}
        >
          {event.name}
        </button>
      </h3>

      {translation ? (
        <p className="mt-0.5 text-[13px] leading-relaxed text-pretty text-foreground/85">{translation}</p>
      ) : (
        <p className="mt-0.5 text-[13px] text-missing italic">No plain-language translation in data</p>
      )}

      {fieldEntries.length > 0 && (
        <dl className="mt-2 flex flex-wrap gap-x-3 gap-y-0.5 font-mono text-[11px]">
          {fieldEntries.map(([k, v]) => (
            <div key={k} className="flex gap-1">
              <dt className="text-muted-foreground">{k}</dt>
              <dd>
                <FieldValueText event={event} k={k} value={v} />
              </dd>
            </div>
          ))}
        </dl>
      )}
    </article>
  )
})
