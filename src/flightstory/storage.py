"""
Module F — Storage.

Responsibilities:
- Write extracted records as Parquet files in per-node directories.
- Maintain a single shared DuckDB database with views across all node folders.
- Support idempotent batch writes (skip unchanged source files on rerun).
- Avoid creating one Parquet file per record.
- Keep records traceable to their source file, table, and row.
- Never silently overwrite valid output with a failed ingestion batch.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .config import DUCKDB_PATH, NODES_DIR, node_output_dir
from .models import IngestionRecord

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Parquet schema
# ---------------------------------------------------------------------------

_PARQUET_SCHEMA = pa.schema([
    pa.field("event_id",              pa.string()),
    pa.field("workspace_id",          pa.string()),
    pa.field("node_id",               pa.string()),
    pa.field("source_file",           pa.string()),
    pa.field("source_file_hash",      pa.string()),
    pa.field("source_table_id",       pa.string()),
    pa.field("source_row_number",     pa.int64()),
    pa.field("timestamp_raw",         pa.string()),
    pa.field("timestamp_normalized",  pa.string()),
    pa.field("timestamp_parse_status",pa.string()),
    pa.field("timestamp_parse_error", pa.string()),
    pa.field("original_record",       pa.string()),  # JSON string
])


# ---------------------------------------------------------------------------
# Idempotency helpers
# ---------------------------------------------------------------------------

def _batch_parquet_path(node_dir: Path, file_hash: str) -> Path:
    """
    Return the deterministic Parquet path for a given source-file hash.

    One Parquet file per source file (not per table or per record).
    The filename is derived from the SHA-256 so the same unchanged file
    always maps to the same path, enabling safe re-run detection.
    """
    return node_dir / f"{file_hash}.parquet"


def batch_already_written(node_id: str, file_hash: str) -> bool:
    """Return True if a Parquet batch for *file_hash* already exists."""
    node_dir = node_output_dir(node_id)
    return _batch_parquet_path(node_dir, file_hash).exists()


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

@dataclass
class WriteResult:
    parquet_path: Path
    rows_written: int
    skipped: bool = False      # True when the batch already existed
    error: str | None = None


def write_batch(
    records: Iterable[IngestionRecord],
    node_id: str,
    file_hash: str,
    *,
    overwrite: bool = False,
) -> WriteResult:
    """
    Write *records* to a Parquet file for *node_id*.

    Parameters
    ----------
    records : Iterable[IngestionRecord]
        Records to persist.  Consumed exactly once.
    node_id : str
        Determines the output subdirectory.
    file_hash : str
        SHA-256 of the originating HTML file.
    overwrite : bool
        When True, replace an existing batch even for an unchanged file.
        When False (default), skip writing if the file already exists.

    Returns
    -------
    WriteResult
    """
    node_dir = node_output_dir(node_id)
    parquet_path = _batch_parquet_path(node_dir, file_hash)

    if parquet_path.exists() and not overwrite:
        log.info("Batch already exists, skipping: %s", parquet_path.name)
        # Count existing rows for the result
        existing = pq.read_metadata(parquet_path).num_rows
        return WriteResult(
            parquet_path=parquet_path,
            rows_written=existing,
            skipped=True,
        )

    rows = [r.to_dict() for r in records]
    if not rows:
        log.debug("No records to write for hash %s", file_hash[:8])
        return WriteResult(
            parquet_path=parquet_path,
            rows_written=0,
        )

    df = pd.DataFrame(rows)
    # Ensure all expected columns are present with correct types
    for col, dtype in IngestionRecord.column_dtypes().items():
        if col not in df.columns:
            df[col] = pd.NA
        if dtype == "int64":
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        else:
            df[col] = df[col].astype("string")

    table = pa.Table.from_pandas(df, schema=_PARQUET_SCHEMA, safe=False)

    # Atomic write: write to a temp path then rename to avoid corrupt outputs
    tmp_path = parquet_path.with_suffix(".tmp.parquet")
    try:
        pq.write_table(table, tmp_path, compression="snappy")
        tmp_path.replace(parquet_path)
    except Exception as exc:
        # Clean up partial write
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        log.error("Failed to write batch %s: %s", parquet_path.name, exc)
        return WriteResult(
            parquet_path=parquet_path,
            rows_written=0,
            error=str(exc),
        )

    log.info(
        "Wrote %d records → %s", len(rows), parquet_path.relative_to(NODES_DIR)
    )
    return WriteResult(parquet_path=parquet_path, rows_written=len(rows))


# ---------------------------------------------------------------------------
# DuckDB management
# ---------------------------------------------------------------------------

def init_duckdb(db_path: Path | None = None) -> duckdb.DuckDBPyConnection:
    """
    Open (or create) the shared DuckDB database.

    Returns a connection with auto-commit behaviour.  The caller is
    responsible for closing the connection when done.
    """
    if db_path is None:
        # Import lazily so that test monkeypatching of storage.DUCKDB_PATH
        # or config.DUCKDB_PATH takes effect at call time.
        from . import config as _cfg
        db_path = getattr(_cfg, "DUCKDB_PATH", DUCKDB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    log.info("DuckDB opened: %s", db_path)
    return conn


def refresh_duckdb_views(
    conn: duckdb.DuckDBPyConnection,
    nodes_dir: Path | None = None,
) -> None:
    """
    Register a DuckDB view for each node folder that contains Parquet files.

    Also creates a unified ``all_records`` view spanning every node.

    Views are replaced (not appended) so that re-runs stay consistent.
    """
    if nodes_dir is None:
        from . import config as _cfg
        nodes_dir = getattr(_cfg, "NODES_DIR", NODES_DIR)

    if not nodes_dir.exists():
        log.debug("nodes_dir does not exist yet: %s", nodes_dir)
        return

    node_dirs = [p for p in nodes_dir.iterdir() if p.is_dir()]
    node_views: list[str] = []

    for node_dir in sorted(node_dirs):
        parquet_files = sorted(node_dir.glob("*.parquet"))
        if not parquet_files:
            log.debug("No Parquet files yet in %s, skipping view", node_dir.name)
            continue

        # DuckDB can read a glob of Parquet files
        glob_pattern = str(node_dir / "*.parquet").replace("\\", "/")
        view_name = f"node_{node_dir.name.lower()}"

        conn.execute(
            f"CREATE OR REPLACE VIEW {view_name} AS "
            f"SELECT * FROM read_parquet('{glob_pattern}')"
        )
        node_views.append(view_name)
        log.info("Refreshed DuckDB view: %s", view_name)

    # Unified view
    if node_views:
        union_sql = " UNION ALL ".join(
            f"SELECT * FROM {v}" for v in node_views
        )
        conn.execute(
            f"CREATE OR REPLACE VIEW all_records AS {union_sql}"
        )
        log.info("Refreshed unified DuckDB view: all_records (%d nodes)", len(node_views))
    else:
        log.warning("No node Parquet files found; all_records view not created")


def query_record_counts(
    conn: duckdb.DuckDBPyConnection,
) -> dict[str, int]:
    """
    Return a dict of {node_id: record_count} by querying DuckDB views.
    """
    try:
        rows = conn.execute(
            "SELECT node_id, COUNT(*) AS cnt FROM all_records GROUP BY node_id"
        ).fetchall()
        return {row[0]: row[1] for row in rows}
    except duckdb.CatalogException:
        # View not yet created (no data ingested)
        return {}


def verify_stored_counts(
    conn: duckdb.DuckDBPyConnection,
    expected: dict[str, int],
) -> list[str]:
    """
    Compare *expected* {node_id: count} against DuckDB stored counts.

    Returns a list of discrepancy messages (empty = all good).
    """
    actual = query_record_counts(conn)
    issues: list[str] = []

    for node_id, exp_count in expected.items():
        act_count = actual.get(node_id, 0)
        if act_count != exp_count:
            issues.append(
                f"Node {node_id}: expected {exp_count} records, "
                f"DuckDB has {act_count}"
            )

    for node_id in set(actual) - set(expected):
        issues.append(
            f"Node {node_id}: found {actual[node_id]} stored records "
            f"but no expectation recorded"
        )

    return issues
