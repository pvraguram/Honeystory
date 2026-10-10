const pad = (n: number) => String(n).padStart(2, '0')

export function formatClock(sec: number, withSeconds = true): string {
  const s = Math.max(0, Math.floor(sec))
  const h = Math.floor(s / 3600) % 24
  const m = Math.floor((s % 3600) / 60)
  return withSeconds ? `${pad(h)}:${pad(m)}:${pad(s % 60)}` : `${pad(h)}:${pad(m)}`
}

export function formatDuration(sec: number): string {
  if (!Number.isFinite(sec) || sec < 0) return '—'
  if (sec < 1) return `${Math.round(sec * 1000)} ms`
  if (sec < 60) return `${Math.round(sec * 10) / 10} s`
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  if (m < 60) return s ? `${m} min ${s} s` : `${m} min`
  return `${Math.floor(m / 60)} h ${m % 60} min`
}

/** Parses "HH:MM" or "HH:MM:SS" into seconds since midnight. */
export function parseClock(text: string): number | null {
  const match = /^(\d{1,2}):(\d{2})(?::(\d{2}))?$/.exec(text.trim())
  if (!match) return null
  const [, h, m, s] = match
  const hh = Number(h)
  const mm = Number(m)
  const ss = s ? Number(s) : 0
  if (hh > 23 || mm > 59 || ss > 59) return null
  return hh * 3600 + mm * 60 + ss
}
