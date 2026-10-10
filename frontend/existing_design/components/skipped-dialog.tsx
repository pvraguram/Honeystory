'use client'

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useVisStore } from '@/store/vis-store'
import { useDataset } from './dataset-context'
import { FamilyBadge } from './common/primitives'

export function SkippedDialog() {
  const ds = useDataset()
  const open = useVisStore((s) => s.skippedOpen)
  const setOpen = useVisStore((s) => s.setSkippedOpen)
  const { report } = ds

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-h-[85dvh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Skipped records</DialogTitle>
          <DialogDescription>
            {report.totals.skipped} of {report.totals.rowsIn} input rows could not be parsed and are not in the feed.
          </DialogDescription>
        </DialogHeader>

        <table className="w-full text-left text-xs">
          <caption className="sr-only">Rows per family</caption>
          <thead className="text-muted-foreground">
            <tr className="border-b">
              <th className="py-1.5 font-medium">Family</th>
              <th className="py-1.5 text-right font-medium">Rows in</th>
              <th className="py-1.5 text-right font-medium">Parsed</th>
              <th className="py-1.5 text-right font-medium">Skipped</th>
            </tr>
          </thead>
          <tbody className="font-mono tabular-nums">
            {Object.entries(report.byFamily).map(([fam, c]) => (
              <tr key={fam} className="border-b last:border-0">
                <td className="py-1.5">
                  <FamilyBadge family={fam} />
                </td>
                <td className="py-1.5 text-right">{c.rowsIn}</td>
                <td className="py-1.5 text-right">{c.parsed}</td>
                <td className="py-1.5 text-right">{c.skipped}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {report.skipped.length === 0 ? (
          <p className="text-sm text-muted-foreground">No rows were skipped.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {report.skipped.map((s, i) => (
              <li key={i} className="rounded-lg border bg-muted/40 p-3">
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <FamilyBadge family={s.family} />
                  {s.node && <span className="font-mono">{s.node}</span>}
                  {s.line !== undefined && <span className="font-mono text-muted-foreground">line {s.line}</span>}
                  <span className="font-medium">{s.reason}</span>
                </div>
                {s.raw && (
                  <pre className="mt-2 overflow-x-auto rounded bg-background p-2 font-mono text-[11px] whitespace-pre-wrap break-all text-muted-foreground">
                    {s.raw}
                  </pre>
                )}
              </li>
            ))}
          </ul>
        )}
      </DialogContent>
    </Dialog>
  )
}
