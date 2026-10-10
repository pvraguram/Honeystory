'use client'

import { useState } from 'react'
import {
  Check,
  Copy,
  ExternalLink,
  FileCode,
  Info,
  Layers,
  X,
} from 'lucide-react'
import type { EventRecordNode } from '@/lib/flight-tree'

interface EventInspectorProps {
  event: EventRecordNode | null
  onClose: () => void
}

export function EventInspector({ event, onClose }: EventInspectorProps) {
  const [copied, setCopied] = useState(false)

  if (!event) return null

  const rawLogPreview = event.rawHtml || Object.entries(event.fields || {}).map(([k, v]) => `${k}: ${v}`).join('\n')

  const copyRawLog = async () => {
    await navigator.clipboard.writeText(rawLogPreview)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const fieldsEntries = Object.entries(event.fields || {})

  return (
    <aside
      aria-label="Event Inspector"
      className="flex h-full w-[420px] shrink-0 flex-col border-l border-slate-200 bg-white shadow-xs select-none z-20"
    >
      {/* Inspector Header */}
      <div className="flex items-start justify-between border-b border-slate-200 p-4 bg-slate-50/50">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-semibold text-slate-500">#{event.number}</span>
            <span className="font-mono text-xs text-slate-700">{event.time24}</span>
            {event.eventCode && (
              <span className="rounded bg-slate-200/80 px-1.5 py-0.2 font-mono text-[10px] text-slate-700">
                {event.eventCode}
              </span>
            )}
          </div>
          <h2 className="mt-1 text-sm font-bold text-slate-900 leading-snug">{event.eventName}</h2>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-800 transition-colors"
          aria-label="Close inspector"
        >
          <X className="size-4" />
        </button>
      </div>

      {/* Inspector Body */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-5 text-xs">
        {/* Core Metadata Bar */}
        <div className="grid grid-cols-2 gap-2 rounded border border-slate-200 bg-slate-50/40 p-3 text-xs">
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-bold block">Subsystem Node</span>
            <span className="font-semibold text-slate-800 font-mono">{event.node}</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-bold block">Log Family</span>
            <span className="font-semibold text-slate-800 truncate block">{event.family}</span>
          </div>
          <div className="mt-1">
            <span className="text-[10px] text-slate-400 uppercase font-bold block">Ingestion Status</span>
            <div className="flex items-center gap-1.5 font-medium text-emerald-700">
              <span className="size-1.5 rounded-full bg-emerald-500" />
              <span>Ingested & Valid</span>
            </div>
          </div>
          <div className="mt-1">
            <span className="text-[10px] text-slate-400 uppercase font-bold block">Timestamp</span>
            <span className="font-mono text-slate-700">{event.timestampNormalized}</span>
          </div>
        </div>

        {/* Plain Language Decoded Translation */}
        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
            Event Description & Interpretation
          </span>
          <div className="rounded border border-slate-200 bg-white p-3 text-xs leading-relaxed text-slate-800 shadow-2xs">
            {event.translation || (
              <span className="text-slate-500 italic">
                Decoded telemetry event registered from {event.node} during {event.family} logging cycle.
              </span>
            )}
          </div>
        </div>

        {/* Parsed Fields Grid */}
        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
            Parsed Telemetry Parameters ({fieldsEntries.length})
          </span>
          {fieldsEntries.length > 0 ? (
            <div className="rounded border border-slate-200 bg-white divide-y divide-slate-100 max-h-56 overflow-y-auto font-mono text-[11px]">
              {fieldsEntries.map(([k, v]) => (
                <div key={k} className="flex justify-between items-center py-1.5 px-3">
                  <span className="text-slate-500 truncate mr-2">{k}</span>
                  <span className="font-semibold text-slate-900 truncate max-w-[200px]" title={String(v)}>
                    {String(v)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No structured key-value attributes in record.</p>
          )}
        </div>

        {/* Source File Provenance */}
        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
            Source Provenance
          </span>
          <div className="rounded border border-slate-200 bg-slate-50/50 p-2.5 text-[11px] font-mono text-slate-700">
            <div className="flex items-center gap-1.5 text-slate-600 truncate">
              <FileCode className="size-3.5 shrink-0" />
              <span className="truncate">{event.node}_Report.html</span>
            </div>
            <div className="mt-1 text-[10px] text-slate-400">
              Event UUID: <span className="select-all text-slate-600">{event.id}</span>
            </div>
          </div>
        </div>

        {/* Raw Decoded Log Record */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Raw HTML Log
            </span>
            <button
              type="button"
              onClick={copyRawLog}
              className="flex items-center gap-1 text-[11px] font-medium text-slate-600 hover:text-slate-900"
            >
              {copied ? (
                <>
                  <Check className="size-3 text-emerald-600" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="size-3" />
                  Copy Log
                </>
              )}
            </button>
          </div>
          <pre className="rounded border border-slate-200 bg-slate-900 text-slate-100 p-3 font-mono text-[10px] leading-relaxed max-h-48 overflow-auto whitespace-pre-wrap">
            {rawLogPreview}
          </pre>
        </div>
      </div>
    </aside>
  )
}
