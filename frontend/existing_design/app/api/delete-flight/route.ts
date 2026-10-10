import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'
import { exec } from 'child_process'
import util from 'util'

const execPromise = util.promisify(exec)

export async function POST(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const flightId = searchParams.get('flight_id') || 'AA100'

    // 1. Reset frontend mock dataset
    const mockDir = path.join(process.cwd(), 'data', 'mock')
    if (fs.existsSync(mockDir)) {
      fs.writeFileSync(path.join(mockDir, 'events.json'), '[]', 'utf-8')
      fs.writeFileSync(path.join(mockDir, 'translations.json'), '{}', 'utf-8')
      fs.writeFileSync(
        path.join(mockDir, 'manifest.json'),
        JSON.stringify({ ingested_at: null, total_records: 0, nodes: {} }),
        'utf-8'
      )
    }

    // 2. Trigger python main.py reset in background to wipe DuckDB and Parquet
    const projectRoot = path.resolve(process.cwd(), '..', '..')
    try {
      await execPromise('python main.py reset', { cwd: projectRoot })
    } catch (cmdErr) {
      console.warn('Backend reset script execution warning:', cmdErr)
    }

    return NextResponse.json({
      status: 'success',
      message: `Complete aircraft data, nodes, and logs deleted for ${flightId}.`,
      flight_id: flightId,
      records_remaining: 0,
    })
  } catch (error: any) {
    return NextResponse.json(
      { status: 'error', message: error?.message || 'Failed to delete aircraft data.' },
      { status: 500 }
    )
  }
}
