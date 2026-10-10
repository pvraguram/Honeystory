'use client'

import { useMemo, useState } from 'react'
import { Check, ChevronLeft, ChevronRight, Copy, X } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { Claim, Incident, LogEvent } from '@/data/schemas'
import { eventsNear, nodeStateAt, phaseAt, translationFor } from '@/lib/derive'
import { formatClock } from '@/lib/time'
import { cn } from '@/lib/utils'
import { useVisStore, type DetailTab } from '@/store/vis-store'
import { useDataset, useFeedView, useFocusEvent } from '../dataset-context'
import { CategoryBadge, EventChip, FamilyBadge, LabelTag, MissingValue, NodeBadge } from '../common/primitives'
import { FieldValueText } from '../feed/log-card'

const NEARBY_WINDOW_SEC = 60

export function DetailPanel() {
  const ds = useDataset()
  const selectedId = useVisStore((s) => s.selectedId)
  const tab = useVisStore((s) => s.activeTab)
  const setTab = useVisStore((s) => s.setTab)
  const close = useVisStore((s) => s.closePanel)
  const event = selectedId ? ds.byId.get(selectedId) : undefined

  if (!event) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center text-sm text-muted-foreground">
        Select an event to see its context.
      </div>
    )
  }

  const incidents = ds.incidentsByEvent.get(event.id) ?? []

  return (
    <div className="flex h-full min-h-0 flex-col">
      <PanelHeader event={event} onClose={close} />
      <Tabs value={tab} onValueChange={(v) => setTab(v as DetailTab)} className="flex min-h-0 flex-1 flex-col gap-0">
        <TabsList className="mx-4 mt-3 grid w-auto grid-cols-4">
          <TabsTrigger value="backdrop">Backdrop</TabsTrigger>
          <TabsTrigger value="inference">Inference</TabsTrigger>
          <TabsTrigger value="hypothesis">Hypothesis</TabsTrigger>
          <TabsTrigger value="source">Source</TabsTrigger>
        </TabsList>
        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
          <TabsContent value="backdrop" className="mt-0">
            <BackdropTab event={event} incidents={incidents} />
          </TabsContent>
          <TabsContent value="inference" className="mt-0">
            <ClaimsTab incidents={incidents} kind="inference" />
          </TabsContent>
          <TabsContent value="hypothesis" className="mt-0">
            <ClaimsTab incidents={incidents} kind="hypothesis" />
          </TabsContent>
          <TabsContent value="source" className="mt-0">
            <SourceTab event={event} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  )
}

function PanelHeader({ event, onClose }: { event: LogEvent; onClose: () => void }) {
  const ds = useDataset()
  const focus = useFocusEvent()
  const { visible } = useFeedView()
  const idx = visible.findIndex((e) => e.id === event.id)
  const prev = idx > 0 ? visible[idx - 1] : undefined
  const next = idx >= 0 && idx < visible.length - 1 ? visible[idx + 1] : undefined
  const translation = translationFor(ds, event.id)

  return (
    <header className="border-b px-4 pt-3 pb-3">
      <div className="flex items-center gap-1">
        <div className="flex flex-wrap items-center gap-1.5">
          <time className="font-mono text-sm font-semibold tabular-nums">{event.time24}</time>
          <NodeBadge node={event.node} session={event.session} />
          <FamilyBadge family={event.family} />
          <CategoryBadge category={event.category} />
        </div>
        <div className="ml-auto flex items-center">
          <button
            type="button"
            disabled={!prev}
            onClick={() => prev && focus(prev.id)}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground disabled:opacity-30"
            aria-label="Previous event"
          >
            <ChevronLeft className="size-4" />
          </button>
          <button
            type="button"
            disabled={!next}
            onClick={() => next && focus(next.id)}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground disabled:opacity-30"
            aria-label="Next event"
          >
            <ChevronRight className="size-4" />
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground"
            aria-label="Close details"
          >
            <X className="size-4" />
          </button>
        </div>
      </div>
      <h2 className="mt-2 text-base font-semibold text-balance">{event.name}</h2>
      {event.code && <p className="font-mono text-xs text-muted-foreground">{event.code}</p>}
      {translation ? (
        <p className="mt-1.5 text-sm leading-relaxed text-pretty text-foreground/85">{translation}</p>
      ) : (
        <p className="mt-1.5 text-sm">
          <MissingValue>No plain-language translation in data</MissingValue>
        </p>
      )}
    </header>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-2">
      <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{title}</h3>
      {children}
    </section>
  )
}

function BackdropTab({ event, incidents }: { event: LogEvent; incidents: Incident[] }) {
  const ds = useDataset()
  const phase = phaseAt(ds, event.tsSec)
  const nodeStates = useMemo(() => ds.nodes.map((n) => nodeStateAt(ds, n, event.tsSec)), [ds, event.tsSec])
  const nearbyFaults = useMemo(
    () => eventsNear(ds, event.tsSec, NEARBY_WINDOW_SEC, (e) => e.family === 'Fault' && e.id !== event.id).slice(0, 8),
    [ds, event],
  )
  const fields = Object.entries(event.fields)

  return (
    <div className="flex flex-col gap-6">
      <Section title="Fields">
        {fields.length ? (
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 rounded-lg border p-3 font-mono text-xs">
            {fields.map(([k, v]) => (
              <div key={k} className="contents">
                <dt className="text-muted-foreground">{k}</dt>
                <dd className="break-all">
                  <FieldValueText event={event} k={k} value={v} />
                </dd>
              </div>
            ))}
          </dl>
        ) : (
          <MissingValue>No structured fields parsed</MissingValue>
        )}
      </Section>

      <Section title="Situation at this moment">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Phase</span>
          {phase ? <span className="font-medium">{phase.name}</span> : <MissingValue />}
        </div>
        <ul className="grid gap-2 sm:grid-cols-2">
          {nodeStates.map((s) => (
            <li key={s.node} className={cn('rounded-lg border p-3 text-xs', s.node === event.node && 'border-primary/60')}>
              <div className="mb-2 flex items-center justify-between">
                <span className="font-mono font-semibold">{s.node}</span>
                {s.session ? (
                  <span className="font-mono text-muted-foreground">session {s.session}</span>
                ) : (
                  <MissingValue>no logs yet</MissingValue>
                )}
              </div>
              <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
                <dt className="text-muted-foreground">Mode</dt>
                <dd>{s.mode ?? <MissingValue />}</dd>
                <dt className="text-muted-foreground">Opposite FMS</dt>
                <dd>
                  {s.oppositeFmsOk === null ? (
                    <MissingValue />
                  ) : s.oppositeFmsOk ? (
                    <span className="text-confirmed">OK</span>
                  ) : (
                    <span className="text-fam-fault">Not OK</span>
                  )}
                </dd>
                <dt className="text-muted-foreground">Last boot</dt>
                <dd>{s.bootEvent ? <EventChip id={s.bootEvent.id} /> : <MissingValue />}</dd>
              </dl>
            </li>
          ))}
        </ul>
      </Section>

      <Section title={`Faults within ±${NEARBY_WINDOW_SEC} s`}>
        {nearbyFaults.length ? (
          <ul className="flex flex-col gap-1">
            {nearbyFaults.map((e) => (
              <li key={e.id}>
                <EventChip id={e.id} className="w-full" />
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">None.</p>
        )}
      </Section>

      <Section title="Incidents">
        {ds.incidents === null ? (
          <MissingValue>incidents.json not supplied</MissingValue>
        ) : incidents.length ? (
          <ul className="flex flex-col gap-3">
            {incidents.map((inc) => (
              <li key={inc.id} className="rounded-lg border p-3 text-sm">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium text-pretty">{inc.title}</p>
                  {inc.severity && (
                    <span className="shrink-0 rounded bg-secondary px-1.5 py-0.5 text-[10px] font-semibold uppercase">
                      {inc.severity}
                    </span>
                  )}
                </div>
                <p className="mt-1 font-mono text-xs text-muted-foreground">
                  {formatClock(inc.startSec)} – {formatClock(inc.endSec)}
                </p>
                <p className="mt-2 text-xs">
                  <span className="text-muted-foreground">Impact: </span>
                  {inc.impact ?? <MissingValue />}
                </p>
                <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
                  <span className="text-muted-foreground">Recovery:</span>
                  {inc.recoveryEventId ? <EventChip id={inc.recoveryEventId} /> : <MissingValue>none recorded</MissingValue>}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">This event is not part of any identified incident.</p>
        )}
      </Section>
    </div>
  )
}

function ClaimsTab({ incidents, kind }: { incidents: Incident[]; kind: 'inference' | 'hypothesis' }) {
  const ds = useDataset()
  if (ds.incidents === null) return <MissingValue>incidents.json not supplied, so no {kind} is available.</MissingValue>
  const withClaims = incidents.filter((i) => i[kind].length > 0)
  if (!withClaims.length) {
    return (
      <p className="text-sm text-muted-foreground">
        {incidents.length ? `No ${kind} recorded for this event's incident.` : `This event has no ${kind} in the data.`}
      </p>
    )
  }
  return (
    <div className="flex flex-col gap-6">
      {kind === 'hypothesis' && (
        <p className="rounded-lg border border-probable/40 bg-probable/10 p-3 text-xs text-pretty">
          Hypotheses are explanations that fit the evidence but are not proven by the log.
        </p>
      )}
      {withClaims.map((inc) => (
        <section key={inc.id} className="flex flex-col gap-3">
          {withClaims.length > 1 && <h3 className="text-sm font-semibold">{inc.title}</h3>}
          <ol className="flex flex-col gap-3">
            {inc[kind].map((c, i) => (
              <ClaimItem key={i} claim={c} tab={kind} />
            ))}
          </ol>
        </section>
      ))}
    </div>
  )
}

function ClaimItem({ claim, tab }: { claim: Claim; tab: DetailTab }) {
  return (
    <li className="rounded-lg border p-3">
      <div className="mb-1.5">
        <LabelTag label={claim.label} />
      </div>
      <p className="text-sm leading-relaxed text-pretty">{claim.text}</p>
      {claim.citations.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {claim.citations.map((id) => (
            <EventChip key={id} id={id} tab={tab} />
          ))}
        </div>
      ) : (
        <p className="mt-2 text-xs">
          <MissingValue>No supporting event cited</MissingValue>
        </p>
      )}
    </li>
  )
}

function SourceTab({ event }: { event: LogEvent }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(event.rawHtml)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div className="flex flex-col gap-6">
      <Section title="Record">
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 rounded-lg border p-3 font-mono text-xs">
          <dt className="text-muted-foreground">id</dt>
          <dd className="break-all">{event.id}</dd>
          <dt className="text-muted-foreground">session</dt>
          <dd>{event.session}</dd>
          <dt className="text-muted-foreground">seq</dt>
          <dd>{event.seq}</dd>
          <dt className="text-muted-foreground">tsSec</dt>
          <dd>{event.tsSec}</dd>
          <dt className="text-muted-foreground">flags</dt>
          <dd>{event.flags.length ? event.flags.join(', ') : <span className="text-muted-foreground">none</span>}</dd>
        </dl>
      </Section>

      <Section title="Raw source">
        <div className="relative">
          <button
            type="button"
            onClick={copy}
            className="absolute top-2 right-2 rounded-md border bg-card p-1.5 text-muted-foreground hover:text-foreground"
            aria-label="Copy raw source"
          >
            {copied ? <Check className="size-3.5 text-confirmed" /> : <Copy className="size-3.5" />}
          </button>
          <pre className="max-h-80 overflow-auto rounded-lg border bg-muted/40 p-3 pr-10 font-mono text-[11px] leading-relaxed whitespace-pre-wrap break-all">
            {event.rawHtml}
          </pre>
        </div>
      </Section>

      <Section title="Parser notes">
        {event.parseNotes.length ? (
          <ul className="flex list-disc flex-col gap-1 pl-4 text-xs">
            {event.parseNotes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">None.</p>
        )}
      </Section>
    </div>
  )
}
