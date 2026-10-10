import {
  AlertOctagon,
  Activity,
  Cpu,
  MessagesSquare,
  Navigation,
  Power,
  type LucideIcon,
} from 'lucide-react'

export interface FamilyStyle {
  label: string
  color: string
  icon: LucideIcon
}

// SYS is a placeholder for the fifth family until the ingestion team confirms its name and colour.
const FAMILIES: Record<string, FamilyStyle> = {
  Fault: { label: 'Fault', color: 'var(--fam-fault)', icon: AlertOctagon },
  CI_BPQ: { label: 'CI_BPQ', color: 'var(--fam-ci)', icon: MessagesSquare },
  LBPQ: { label: 'LBPQ', color: 'var(--fam-lbpq)', icon: Navigation },
  STATE: { label: 'STATE', color: 'var(--fam-state)', icon: Activity },
  SYS: { label: 'SYS', color: 'var(--fam-other)', icon: Power },
}

const FALLBACK: Omit<FamilyStyle, 'label'> = { color: 'var(--fam-other)', icon: Cpu }

export const FAMILY_ORDER = ['Fault', 'CI_BPQ', 'LBPQ', 'STATE', 'SYS']

export function familyStyle(family: string): FamilyStyle {
  return FAMILIES[family] ?? { label: family, ...FALLBACK }
}

export function sortFamilies(families: string[]): string[] {
  return [...families].sort((a, b) => {
    const ia = FAMILY_ORDER.indexOf(a)
    const ib = FAMILY_ORDER.indexOf(b)
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib) || a.localeCompare(b)
  })
}
