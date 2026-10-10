import { FileWarning } from 'lucide-react'
import type { LoadIssue } from '@/data/schemas'

export function LoadErrorScreen({ errors }: { errors: LoadIssue[] }) {
  return (
    <main className="mx-auto flex min-h-dvh max-w-2xl flex-col justify-center gap-6 p-6">
      <div className="flex items-center gap-3">
        <FileWarning className="size-8 text-destructive" aria-hidden />
        <div>
          <h1 className="text-xl font-semibold text-balance">The log data could not be loaded</h1>
          <p className="text-sm text-muted-foreground">
            One or more input files is missing or does not match the expected schema.
          </p>
        </div>
      </div>
      <ul className="flex flex-col gap-3">
        {errors.map((err) => (
          <li key={err.file} className="rounded-lg border bg-card p-4">
            <p className="font-mono text-sm font-semibold">{err.file}</p>
            <p className="mt-1 text-sm">{err.message}</p>
            {err.issues.length > 0 && (
              <ul className="mt-3 flex flex-col gap-1 font-mono text-xs text-muted-foreground">
                {err.issues.slice(0, 20).map((issue, i) => (
                  <li key={i}>
                    <span className="text-destructive">{issue.path || '(root)'}</span>: {issue.message}
                  </li>
                ))}
                {err.issues.length > 20 && <li>…and {err.issues.length - 20} more</li>}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </main>
  )
}
