"""
Phase 6 — Command-Line Interface.

Commands:
  inspect  — Run HTML reconnaissance on the input directory.
  ingest   — Run the full ingestion pipeline.
  status   — Show stored record counts and manifest history.
  validate — Verify stored Parquet counts against DuckDB.

Usage:
  python main.py inspect --input data/input_html/
  python main.py inspect --input data/input_html/ --output recon_report.json
  python main.py ingest --config config/node_mapping.json
  python main.py ingest --config config/node_mapping.json --force
  python main.py status
  python main.py validate
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .config import (
    DATABASE_DIR,
    DEFAULT_NODE_MAPPING_PATH,
    INPUT_HTML_DIR,
    MANIFESTS_DIR,
    NODES_DIR,
    ensure_data_dirs,
)
from .orchestrator import IngestionManifest, IngestionOrchestrator
from .recon import HtmlRecon


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        level=level,
        stream=sys.stderr,
    )
    # Suppress noisy third-party loggers
    for noisy in ("bs4", "urllib3", "charset_normalizer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_inspect(args: argparse.Namespace) -> int:
    """Run HTML reconnaissance."""
    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    print(f"Inspecting HTML files in: {input_dir}")
    recon = HtmlRecon(input_dir=input_dir)
    report = recon.run()
    recon.print_summary(report)

    if args.output:
        out_path = Path(args.output)
        HtmlRecon.save_json(report, out_path)
        print(f"\nReport saved to: {out_path}")

    return 0 if report.files_errored == 0 else 1


def cmd_ingest(args: argparse.Namespace) -> int:
    """Run the ingestion pipeline."""
    mapping_config = Path(args.config)
    if not mapping_config.exists():
        print(
            f"ERROR: Node mapping config not found: {mapping_config}\n"
            f"Hint: create {mapping_config} with entries like:\n"
            f'  {{"log_file.html": "NODE_A"}}',
            file=sys.stderr,
        )
        return 1

    input_dir = Path(args.input) if args.input else INPUT_HTML_DIR

    print(f"Starting ingestion")
    print(f"  Input dir    : {input_dir}")
    print(f"  Node mapping : {mapping_config}")
    if args.force:
        print("  Mode         : FORCE (reprocessing all files)")
    if args.workers and args.workers > 0:
        print(f"  Workers      : {args.workers} (manual override)")
    else:
        print("  Workers      : AUTO (dynamically tuned to file count & size)")
    print()

    orchestrator = IngestionOrchestrator(
        input_dir=input_dir,
        mapping_config=mapping_config,
        force_reprocess=args.force,
        archive_inputs=not args.no_archive,
        workers=args.workers,
    )
    manifest = orchestrator.run()
    _print_manifest_report(manifest)

    return 0 if manifest.status == "success" else 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show recent manifest history and DuckDB record counts."""
    ensure_data_dirs()

    # -- Manifest history ---------------------------------------------------
    manifests = sorted(MANIFESTS_DIR.glob("*.json"), reverse=True)
    if not manifests:
        print("No ingestion runs found yet.")
    else:
        print(f"Recent ingestion runs ({min(5, len(manifests))} of {len(manifests)}):")
        for mf in manifests[:5]:
            with mf.open("r") as fh:
                m = json.load(fh)
            print(
                f"  {m['run_id']}  status={m['status']}  "
                f"extracted={m['total_records_extracted']}  "
                f"stored={m['total_records_stored']}"
            )

    print()

    # -- DuckDB counts ------------------------------------------------------
    from .storage import init_duckdb, query_record_counts
    try:
        conn = init_duckdb()
        counts = query_record_counts(conn)
        conn.close()
        if counts:
            print("DuckDB record counts by node:")
            for node_id, cnt in sorted(counts.items()):
                print(f"  {node_id}: {cnt:,} records")
            print(f"  TOTAL : {sum(counts.values()):,} records")
        else:
            print("DuckDB: no records found (not yet ingested).")
    except Exception as exc:  # noqa: BLE001
        print(f"DuckDB query failed: {exc}", file=sys.stderr)

    print()

    # -- Parquet file listing -----------------------------------------------
    parquet_files = sorted(NODES_DIR.rglob("*.parquet"))
    if parquet_files:
        print(f"Parquet files ({len(parquet_files)}):")
        for pf in parquet_files:
            try:
                import pyarrow.parquet as pq
                n = pq.read_metadata(str(pf)).num_rows
                rel = pf.relative_to(NODES_DIR)
                print(f"  {rel}  ({n:,} rows)")
            except Exception:
                print(f"  {pf.name}  (unreadable)")
    else:
        print("No Parquet files found yet.")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Verify Parquet contents against DuckDB and report discrepancies."""
    from .storage import init_duckdb, query_record_counts, verify_stored_counts

    # Build expected counts from Parquet files on disk
    import pyarrow.parquet as pq

    expected: dict[str, int] = {}
    parquet_files = sorted(NODES_DIR.rglob("*.parquet"))

    for pf in parquet_files:
        try:
            meta = pq.read_metadata(str(pf))
            tbl = pq.read_table(str(pf), columns=["node_id"])
            for node_id in tbl["node_id"].to_pylist():
                if node_id:
                    expected[node_id] = expected.get(node_id, 0) + 1
        except Exception as exc:
            print(f"WARNING: Cannot read {pf.name}: {exc}", file=sys.stderr)

    if not expected:
        print("No Parquet data found to validate.")
        return 0

    try:
        conn = init_duckdb()
        issues = verify_stored_counts(conn, expected)
        conn.close()
    except Exception as exc:
        print(f"ERROR: DuckDB validation failed: {exc}", file=sys.stderr)
        return 1

    if issues:
        print("VALIDATION ISSUES:")
        for issue in issues:
            print(f"  ✗ {issue}")
        return 1

    print(f"Validation PASSED — {len(expected)} node(s), all counts match.")
    for node_id, cnt in sorted(expected.items()):
        print(f"  {node_id}: {cnt:,} records [OK]")
    return 0


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def _print_manifest_report(m: IngestionManifest) -> None:
    w = 72
    sep = "=" * w
    thin = "-" * w

    print(sep)
    print(f"INGESTION REPORT  run={m.run_id}  status={m.status.upper()}")
    print(sep)
    print(f"  Files discovered : {m.files_discovered}")
    print(f"  Files mapped     : {m.files_mapped}")
    print(f"  Files unmapped   : {m.files_unmapped}")
    print(thin)
    print(f"  Files success    : {m.files_success}")
    print(f"  Files skipped    : {m.files_skipped}")
    print(f"  Files failed     : {m.files_failed}")
    print(thin)
    print(f"  Records extracted: {m.total_records_extracted:,}")
    print(f"  Records stored   : {m.total_records_stored:,}")
    print(thin)
    print(f"  Timestamps valid   : {m.total_ts_valid:,}")
    print(f"  Timestamps missing : {m.total_ts_missing:,}")
    print(f"  Timestamps invalid : {m.total_ts_invalid:,}")
    print(thin)

    if m.unmapped_files:
        print("  UNMAPPED FILES (no node assignment):")
        for f in m.unmapped_files:
            print(f"    [-] {f}")
        print(thin)

    if m.validation_issues:
        print("  VALIDATION ISSUES:")
        for issue in m.validation_issues:
            print(f"    [!] {issue}")
        print(thin)

    if m.file_outcomes:
        print("  Per-file outcomes:")
        for o in m.file_outcomes:
            icon = {"success": "+", "skipped": "~", "failed": "!", "no_records": "-"}.get(
                o.status, "?"
            )
            print(
                f"    [{icon}] {o.filename}  node={o.node_id}  "
                f"tables={o.tables_inspected}  "
                f"records={o.records_stored}"
            )
            if o.error:
                print(f"        ERROR: {o.error}")
            if o.skipped_tables:
                print(f"        Skipped tables: {', '.join(o.skipped_tables[:5])}")

    print(sep)
    print(f"  Completed: {m.completed_at}")
    print(sep)


# ---------------------------------------------------------------------------
# Extended Handlers (Export, Reset, Full Pipeline)
# ---------------------------------------------------------------------------

def cmd_export(args: argparse.Namespace) -> int:
    """Export DuckDB records into UI JSON dataset."""
    from .dataset_builder import export_ui_dataset
    print("Exporting DuckDB records to frontend dataset...")
    export_ui_dataset()
    print("Dataset successfully exported to frontend/existing_design/data/mock/")
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    """Safely reset DuckDB, Parquet shards, and UI cache (preserving raw HTML source files)."""
    from .config import DATABASE_DIR, DUCKDB_PATH, NODES_DIR, MANIFESTS_DIR, DATA_DIR, PROJECT_ROOT

    print("Purging database and cache...")
    if DUCKDB_PATH.exists():
        DUCKDB_PATH.unlink()
        print(f"  [x] Deleted DuckDB: {DUCKDB_PATH}")
    wal_file = DATABASE_DIR / "flightstory.duckdb.wal"
    if wal_file.exists():
        wal_file.unlink()

    if NODES_DIR.exists():
        for sub_dir in NODES_DIR.iterdir():
            if sub_dir.is_dir():
                for p in sub_dir.glob("*.parquet"):
                    p.unlink()
        print(f"  [x] Cleared Parquet files in: {NODES_DIR}")

    if MANIFESTS_DIR.exists():
        for m in MANIFESTS_DIR.glob("*.json"):
            m.unlink()
        print(f"  [x] Cleared manifests in: {MANIFESTS_DIR}")

    recon_json = DATA_DIR / "recon_report.json"
    if recon_json.exists():
        recon_json.unlink()

    mock_dir = PROJECT_ROOT / "frontend" / "existing_design" / "data" / "mock"
    if mock_dir.exists():
        (mock_dir / "events.json").write_text("[]", encoding="utf-8")
        (mock_dir / "translations.json").write_text("{}", encoding="utf-8")
        (mock_dir / "manifest.json").write_text('{"ingested_at": null, "total_records": 0, "nodes": {}}', encoding="utf-8")
        print(f"  [x] Reset frontend mock files to empty in: {mock_dir}")

    print("\n[OK] System wiped clean! All source HTML logs in data/input_html remain intact.")
    print("Run 'python main.py pipeline' to re-test end-to-end.")
    return 0


def cmd_pipeline(args: argparse.Namespace) -> int:
    """Run full end-to-end pipeline: inspect -> ingest -> export."""
    from .dataset_builder import export_ui_dataset

    print("==================================================")
    print("STEP 1: HTML Reconnaissance")
    print("==================================================")
    recon = HtmlRecon(input_dir=INPUT_HTML_DIR)
    report = recon.run()
    recon.print_summary(report)

    print("\n==================================================")
    print("STEP 2: Data Ingestion (DuckDB + Parquet)")
    print("==================================================")
    orch = IngestionOrchestrator(
        input_dir=INPUT_HTML_DIR,
        mapping_config=DEFAULT_NODE_MAPPING_PATH,
        force_reprocess=True,
        archive_inputs=True,
    )
    manifest = orch.run()
    _print_manifest_report(manifest)

    print("\n==================================================")
    print("STEP 3: Domain Translation & UI Export")
    print("==================================================")
    export_ui_dataset()
    print("\n[SUCCESS] End-to-end ingestion & UI export completed!")
    print(f"Total stored records: {manifest.total_records_stored}")

    print("\n==================================================")
    print("STEP 4: Teammate Lightning Normalization")
    print("==================================================")
    try:
        from .normalizer import run_lightning_pipeline
        run_lightning_pipeline()
    except Exception as e:
        print(f"Warning: normalizer failed: {e}")

    print("\n==================================================")
    print("STEP 5: Cross-Node Correlation Engine")
    print("==================================================")
    try:
        from .correlator import FDMCrossNodeCorrelationEngine
        engine = FDMCrossNodeCorrelationEngine()
        engine.export_json()
    except Exception as e:
        print(f"Warning: correlator failed: {e}")

    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    """Start live FastAPI ingestion server."""
    from .server import start_server
    start_server(host=args.host, port=args.port)
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flightstory",
        description="FlightStory AI — Aircraft Data Ingestion Engine",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # inspect
    p_inspect = sub.add_parser("inspect", help="Inspect HTML files (reconnaissance)")
    p_inspect.add_argument(
        "--input", default=str(INPUT_HTML_DIR),
        help=f"Input directory (default: {INPUT_HTML_DIR})",
    )
    p_inspect.add_argument(
        "--output", default=None,
        help="Save JSON report to this path",
    )

    # ingest
    p_ingest = sub.add_parser("ingest", help="Run ingestion pipeline")
    p_ingest.add_argument(
        "--config", default=str(DEFAULT_NODE_MAPPING_PATH),
        help=f"Node mapping JSON file (default: {DEFAULT_NODE_MAPPING_PATH})",
    )
    p_ingest.add_argument(
        "--input", default=None,
        help="Override input directory",
    )
    p_ingest.add_argument(
        "--force", action="store_true",
        help="Reprocess all files even if unchanged",
    )
    p_ingest.add_argument(
        "--no-archive", action="store_true",
        help="Skip copying originals to raw_archive/",
    )
    p_ingest.add_argument(
        "-w", "--workers", type=int, default=None,
        help="Number of parallel worker threads (default: auto-tuned based on workload)",
    )

    # status
    sub.add_parser("status", help="Show ingestion history and record counts")

    # validate
    sub.add_parser("validate", help="Verify stored counts against DuckDB")

    # export
    sub.add_parser("export", help="Export DuckDB records into UI JSON dataset")

    # reset
    sub.add_parser("reset", help="Purge DuckDB and cache to start testing from scratch")

    # pipeline
    sub.add_parser("pipeline", help="Run complete end-to-end pipeline (inspect + ingest + export)")

    # serve
    p_serve = sub.add_parser("serve", help="Start FastAPI server on port 8000 for UI ingestion")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    _setup_logging(verbose=args.verbose)

    handlers = {
        "inspect": cmd_inspect,
        "ingest": cmd_ingest,
        "status": cmd_status,
        "validate": cmd_validate,
        "export": cmd_export,
        "reset": cmd_reset,
        "pipeline": cmd_pipeline,
        "serve": cmd_serve,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    sys.exit(handler(args))


if __name__ == "__main__":
    main()
