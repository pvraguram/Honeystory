"""
Tests for Module G — Ingestion Orchestrator (integration tests).

Covers:
- Full pipeline runs without error on fixture files
- Node mapping is respected
- Unmapped files are reported but don't block other files
- Manifests are saved and contain accurate statistics
- Re-running on unchanged files skips Parquet re-writes
- Changed files (force_reprocess=True) are re-written
- Failure on one file does not prevent processing of others
- Record counts in manifest match DuckDB stored counts
- Missing mapping config produces a clear error in the manifest
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.conftest import FIXTURES_DIR, make_html_with_iso_timestamps


def _make_orchestrator(
    tmp_path: Path,
    mapping: dict,
    *,
    force: bool = False,
    archive: bool = False,
):
    """Create an IngestionOrchestrator pointed at an isolated tmp directory."""
    import flightstory.config as cfg
    import flightstory.storage as storage
    import flightstory.orchestrator as orch_mod

    # Redirect all data paths to tmp
    input_dir = tmp_path / "input_html"
    nodes_dir = tmp_path / "nodes"
    manifests_dir = tmp_path / "manifests"
    archive_dir = tmp_path / "raw_archive"
    db_dir = tmp_path / "database"

    for d in (input_dir, nodes_dir, manifests_dir, archive_dir, db_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Patch config globals
    cfg.INPUT_HTML_DIR = input_dir
    cfg.NODES_DIR = nodes_dir
    cfg.MANIFESTS_DIR = manifests_dir
    cfg.RAW_ARCHIVE_DIR = archive_dir
    cfg.DATABASE_DIR = db_dir
    cfg.DUCKDB_PATH = db_dir / "test.duckdb"
    cfg.OUTPUT_DIR_MARKERS = (archive_dir, nodes_dir, db_dir)

    # Patch storage module globals (it captured NODES_DIR at import)
    storage.NODES_DIR = nodes_dir
    storage.DUCKDB_PATH = db_dir / "test.duckdb"

    # Patch orchestrator module constants (captured at import)
    orch_mod.MANIFESTS_DIR = manifests_dir
    orch_mod.RAW_ARCHIVE_DIR = archive_dir
    orch_mod.INPUT_HTML_DIR = input_dir

    # Write mapping config
    mapping_path = tmp_path / "mapping.json"
    mapping_path.write_text(json.dumps(mapping), encoding="utf-8")

    from flightstory.orchestrator import IngestionOrchestrator
    return IngestionOrchestrator(
        input_dir=input_dir,
        mapping_config=mapping_path,
        force_reprocess=force,
        archive_inputs=archive,
    ), input_dir


class TestOrchestratorHappyPath:
    def test_simple_file_ingested(self, tmp_path: Path) -> None:
        orch, input_dir = _make_orchestrator(
            tmp_path, {"simple.html": "NODE_A"}
        )
        make_html_with_iso_timestamps(input_dir / "simple.html", n_rows=4)
        manifest = orch.run()

        assert manifest.status == "success"
        assert manifest.files_success == 1
        assert manifest.total_records_extracted == 4
        assert manifest.total_records_stored == 4

    def test_multi_node_assignment(self, tmp_path: Path) -> None:
        orch, input_dir = _make_orchestrator(
            tmp_path,
            {"file_a.html": "NODE_A", "file_b.html": "NODE_B"},
        )
        make_html_with_iso_timestamps(input_dir / "file_a.html", n_rows=3)
        make_html_with_iso_timestamps(input_dir / "file_b.html", n_rows=5)
        manifest = orch.run()

        assert manifest.status == "success"
        assert manifest.total_records_stored == 8
        nodes_assigned = {o.node_id for o in manifest.file_outcomes}
        assert "NODE_A" in nodes_assigned
        assert "NODE_B" in nodes_assigned

    def test_manifest_saved_to_disk(self, tmp_path: Path) -> None:
        import flightstory.config as cfg
        orch, input_dir = _make_orchestrator(
            tmp_path, {"f.html": "NODE_A"}
        )
        make_html_with_iso_timestamps(input_dir / "f.html", n_rows=2)
        manifest = orch.run()

        manifest_files = list(cfg.MANIFESTS_DIR.glob("*.json"))
        assert len(manifest_files) == 1
        data = json.loads(manifest_files[0].read_text(encoding="utf-8"))
        assert data["run_id"] == manifest.run_id

    def test_manifest_statistics_accurate(self, tmp_path: Path) -> None:
        orch, input_dir = _make_orchestrator(
            tmp_path, {"g.html": "NODE_A"}
        )
        make_html_with_iso_timestamps(input_dir / "g.html", n_rows=6)
        manifest = orch.run()

        assert manifest.total_ts_valid == 6
        assert manifest.total_ts_missing == 0


class TestOrchestratorUnmapped:
    def test_unmapped_files_reported(self, tmp_path: Path) -> None:
        orch, input_dir = _make_orchestrator(
            tmp_path, {"mapped.html": "NODE_A"}
        )
        make_html_with_iso_timestamps(input_dir / "mapped.html", n_rows=2)
        make_html_with_iso_timestamps(input_dir / "unmapped.html", n_rows=2)
        manifest = orch.run()

        assert "unmapped.html" in manifest.unmapped_files
        assert manifest.files_unmapped == 1

    def test_unmapped_does_not_block_mapped(self, tmp_path: Path) -> None:
        orch, input_dir = _make_orchestrator(
            tmp_path, {"mapped.html": "NODE_A"}
        )
        make_html_with_iso_timestamps(input_dir / "mapped.html", n_rows=3)
        make_html_with_iso_timestamps(input_dir / "unmapped.html", n_rows=3)
        manifest = orch.run()

        assert manifest.files_success == 1
        assert manifest.total_records_stored == 3


class TestOrchestratorIdempotency:
    def test_rerun_skips_unchanged_file(self, tmp_path: Path) -> None:
        orch, input_dir = _make_orchestrator(
            tmp_path, {"idem.html": "NODE_A"}
        )
        make_html_with_iso_timestamps(input_dir / "idem.html", n_rows=4)

        manifest1 = orch.run()
        assert manifest1.files_success == 1

        manifest2 = orch.run()
        # Second run: file unchanged → skipped
        assert manifest2.files_skipped == 1
        assert manifest2.total_records_stored == 4  # comes from existing Parquet

    def test_force_reprocesses_unchanged(self, tmp_path: Path) -> None:
        orch, input_dir = _make_orchestrator(
            tmp_path, {"force.html": "NODE_A"}, force=True
        )
        make_html_with_iso_timestamps(input_dir / "force.html", n_rows=4)

        manifest1 = orch.run()
        manifest2 = orch.run()
        # Force=True: always re-writes, never skips
        assert manifest2.files_success == 1
        assert manifest2.files_skipped == 0


class TestOrchestratorMissingConfig:
    def test_missing_mapping_config(self, tmp_path: Path) -> None:
        import flightstory.config as cfg
        import flightstory.storage as storage

        input_dir = tmp_path / "input_html"
        input_dir.mkdir()
        manifests_dir = tmp_path / "manifests"
        manifests_dir.mkdir()
        nodes_dir = tmp_path / "nodes"
        nodes_dir.mkdir()
        db_dir = tmp_path / "database"
        db_dir.mkdir()

        cfg.INPUT_HTML_DIR = input_dir
        cfg.NODES_DIR = nodes_dir
        cfg.MANIFESTS_DIR = manifests_dir
        cfg.RAW_ARCHIVE_DIR = tmp_path / "raw_archive"
        cfg.DATABASE_DIR = db_dir
        cfg.DUCKDB_PATH = db_dir / "test.duckdb"
        storage.NODES_DIR = nodes_dir

        from flightstory.orchestrator import IngestionOrchestrator
        orch = IngestionOrchestrator(
            input_dir=input_dir,
            mapping_config=tmp_path / "nonexistent_mapping.json",
        )
        manifest = orch.run()
        assert manifest.status == "failed"


class TestOrchestratorRecordCounts:
    def test_duckdb_counts_match_manifest(self, tmp_path: Path) -> None:
        """DuckDB stored counts should match the manifest totals."""
        import duckdb
        import flightstory.config as cfg
        import flightstory.storage as storage

        orch, input_dir = _make_orchestrator(
            tmp_path,
            {"count_a.html": "NODE_A", "count_b.html": "NODE_B"},
        )
        make_html_with_iso_timestamps(input_dir / "count_a.html", n_rows=3)
        make_html_with_iso_timestamps(input_dir / "count_b.html", n_rows=4)
        manifest = orch.run()

        conn = duckdb.connect(str(cfg.DUCKDB_PATH))
        from flightstory.storage import query_record_counts
        counts = query_record_counts(conn)
        conn.close()

        db_total = sum(counts.values())
        assert db_total == manifest.total_records_stored


class TestOrchestratorParallel:
    def test_parallel_ingestion_multi_files(self, tmp_path: Path) -> None:
        """Parallel ingestion with 4 workers processes multiple files successfully."""
        orch, input_dir = _make_orchestrator(
            tmp_path,
            {
                "p1.html": "NODE_A",
                "p2.html": "NODE_A",
                "p3.html": "NODE_B",
                "p4.html": "NODE_C",
            },
        )
        orch.workers = 4

        for name, n in [("p1.html", 5), ("p2.html", 4), ("p3.html", 6), ("p4.html", 3)]:
            make_html_with_iso_timestamps(input_dir / name, n_rows=n)

        manifest = orch.run()
        assert manifest.status == "success"
        assert manifest.files_success == 4
        assert manifest.total_records_stored == 18
        assert len(manifest.file_outcomes) == 4
        # Deterministic sorting in manifest outcomes
        assert [o.filename for o in manifest.file_outcomes] == ["p1.html", "p2.html", "p3.html", "p4.html"]

    def test_auto_adaptive_workers_run(self, tmp_path: Path) -> None:
        """When workers=None, orchestrator auto-tunes worker count dynamically."""
        orch, input_dir = _make_orchestrator(
            tmp_path,
            {"a.html": "NODE_A", "b.html": "NODE_B"},
        )
        orch.workers = None  # auto mode

        make_html_with_iso_timestamps(input_dir / "a.html", n_rows=3)
        make_html_with_iso_timestamps(input_dir / "b.html", n_rows=3)

        manifest = orch.run()
        assert manifest.status == "success"
        assert manifest.files_success == 2
        assert manifest.total_records_stored == 6


class TestComputeOptimalWorkers:
    def test_single_file_yields_one_worker(self) -> None:
        from flightstory.discovery import FileRecord
        from flightstory.orchestrator import compute_optimal_workers

        tasks = [(FileRecord(path=Path("f.html"), size_bytes=1000, sha256="1"), "NODE_A")]
        assert compute_optimal_workers(tasks, None) == 1

    def test_manual_override_respected(self) -> None:
        from flightstory.discovery import FileRecord
        from flightstory.orchestrator import compute_optimal_workers

        tasks = [
            (FileRecord(path=Path(f"f{i}.html"), size_bytes=1000, sha256=str(i)), "NODE_A")
            for i in range(10)
        ]
        assert compute_optimal_workers(tasks, requested_workers=3) == 3

    def test_override_clamped_to_task_count(self) -> None:
        from flightstory.discovery import FileRecord
        from flightstory.orchestrator import compute_optimal_workers

        tasks = [(FileRecord(path=Path("f.html"), size_bytes=1000, sha256="1"), "NODE_A")]
        # User asks for 8 workers for 1 file -> clamps to 1
        assert compute_optimal_workers(tasks, requested_workers=8) == 1
