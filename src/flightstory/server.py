"""
FlightStory AI — Ingestion API Server (FastAPI).

Provides endpoints for live UI ingestion:
- GET  /api/status               — Returns DuckDB record counts.
- POST /api/upload-and-ingest    — Ingests uploaded HTML files and exports UI dataset.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import DUCKDB_PATH, INPUT_HTML_DIR, DEFAULT_NODE_MAPPING_PATH
from .storage import init_duckdb, query_record_counts
from .orchestrator import IngestionOrchestrator
from .dataset_builder import export_ui_dataset

log = logging.getLogger(__name__)

app = FastAPI(title="FlightStory Ingestion API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
def get_status():
    if not DUCKDB_PATH.exists():
        return {"total_records": 0, "nodes": {}}

    try:
        con = init_duckdb()
        counts = query_record_counts(con)
        con.close()
        total = sum(counts.values())
        return {
            "total_records": total,
            "nodes": counts,
        }
    except Exception as ex:
        return {"total_records": 0, "error": str(ex)}


@app.post("/api/upload-and-ingest")
async def upload_and_ingest(
    files: List[UploadFile] = File(...),
    flight_id: str = Query("AA100"),
):
    INPUT_HTML_DIR.mkdir(parents=True, exist_ok=True)
    saved_files = []

    for f in files:
        target = INPUT_HTML_DIR / f.filename
        content = await f.read()
        target.write_bytes(content)
        saved_files.append(f.filename)

    # Run orchestrator
    orch = IngestionOrchestrator(
        input_dir=INPUT_HTML_DIR,
        node_mapping_config=DEFAULT_NODE_MAPPING_PATH,
    )
    manifest = orch.run(force=True, copy_to_archive=True)

    # Export to UI
    export_ui_dataset()

    return {
        "status": "success",
        "flight_id": flight_id,
        "files_uploaded": len(saved_files),
        "records_extracted": manifest.total_records_extracted,
        "records_stored": manifest.total_records_stored,
        "outcomes": [
            {
                "filename": o.filename,
                "node_id": o.node_id,
                "records": o.records_stored,
                "status": o.status,
            }
            for o in manifest.file_outcomes
        ],
    }


@app.post("/api/delete-flight")
def delete_flight(flight_id: str = Query("AA100")):
    """Purges DuckDB tables, Parquet shards, and resets mock data to 0 records."""
    from .config import PROJECT_ROOT, NODES_DIR, MANIFESTS_DIR, DATA_DIR, DATABASE_DIR
    
    if DUCKDB_PATH.exists():
        try:
            DUCKDB_PATH.unlink()
        except Exception:
            pass
    wal_file = DATABASE_DIR / "flightstory.duckdb.wal"
    if wal_file.exists():
        try:
            wal_file.unlink()
        except Exception:
            pass

    if NODES_DIR.exists():
        for sub_dir in NODES_DIR.iterdir():
            if sub_dir.is_dir():
                for p in sub_dir.glob("*.parquet"):
                    p.unlink()

    if MANIFESTS_DIR.exists():
        for m in MANIFESTS_DIR.glob("*.json"):
            m.unlink()

    mock_dir = PROJECT_ROOT / "frontend" / "existing_design" / "data" / "mock"
    if mock_dir.exists():
        (mock_dir / "events.json").write_text("[]", encoding="utf-8")
        (mock_dir / "translations.json").write_text("{}", encoding="utf-8")
        (mock_dir / "manifest.json").write_text('{"ingested_at": null, "total_records": 0, "nodes": {}}', encoding="utf-8")

    return {
        "status": "success",
        "message": f"Complete aircraft data, nodes, and logs deleted for {flight_id}.",
        "flight_id": flight_id,
        "records_remaining": 0,
    }


def start_server(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    print(f"Starting FlightStory API Server on http://{host}:{port}...")
    uvicorn.run("flightstory.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    start_server()
