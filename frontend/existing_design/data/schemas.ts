import { z } from 'zod'

const stringOrList = z
  .union([z.string(), z.array(z.string())])
  .nullish()
  .transform((v) => (v == null ? [] : Array.isArray(v) ? v : v ? [v] : []))

export const fieldValueSchema = z.union([z.string(), z.number(), z.boolean(), z.null()])

export const eventSchema = z.object({
  id: z.string(),
  family: z.string(),
  node: z.string(),
  session: z.union([z.number(), z.string()]).transform(String),
  seq: z.number(),
  time24: z.string(),
  tsSec: z.number(),
  category: z.string(),
  name: z.string(),
  code: z.string().nullish().transform((v) => v ?? ''),
  fields: z.record(z.string(), fieldValueSchema).default({}),
  flags: stringOrList,
  rawHtml: z.string(),
  parseNotes: stringOrList,
})

export const eventsFileSchema = z.array(eventSchema)

export const translationsFileSchema = z.record(z.string(), z.string())

export const skippedRecordSchema = z.object({
  family: z.string(),
  node: z.string().optional(),
  line: z.number().optional(),
  reason: z.string(),
  raw: z.string().optional(),
})

export const importReportSchema = z.object({
  generatedAt: z.string().optional(),
  source: z.string().optional(),
  totals: z.object({
    rowsIn: z.number(),
    events: z.number(),
    skipped: z.number(),
  }),
  byFamily: z.record(
    z.string(),
    z.object({ rowsIn: z.number(), parsed: z.number(), skipped: z.number() }),
  ),
  skipped: z.array(skippedRecordSchema),
})

export const claimSchema = z.object({
  text: z.string(),
  label: z.enum(['confirmed', 'probable', 'missing']),
  citations: z.array(z.string()).default([]),
})

export const incidentSchema = z.object({
  id: z.string(),
  title: z.string(),
  severity: z.string().optional(),
  startSec: z.number(),
  endSec: z.number(),
  eventIds: z.array(z.string()).default([]),
  impact: z.string().nullish(),
  recoveryEventId: z.string().nullish(),
  inference: z.array(claimSchema).default([]),
  hypothesis: z.array(claimSchema).default([]),
})

export const incidentsFileSchema = z.object({
  incidents: z.array(incidentSchema),
})

export type LogEvent = z.infer<typeof eventSchema>
export type FieldValue = z.infer<typeof fieldValueSchema>
export type Translations = z.infer<typeof translationsFileSchema>
export type ImportReport = z.infer<typeof importReportSchema>
export type SkippedRecord = z.infer<typeof skippedRecordSchema>
export type Claim = z.infer<typeof claimSchema>
export type Incident = z.infer<typeof incidentSchema>

export interface RawDataset {
  events: LogEvent[]
  translations: Translations
  report: ImportReport
  incidents: Incident[] | null
}

export interface LoadIssue {
  file: string
  message: string
  issues: { path: string; message: string }[]
}

export type LoadResult = { ok: true; data: RawDataset } | { ok: false; errors: LoadIssue[] }
