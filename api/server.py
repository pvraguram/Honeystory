"""
FlightStory AI — Backend API Bridge for React Frontend.

Exposes REST API endpoints connecting the React UI to the Ingestion Engine
and DuckDB analytical layer.
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

import duckdb
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flightstory.config import DUCKDB_PATH, INPUT_HTML_DIR, ensure_data_dirs
from flightstory.orchestrator import IngestionOrchestrator
from flightstory.storage import init_duckdb, query_record_counts

log = logging.getLogger("flightstory.api")

app = FastAPI(
    title="FlightStory AI API",
    description="Backend API connecting React UI to FlightStory Ingestion & DuckDB analytical layer",
    version="0.1.0",
)

# Enable CORS for React dev servers (Vite: 5173, CRA: 3000, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    ensure_data_dirs()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "FlightStory AI Engine API"}


@app.get("/api/status")
def get_system_status():
    """Return stored records per node and latest manifest summary."""
    try:
        conn = init_duckdb()
        counts = query_record_counts(conn)
        conn.close()
    except Exception as exc:
        counts = {}
        log.warning("Could not read DuckDB counts: %s", exc)

    from flightstory.config import MANIFESTS_DIR
    manifests = sorted(MANIFESTS_DIR.glob("*.json"), reverse=True)
    latest_run = None
    if manifests:
        try:
            latest_run = json.loads(manifests[0].read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "status": "ready",
        "nodes": counts,
        "total_records": sum(counts.values()),
        "latest_run": latest_run,
    }


@app.post("/api/upload-and-ingest")
async def upload_and_ingest(
    files: list[UploadFile] = File(...),
    flight_id: str = Query("AA100", description="Target flight identifier (e.g. AA100)"),
    workers: int | None = Query(None, description="Parallel worker count (auto-tuned if omitted)"),
    force: bool = Query(False, description="Reprocess files even if unchanged"),
):
    """
    Receive uploaded HTML aircraft log files, save them to data/input_html,
    and trigger parallel ingestion segregated by node and flight.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    saved_files: list[str] = []
    INPUT_HTML_DIR.mkdir(parents=True, exist_ok=True)

    for file in files:
        if not file.filename.lower().endswith((".html", ".htm")):
            continue
        dest_path = INPUT_HTML_DIR / file.filename
        with dest_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)

    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid .html or .htm files received")

    orchestrator = IngestionOrchestrator(
        input_dir=INPUT_HTML_DIR,
        force_reprocess=force,
        workers=workers,
    )
    manifest = orchestrator.run()

    return {
        "status": manifest.status,
        "run_id": manifest.run_id,
        "flight_id": flight_id,
        "files_uploaded": len(saved_files),
        "files_processed": manifest.files_success,
        "files_failed": manifest.files_failed,
        "records_extracted": manifest.total_records_extracted,
        "records_stored": manifest.total_records_stored,
        "outcomes": [
            {
                "filename": o.filename,
                "node_id": o.node_id,
                "status": o.status,
                "records": o.records_stored,
                "error": o.error,
            }
            for o in manifest.file_outcomes
        ],
    }


@app.get("/api/records")
def get_records(
    node_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
):
    """
    Query records across all nodes or a specific node from DuckDB.
    """
    if not DUCKDB_PATH.exists():
        return {"total": 0, "records": []}

    conn = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        where_clauses = []
        if node_id:
            where_clauses.append(f"node_id = '{node_id.upper()}'")
        if search:
            escaped_search = search.replace("'", "''")
            where_clauses.append(f"(original_record ILIKE '%{escaped_search}%' OR timestamp_raw ILIKE '%{escaped_search}%')")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        count_sql = f"SELECT COUNT(*) FROM all_records {where_sql}"
        total = conn.execute(count_sql).fetchone()[0]

        query_sql = f"""
            SELECT 
                event_id, 
                node_id, 
                source_file, 
                source_table_id, 
                source_row_number, 
                timestamp_raw, 
                timestamp_normalized, 
                timestamp_parse_status, 
                original_record
            FROM all_records
            {where_sql}
            ORDER BY timestamp_normalized ASC NULLS LAST
            LIMIT {limit} OFFSET {offset}
        """
        rows = conn.execute(query_sql).fetchall()

        records = []
        for r in rows:
            try:
                parsed_orig = json.loads(r[8])
            except Exception:
                parsed_orig = r[8]

            records.append({
                "event_id": r[0],
                "node_id": r[1],
                "source_file": Path(r[2]).name if r[2] else "",
                "source_table_id": r[3],
                "row_number": r[4],
                "timestamp_raw": r[5],
                "timestamp_normalized": r[6],
                "parse_status": r[7],
                "data": parsed_orig,
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "records": records,
        }
    finally:
        conn.close()
