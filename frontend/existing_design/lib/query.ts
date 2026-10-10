import type { LogEvent } from '@/data/schemas'
import { parseClock } from './time'

export type QueryKey = 'family' | 'node' | 'category' | 'code' | 'name' | 'time' | 'flag' | 'id' | 'session'

const KEY_ALIASES: Record<string, QueryKey> = {
  family: 'family',
  fam: 'family',
  node: 'node',
  cat: 'category',
  category: 'category',
  code: 'code',
  name: 'name',
  time: 'time',
  t: 'time',
  flag: 'flag',
  id: 'id',
  session: 'session',
}

export interface ParsedQuery {
  terms: Partial<Record<QueryKey, string[]>>
  timeRanges: [number, number][]
  text: string[]
  errors: string[]
  isEmpty: boolean
}

const TOKEN = /(\w+):"([^"]*)"|(\w+):(\S+)|"([^"]*)"|(\S+)/g

export function parseQuery(input: string): ParsedQuery {
  const terms: ParsedQuery['terms'] = {}
  const timeRanges: [number, number][] = []
  const text: string[] = []
  const errors: string[] = []

  for (const m of input.matchAll(TOKEN)) {
    const rawKey = m[1] ?? m[3]
    const value = (m[2] ?? m[4] ?? '').trim()
    if (rawKey) {
      const key = KEY_ALIASES[rawKey.toLowerCase()]
      if (!key) {
        errors.push(`Unknown key "${rawKey}"`)
        continue
      }
      if (!value) continue
      if (key === 'time') {
        const [a, b = a] = value.split('-')
        const from = parseClock(a)
        const to = parseClock(b)
        if (from == null || to == null) {
          errors.push(`Bad time "${value}" (use HH:MM-HH:MM)`)
          continue
        }
        const endPad = b.split(':').length === 2 ? 59.999 : 0.999
        timeRanges.push([Math.min(from, to), Math.max(from, to) + endPad])
        continue
      }
      ;(terms[key] ??= []).push(value.toLowerCase())
    } else {
      const word = (m[5] ?? m[6] ?? '').trim()
      if (word) text.push(word.toLowerCase())
    }
  }

  return {
    terms,
    timeRanges,
    text,
    errors,
    isEmpty: !Object.keys(terms).length && !timeRanges.length && !text.length,
  }
}

export function matchesQuery(e: LogEvent, q: ParsedQuery, translation: string | null): boolean {
  if (q.isEmpty) return true
  const t = q.terms
  const lc = (s: string) => s.toLowerCase()

  if (t.family && !t.family.some((v) => lc(e.family) === v || lc(e.family).includes(v))) return false
  if (t.node && !t.node.some((v) => lc(e.node) === v || lc(e.node).includes(v))) return false
  if (t.category && !t.category.some((v) => lc(e.category).includes(v))) return false
  if (t.code && !t.code.some((v) => lc(e.code).includes(v) || lc(e.name).includes(v))) return false
  if (t.name && !t.name.some((v) => lc(e.name).includes(v))) return false
  if (t.id && !t.id.some((v) => lc(e.id).includes(v))) return false
  if (t.session && !t.session.some((v) => lc(e.session) === v)) return false
  if (t.flag && !t.flag.some((v) => e.flags.some((f) => lc(f).startsWith(v)))) return false
  if (q.timeRanges.length && !q.timeRanges.some(([a, b]) => e.tsSec >= a && e.tsSec <= b)) return false

  if (q.text.length) {
    const haystack = lc(
      [e.name, e.code, e.node, e.family, e.category, e.time24, translation ?? '', ...Object.values(e.fields).map(String)].join(' '),
    )
    if (!q.text.every((w) => haystack.includes(w))) return false
  }
  return true
}
