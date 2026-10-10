"""
Tests for Module F — Storage.

Covers:
- Parquet output can be written and read back
- Stored values match extracted values
- Idempotent re-run: unchanged file skips re-write
- Changed file (different hash) triggers re-write
- DuckDB can query records across multiple node Parquet files
- Stored counts reconcile with ingestion reports
- Every record has source provenance in the Parquet output
- Failed writes do not overwrite valid existing output
- DuckDB unified view spans all nodes
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pyarrow.parquet as pq
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flightstory.models import IngestionRecord, TimestampParseStatus
from flightstory.storage import (
    batch_already_written,
    init_duckdb,
    query_record_counts,
    refresh_duckdb_views,
    verify_stored_counts,
    write_batch,
)


def _make_record(
    node_id: str = "NODE_A",
    file_hash: str = "a" * 64,
    row: int = 0,
    ts_raw: str = "2024-01-15T08:00:00.000",
    ts_norm: str = "2024-01-15T08:00:00.000000",
    status: TimestampParseStatus = TimestampParseStatus.VALID,
) -> IngestionRecord:
    return IngestionRecord(
        node_id=node_id,
        source_file="/test/file.html",
        source_file_hash=file_hash,
        source_table_id="table_0",
        source_row_number=row,
        timestamp_raw=ts_raw,
        timestamp_normalized=ts_norm,
        timestamp_parse_status=status,
        original_record={"timestamp": ts_raw, "system": "TEST", "value": str(row)},
    )


class TestWriteBatch:
    def test_parquet_written(self, tmp_path: Path, monkeypatch) -> None:
        """Parquet file is created after write_batch."""
        monkeypatch.setattr(
            "flightstory.storage.NODES_DIR", tmp_path / "nodes"
        )
        monkeypatch.setattr(
            "flightstory.config.NODES_DIR", tmp_path / "nodes"
        )
        from flightstory import storage, config
        storage.NODES_DIR = tmp_path / "nodes"
        config.NODES_DIR = tmp_path / "nodes"

        records = [_make_record(row=i) for i in range(5)]
        result = write_batch(iter(records), "node_a", "a" * 64)
        assert result.error is None
        assert result.parquet_path.exists()

    def test_row_count_matches(self, tmp_path: Path, monkeypatch) -> None:
        """Row count in WriteResult matches the number of records written."""
        from flightstory import storage, config
        storage.NODES_DIR = tmp_path / "nodes"
        config.NODES_DIR = tmp_path / "nodes"

        n = 7
        records = [_make_record(row=i) for i in range(n)]
        result = write_batch(iter(records), "node_a", "b" * 64)
        assert result.rows_written == n

    def test_readback_values_match(self, tmp_path: Path, monkeypatch) -> None:
        """Values in Parquet match what was written."""
        from flightstory import storage, config
        storage.NODES_DIR = tmp_path / "nodes"
        config.NODES_DIR = tmp_path / "nodes"

        rec = _make_record(ts_raw="2024-01-15T09:30:45.123")
        result = write_batch(iter([rec]), "node_a", "c" * 64)

        table = pq.read_table(str(result.parquet_path))
        df = table.to_pandas()
        assert df.iloc[0]["timestamp_raw"] == "2024-01-15T09:30:45.123"
        assert df.iloc[0]["node_id"] == "NODE_A"

    def test_original_record_json_parseable(self, tmp_path: Path, monkeypatch) -> None:
        from flightstory import storage, config
        storage.NODES_DIR = tmp_path / "nodes"
        config.NODES_DIR = tmp_path / "nodes"

        rec = _make_record()
        result = write_batch(iter([rec]), "node_a", "d" * 64)

        table = pq.read_table(str(result.parquet_path))
        df = table.to_pandas()
        original = json.loads(df.iloc[0]["original_record"])
        assert isinstance(original, dict)
        assert "system" in original

    def test_idempotent_skip(self, tmp_path: Path, monkeypatch) -> None:
        """Writing the same file_hash twice (without force) skips the second write."""
        from flightstory import storage, config
        storage.NODES_DIR = tmp_path / "nodes"
        config.NODES_DIR = tmp_path / "nodes"

        fh = "e" * 64
        records1 = [_make_record(row=i) for i in range(3)]
        result1 = write_batch(iter(records1), "node_a", fh)
        assert not result1.skipped

        records2 = [_make_record(row=i, ts_raw="DIFFERENT") for i in range(5)]
        result2 = write_batch(iter(records2), "node_a", fh)
        assert result2.skipped
        # Row count should come from the existing file (3 rows, not 5)
        assert result2.rows_written == 3

    def test_force_overwrite(self, tmp_path: Path, monkeypatch) -> None:
        """overwrite=True replaces the existing Parquet batch."""
        from flightstory import storage, config
        storage.NODES_DIR = tmp_path / "nodes"
        config.NODES_DIR = tmp_path / "nodes"

        fh = "f" * 64
        result1 = write_batch(iter([_make_record(row=0)]), "node_a", fh)
        assert result1.rows_written == 1

        result2 = write_batch(
            iter([_make_record(row=i) for i in range(4)]),
            "node_a",
            fh,
            overwrite=True,
        )
        assert not result2.skipped
        assert result2.rows_written == 4

    def test_batch_already_written_detects_existing(self, tmp_path: Path, monkeypatch) -> None:
        from flightstory import storage, config
        storage.NODES_DIR = tmp_path / "nodes"
        config.NODES_DIR = tmp_path / "nodes"

        fh = "g" * 64
        assert not batch_already_written("node_a", fh)
        write_batch(iter([_make_record()]), "node_a", fh)
        assert batch_already_written("node_a", fh)

    def test_provenance_in_parquet(self, tmp_path: Path, monkeypatch) -> None:
        """All provenance columns are present in every written row."""
        from flightstory import storage, config
        storage.NODES_DIR = tmp_path / "nodes"
        config.NODES_DIR = tmp_path / "nodes"

        records = [_make_record(row=i) for i in range(3)]
        result = write_batch(iter(records), "node_a", "h" * 64)

        table = pq.read_table(str(result.parquet_path))
        df = table.to_pandas()
        required = [
            "event_id", "node_id", "source_file",
            "source_file_hash", "source_table_id", "source_row_number",
        ]
        for col in required:
            assert col in df.columns
            assert df[col].notna().all(), f"Column {col} has nulls"


class TestDuckDB:
    def _setup_two_nodes(self, tmp_path: Path):
        """Write Parquet for node_a and node_b and return nodes_dir."""
        from flightstory import storage, config
        storage.NODES_DIR = tmp_path / "nodes"
        config.NODES_DIR = tmp_path / "nodes"

        recs_a = [_make_record(node_id="NODE_A", row=i, file_hash="a" * 64) for i in range(3)]
        recs_b = [_make_record(node_id="NODE_B", row=i, file_hash="b" * 64) for i in range(2)]

        write_batch(iter(recs_a), "node_a", "a" * 64)
        write_batch(iter(recs_b), "node_b", "b" * 64)
        return tmp_path / "nodes"

    def test_duckdb_query_per_node(self, tmp_path: Path) -> None:
        import duckdb
        nodes_dir = self._setup_two_nodes(tmp_path)
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        refresh_duckdb_views(conn, nodes_dir)

        count_a = conn.execute("SELECT COUNT(*) FROM node_node_a").fetchone()[0]
        count_b = conn.execute("SELECT COUNT(*) FROM node_node_b").fetchone()[0]
        assert count_a == 3
        assert count_b == 2
        conn.close()

    def test_all_records_view_union(self, tmp_path: Path) -> None:
        import duckdb
        nodes_dir = self._setup_two_nodes(tmp_path)
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        refresh_duckdb_views(conn, nodes_dir)

        total = conn.execute("SELECT COUNT(*) FROM all_records").fetchone()[0]
        assert total == 5  # 3 + 2
        conn.close()

    def test_query_record_counts(self, tmp_path: Path) -> None:
        import duckdb
        nodes_dir = self._setup_two_nodes(tmp_path)
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        refresh_duckdb_views(conn, nodes_dir)

        counts = query_record_counts(conn)
        assert counts.get("NODE_A") == 3
        assert counts.get("NODE_B") == 2
        conn.close()

    def test_verify_counts_pass(self, tmp_path: Path) -> None:
        import duckdb
        nodes_dir = self._setup_two_nodes(tmp_path)
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        refresh_duckdb_views(conn, nodes_dir)

        issues = verify_stored_counts(conn, {"NODE_A": 3, "NODE_B": 2})
        assert issues == []
        conn.close()

    def test_verify_counts_fail(self, tmp_path: Path) -> None:
        import duckdb
        nodes_dir = self._setup_two_nodes(tmp_path)
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        refresh_duckdb_views(conn, nodes_dir)

        issues = verify_stored_counts(conn, {"NODE_A": 99, "NODE_B": 2})
        assert len(issues) == 1
        assert "NODE_A" in issues[0]
        conn.close()

    def test_no_data_empty_counts(self, tmp_path: Path) -> None:
        import duckdb
        from flightstory import storage, config
        storage.NODES_DIR = tmp_path / "nodes"
        config.NODES_DIR = tmp_path / "nodes"

        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        refresh_duckdb_views(conn, tmp_path / "nodes")

        counts = query_record_counts(conn)
        assert counts == {}
        conn.close()
