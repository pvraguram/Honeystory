import type { LogEvent, Translations } from '@/data/schemas'

const CSV_COLUMNS = ['id', 'time24', 'tsSec', 'node', 'session', 'seq', 'family', 'category', 'code', 'name', 'translation', 'flags', 'fields'] as const

const escapeCsv = (v: string) => (/[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v)

export function toCsv(events: LogEvent[], translations: Translations): string {
  const lines = [CSV_COLUMNS.join(',')]
  for (const e of events) {
    const row: Record<(typeof CSV_COLUMNS)[number], string> = {
      id: e.id,
      time24: e.time24,
      tsSec: String(e.tsSec),
      node: e.node,
      session: e.session,
      seq: String(e.seq),
      family: e.family,
      category: e.category,
      code: e.code,
      name: e.name,
      translation: translations[e.id] ?? '',
      flags: e.flags.join(';'),
      fields: JSON.stringify(e.fields),
    }
    lines.push(CSV_COLUMNS.map((c) => escapeCsv(row[c])).join(','))
  }
  return lines.join('\n')
}

export function toJson(events: LogEvent[], translations: Translations): string {
  return JSON.stringify(
    events.map((e) => ({ ...e, translation: translations[e.id] ?? null })),
    null,
    2,
  )
}

export function downloadText(filename: string, text: string, mime: string) {
  const blob = new Blob([text], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
