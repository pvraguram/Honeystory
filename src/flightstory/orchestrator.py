"""
Module G — Ingestion orchestration.

Coordinates the full pipeline for one ingestion run:

  1. Validate the configured node mapping.
  2. Discover input files.
  3. Cross-reference with the node mapping; flag unmapped files.
  4. For each node (sequentially):
     a. For each file assigned to that node:
        i.   Check if the batch already exists (idempotency).
        ii.  Extract records (lazy batched generator).
        iii. Write Parquet batch.
        iv.  Record outcomes.
  5. Refresh DuckDB views.
  6. Verify stored record counts.
  7. Save a JSON manifest for this run.
  8. Report overall status.

The orchestrator exposes a clean programmatic interface (IngestionOrchestrator)
so that a future UI can call it without changes to the ingestion core.
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .config import (
    DEFAULT_NODE_MAPPING_PATH,
    INPUT_HTML_DIR,
    MANIFESTS_DIR,
    RAW_ARCHIVE_DIR,
    ensure_data_dirs,
)
from .discovery import FileRecord, discover_files
from .extractor import ExtractionReport, extract_file
from .models import IngestionRecord
from .node_mapping import resolve_node_mapping
from .storage import (
    batch_already_written,
    init_duckdb,
    refresh_duckdb_views,
    verify_stored_counts,
    write_batch,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Manifest / result data classes
# ---------------------------------------------------------------------------

@dataclass
class FileOutcome:
    filename: str
    node_id: str
    file_hash: str
    file_size_bytes: int
    status: str                # "success" | "skipped" | "failed" | "no_records"
    tables_inspected: int = 0
    tables_extracted: int = 0
    tables_skipped: int = 0
    records_extracted: int = 0
    records_stored: int = 0
    ts_valid: int = 0
    ts_missing: int = 0
    ts_invalid: int = 0
    ts_ambiguous: int = 0
    error: str | None = None
    skipped_tables: list[str] = field(default_factory=list)
    extraction_errors: list[str] = field(default_factory=list)


@dataclass
class IngestionManifest:
    run_id: str
    started_at: str
    completed_at: str | None
    input_dir: str
    mapping_config: str
    status: str   # "success" | "partial" | "failed"
    files_discovered: int = 0
    files_mapped: int = 0
    files_unmapped: int = 0
    files_success: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    total_records_extracted: int = 0
    total_records_stored: int = 0
    total_ts_valid: int = 0
    total_ts_missing: int = 0
    total_ts_invalid: int = 0
    validation_issues: list[str] = field(default_factory=list)
    unmapped_files: list[str] = field(default_factory=list)
    file_outcomes: list[FileOutcome] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Worker auto-scaling helper
# ---------------------------------------------------------------------------

def compute_optimal_workers(
    tasks: list[tuple[FileRecord, str]],
    requested_workers: int | None = None,
) -> int:
    """
    Dynamically determine the optimal number of worker threads based on:
    1. Explicit override if provided (> 0).
    2. Total file count (never exceed task count).
    3. Aggregate workload (payload size in bytes).
    4. Available system CPU cores.
    """
    if requested_workers is not None and requested_workers > 0:
        return min(requested_workers, len(tasks)) if tasks else 1

    if not tasks:
        return 1

    n_files = len(tasks)
    if n_files == 1:
        return 1

    import os
    cpu_cores = os.cpu_count() or 4
    total_bytes = sum(fr.size_bytes for fr, _ in tasks)

    # Lightweight workload (small files, <= 3 files):
    if total_bytes < 300_000 and n_files <= 3:
        allocated = min(n_files, 2)
    # Medium workload (< 5 MB): scale up to CPU cores or file count
    elif total_bytes < 5_000_000:
        allocated = min(n_files, max(cpu_cores, 2))
    # Heavy workload (>= 5 MB or many files): scale up to 2x cores, capped at 16
    else:
        allocated = min(n_files, max(cpu_cores, 4) * 2, 16)

    log.info(
        "Auto-tuned worker pool: allocated %d workers for %d files "
        "(total: %.2f MB, detected %d CPU cores)",
        allocated,
        n_files,
        total_bytes / (1024 * 1024),
        cpu_cores,
    )
    return allocated


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class IngestionOrchestrator:
    """
    Main entry point for the ingestion pipeline.

    Parameters
    ----------
    input_dir : Path | None
        Directory containing the HTML source files.
        Defaults to ``config.INPUT_HTML_DIR``.
    mapping_config : Path | None
        Path to the node-mapping JSON file.
        Defaults to ``config.DEFAULT_NODE_MAPPING_PATH``.
    force_reprocess : bool
        When True, rewrite Parquet batches even for unchanged files.
    archive_inputs : bool
        When True, copy original HTML files to ``data/raw_archive/``.
    workers : int | None
        Number of parallel workers. If None or 0, workers auto-tune
        adaptively based on file count, size, and available CPU cores.
    """

    def __init__(
        self,
        input_dir: Path | None = None,
        mapping_config: Path | None = None,
        *,
        force_reprocess: bool = False,
        archive_inputs: bool = True,
        workers: int | None = None,
    ) -> None:
        self.input_dir = input_dir or INPUT_HTML_DIR
        self.mapping_config = mapping_config or DEFAULT_NODE_MAPPING_PATH
        self.force_reprocess = force_reprocess
        self.archive_inputs = archive_inputs
        self.workers = workers

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> IngestionManifest:
        """
        Execute the full ingestion pipeline and return a manifest.

        Safe to call multiple times.  Unchanged files are skipped unless
        ``force_reprocess=True``.
        """
        ensure_data_dirs()

        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        started_at = datetime.now(timezone.utc).isoformat()

        manifest = IngestionManifest(
            run_id=run_id,
            started_at=started_at,
            completed_at=None,
            input_dir=str(self.input_dir),
            mapping_config=str(self.mapping_config),
            status="failed",
        )

        log.info("=== Ingestion run %s started ===", run_id)

        # -- Step 1: Discover files -----------------------------------------
        discovery = discover_files(self.input_dir)
        manifest.files_discovered = len(discovery.discovered)

        # -- Step 2: Resolve node mapping ------------------------------------
        filenames = [f.filename for f in discovery.readable_files]
        mapping_result = resolve_node_mapping(filenames, self.mapping_config)

        if mapping_result.load_error:
            log.error("Node mapping failed: %s", mapping_result.load_error)
            manifest.status = "failed"
            manifest.completed_at = datetime.now(timezone.utc).isoformat()
            self._save_manifest(manifest)
            return manifest

        manifest.files_mapped = len(mapping_result.mapped)
        manifest.files_unmapped = len(mapping_result.unmapped)
        manifest.unmapped_files = list(mapping_result.unmapped)

        if mapping_result.unmapped:
            log.warning(
                "%d file(s) have no node assignment: %s",
                len(mapping_result.unmapped),
                mapping_result.unmapped,
            )

        # -- Step 3: Archive originals (optional) ---------------------------
        if self.archive_inputs:
            self._archive_files(discovery.readable_files)

        # -- Step 4: Group files by node and ingest -------------------------
        node_to_files: dict[str, list[FileRecord]] = {}
        file_map = {f.filename: f for f in discovery.readable_files}

        for filename, node_id in mapping_result.mapped.items():
            fr = file_map.get(filename)
            if fr is None:
                continue
            node_to_files.setdefault(node_id, []).append(fr)

        expected_counts: dict[str, int] = {}
        all_outcomes: list[FileOutcome] = []

        # Prepare tasks: list of (FileRecord, node_id)
        tasks: list[tuple[FileRecord, str]] = [
            (fr, node_id)
            for node_id in sorted(node_to_files)
            for fr in node_to_files[node_id]
        ]

        effective_workers = compute_optimal_workers(tasks, self.workers)

        if effective_workers > 1 and len(tasks) > 1:
            import concurrent.futures

            log.info(
                "Executing parallel ingestion with %d workers across %d files",
                effective_workers,
                len(tasks),
            )
            with concurrent.futures.ThreadPoolExecutor(max_workers=effective_workers) as executor:
                futures = {
                    executor.submit(self._ingest_file, fr, node_id): (node_id, fr.filename)
                    for fr, node_id in tasks
                }
                for future in concurrent.futures.as_completed(futures):
                    outcome = future.result()
                    all_outcomes.append(outcome)
        else:
            for fr, node_id in tasks:
                outcome = self._ingest_file(fr, node_id)
                all_outcomes.append(outcome)

        # Sort outcomes deterministically by (node_id, filename)
        all_outcomes.sort(key=lambda o: (o.node_id, o.filename))

        for outcome in all_outcomes:
            manifest.file_outcomes.append(outcome)

            if outcome.status == "success":
                manifest.files_success += 1
            elif outcome.status == "skipped":
                manifest.files_skipped += 1
            else:
                manifest.files_failed += 1

            manifest.total_records_extracted += outcome.records_extracted
            manifest.total_records_stored += outcome.records_stored
            manifest.total_ts_valid += outcome.ts_valid
            manifest.total_ts_missing += outcome.ts_missing
            manifest.total_ts_invalid += outcome.ts_invalid
            expected_counts[outcome.node_id] = (
                expected_counts.get(outcome.node_id, 0) + outcome.records_stored
            )

        # -- Step 5: Refresh DuckDB views ------------------------------------
        try:
            conn = init_duckdb()
            refresh_duckdb_views(conn)
            issues = verify_stored_counts(conn, expected_counts)
            conn.close()
        except Exception as exc:  # noqa: BLE001
            issues = [f"DuckDB refresh failed: {exc}"]
            log.error("DuckDB refresh failed: %s", exc)

        manifest.validation_issues = issues
        if issues:
            log.warning("Validation issues: %s", issues)

        # -- Step 6: Final status -------------------------------------------
        if manifest.files_failed > 0 or issues:
            manifest.status = "partial"
        else:
            manifest.status = "success"

        manifest.completed_at = datetime.now(timezone.utc).isoformat()
        self._save_manifest(manifest)

        log.info(
            "=== Run %s complete: %s | %d extracted | %d stored ===",
            run_id,
            manifest.status,
            manifest.total_records_extracted,
            manifest.total_records_stored,
        )
        return manifest

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ingest_file(self, file_record: FileRecord, node_id: str) -> FileOutcome:
        """Run the extract-write pipeline for one file."""
        outcome = FileOutcome(
            filename=file_record.filename,
            node_id=node_id,
            file_hash=file_record.sha256,
            file_size_bytes=file_record.size_bytes,
            status="failed",
        )

        # Idempotency check
        if batch_already_written(node_id, file_record.sha256) and not self.force_reprocess:
            log.info(
                "Skipping unchanged file (batch exists): %s", file_record.filename
            )
            # Recover stored count from existing Parquet
            import pyarrow.parquet as pq
            from .config import node_output_dir
            p = node_output_dir(node_id) / f"{file_record.sha256}.parquet"
            try:
                stored = pq.read_metadata(str(p)).num_rows
            except Exception:
                stored = 0
            outcome.status = "skipped"
            outcome.records_stored = stored
            return outcome

        # Extract
        try:
            ext_report, record_gen = extract_file(
                html_path=file_record.path,
                node_id=node_id,
                file_hash=file_record.sha256,
            )
        except Exception as exc:  # noqa: BLE001
            outcome.error = str(exc)
            log.error("Extraction failed for %s: %s", file_record.filename, exc)
            return outcome

        if ext_report.file_error:
            outcome.error = ext_report.file_error
            return outcome

        outcome.tables_inspected = len(ext_report.tables)
        outcome.tables_extracted = len(ext_report.extracted_tables)
        outcome.tables_skipped = len(ext_report.skipped_tables)
        outcome.skipped_tables = [t.table_id for t in ext_report.skipped_tables]
        outcome.extraction_errors = [
            err
            for t in ext_report.tables
            for err in t.extraction_errors
        ]

        # Collect all records (consume generator once) with ts statistics
        all_records: list[IngestionRecord] = []
        for batch in record_gen:
            for r in batch:
                all_records.append(r)
                _status = r.timestamp_parse_status.value
                if _status == "valid":
                    outcome.ts_valid += 1
                elif _status == "missing":
                    outcome.ts_missing += 1
                elif _status == "invalid":
                    outcome.ts_invalid += 1
                elif _status == "ambiguous":
                    outcome.ts_ambiguous += 1

        outcome.records_extracted = len(all_records)

        if not all_records:
            outcome.status = "no_records"
            log.info(
                "No records extracted from %s (tables without ts cols: %d)",
                file_record.filename,
                outcome.tables_skipped,
            )
            return outcome

        # Write
        write_result = write_batch(
            iter(all_records),
            node_id=node_id,
            file_hash=file_record.sha256,
            overwrite=self.force_reprocess,
        )

        if write_result.error:
            outcome.error = write_result.error
            return outcome

        outcome.records_stored = write_result.rows_written
        outcome.status = "success"
        return outcome

    def _archive_files(self, file_records: list[FileRecord]) -> None:
        """Copy original input files to raw_archive/ (idempotent)."""
        for fr in file_records:
            dest = RAW_ARCHIVE_DIR / fr.filename
            if not dest.exists():
                try:
                    shutil.copy2(fr.path, dest)
                    log.debug("Archived: %s", fr.filename)
                except OSError as exc:
                    log.warning("Could not archive %s: %s", fr.filename, exc)

    def _save_manifest(self, manifest: IngestionManifest) -> None:
        """Persist the manifest as a JSON file in MANIFESTS_DIR."""
        MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
        path = MANIFESTS_DIR / f"{manifest.run_id}.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(asdict(manifest), fh, indent=2, ensure_ascii=False)
        log.info("Manifest saved: %s", path.name)
