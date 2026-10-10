import { readFile } from 'node:fs/promises'
import path from 'node:path'
import type { z } from 'zod'
import {
  eventsFileSchema,
  importReportSchema,
  incidentsFileSchema,
  translationsFileSchema,
  type LoadIssue,
  type LoadResult,
} from './schemas'

const DATA_DIR = path.join(process.cwd(), 'data', process.env.VIS_DATA_DIR ?? 'mock')

async function readJson(file: string): Promise<{ value?: unknown; missing?: boolean; error?: string }> {
  try {
    const text = await readFile(path.join(DATA_DIR, file), 'utf8')
    return { value: JSON.parse(text) }
  } catch (err) {
    const e = err as NodeJS.ErrnoException
    if (e.code === 'ENOENT') return { missing: true }
    return { error: e.message }
  }
}

function parseWith<T extends z.ZodTypeAny>(
  file: string,
  schema: T,
  raw: { value?: unknown; missing?: boolean; error?: string },
  errors: LoadIssue[],
): z.infer<T> | null {
  if (raw.missing) {
    errors.push({ file, message: 'File not found', issues: [] })
    return null
  }
  if (raw.error) {
    errors.push({ file, message: `Could not read JSON: ${raw.error}`, issues: [] })
    return null
  }
  const result = schema.safeParse(raw.value)
  if (!result.success) {
    errors.push({
      file,
      message: 'Does not match the agreed schema',
      issues: result.error.issues.slice(0, 12).map((i) => ({
        path: i.path.join('.') || '(root)',
        message: i.message,
      })),
    })
    return null
  }
  return result.data
}

export async function loadDataset(): Promise<LoadResult> {
  const [eventsRaw, translationsRaw, reportRaw, incidentsRaw] = await Promise.all([
    readJson('events.json'),
    readJson('translations.json'),
    readJson('import_report.json'),
    readJson('incidents.json'),
  ])

  const errors: LoadIssue[] = []
  const events = parseWith('events.json', eventsFileSchema, eventsRaw, errors)
  const translations = parseWith('translations.json', translationsFileSchema, translationsRaw, errors)
  const report = parseWith('import_report.json', importReportSchema, reportRaw, errors)
  const incidents = incidentsRaw.missing
    ? null
    : parseWith('incidents.json', incidentsFileSchema, incidentsRaw, errors)

  if (errors.length || !events || !translations || !report) {
    return { ok: false, errors }
  }

  return {
    ok: true,
    data: { events, translations, report, incidents: incidents?.incidents ?? null },
  }
}
