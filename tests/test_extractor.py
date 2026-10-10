"""
Tests for Module C — HTML extraction.

Covers:
- Tables with recognizable timestamps are extracted
- Different schemas are handled independently
- Empty tables and missing headers are handled
- Tables without timestamps are reported (not silently dropped)
- Malformed HTML does not crash the pipeline
- Large inputs are processed without holding all data in memory
- Extraction report contains accurate counts
- Row-count mismatches (extra/missing cells) are handled gracefully
- Original column names and values are preserved
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flightstory.extractor import extract_file
from flightstory.models import TimestampParseStatus
from tests.conftest import (
    make_html_with_iso_timestamps,
    make_html_no_timestamps,
    make_large_html,
    FIXTURES_DIR,
)

NODE_ID = "TEST_NODE"
DUMMY_HASH = "a" * 64


class TestExtractSimpleTable:
    def test_records_extracted(self, simple_table_html: Path) -> None:
        report, gen = extract_file(simple_table_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        assert len(records) == 4  # 4 data rows in simple_table.html

    def test_node_id_preserved(self, simple_table_html: Path) -> None:
        _, gen = extract_file(simple_table_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        assert all(r.node_id == NODE_ID for r in records)

    def test_source_file_preserved(self, simple_table_html: Path) -> None:
        _, gen = extract_file(simple_table_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        assert all(r.source_file == str(simple_table_html) for r in records)

    def test_file_hash_preserved(self, simple_table_html: Path) -> None:
        _, gen = extract_file(simple_table_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        assert all(r.source_file_hash == DUMMY_HASH for r in records)

    def test_original_record_has_all_columns(self, simple_table_html: Path) -> None:
        """Every column from the source HTML is preserved in original_record."""
        _, gen = extract_file(simple_table_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        expected_cols = {"timestamp", "system", "event_code", "value", "unit"}
        for rec in records:
            assert set(rec.original_record.keys()) == expected_cols

    def test_row_numbers_sequential(self, simple_table_html: Path) -> None:
        _, gen = extract_file(simple_table_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        row_nums = [r.source_row_number for r in records]
        assert row_nums == list(range(len(records)))

    def test_event_ids_unique(self, simple_table_html: Path) -> None:
        _, gen = extract_file(simple_table_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        event_ids = [r.event_id for r in records]
        assert len(set(event_ids)) == len(event_ids)

    def test_timestamp_raw_unchanged(self, simple_table_html: Path) -> None:
        """timestamp_raw must be the exact string from the HTML cell."""
        _, gen = extract_file(simple_table_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        first_raw = records[0].timestamp_raw
        assert first_raw == "2024-01-15T08:23:45.123"

    def test_timestamp_status_valid(self, simple_table_html: Path) -> None:
        _, gen = extract_file(simple_table_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        assert all(
            r.timestamp_parse_status == TimestampParseStatus.VALID
            for r in records
        )


class TestExtractMultiTable:
    def test_timestamp_tables_extracted(self, multi_table_html: Path) -> None:
        report, gen = extract_file(multi_table_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        # engine_log (3 rows) + fuel_log (2 rows) = 5 records
        assert len(records) == 5

    def test_config_table_skipped(self, multi_table_html: Path) -> None:
        """The config_params table (no timestamps) should be in skipped_tables."""
        report, gen = extract_file(multi_table_html, NODE_ID, DUMMY_HASH)
        list(gen)  # consume generator
        skipped_ids = [t.table_id for t in report.skipped_tables]
        assert "config_params" in skipped_ids

    def test_total_tables_discovered(self, multi_table_html: Path) -> None:
        report, gen = extract_file(multi_table_html, NODE_ID, DUMMY_HASH)
        list(gen)
        assert len(report.tables) == 3

    def test_different_schemas_preserved(self, multi_table_html: Path) -> None:
        """Engine and fuel tables have different schemas — both preserved."""
        report, gen = extract_file(multi_table_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        schemas = {frozenset(r.original_record.keys()) for r in records}
        # Should have 2 different column sets
        assert len(schemas) == 2


class TestExtractNoTimestamp:
    def test_no_records_extracted(self, no_timestamp_html: Path) -> None:
        report, gen = extract_file(no_timestamp_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        assert len(records) == 0

    def test_table_in_report(self, no_timestamp_html: Path) -> None:
        report, gen = extract_file(no_timestamp_html, NODE_ID, DUMMY_HASH)
        list(gen)
        assert len(report.tables) == 1
        assert report.tables[0].skipped_reason is not None

    def test_total_extracted_zero(self, no_timestamp_html: Path) -> None:
        report, gen = extract_file(no_timestamp_html, NODE_ID, DUMMY_HASH)
        list(gen)
        assert report.total_extracted == 0


class TestExtractMalformed:
    def test_does_not_crash(self, malformed_html: Path) -> None:
        """Malformed HTML must not raise an exception."""
        report, gen = extract_file(malformed_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]  # just consume it
        # Should extract at least the rows with valid timestamps
        assert isinstance(records, list)

    def test_valid_rows_extracted(self, malformed_html: Path) -> None:
        """Valid timestamp rows from malformed HTML should still be extracted."""
        report, gen = extract_file(malformed_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        valid = [r for r in records if r.timestamp_parse_status == TimestampParseStatus.VALID]
        assert len(valid) >= 2  # at least the two clear ISO timestamps

    def test_invalid_timestamp_not_discarded(self, malformed_html: Path) -> None:
        """Rows with invalid timestamps are preserved with INVALID status."""
        report, gen = extract_file(malformed_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        invalid = [r for r in records if r.timestamp_parse_status == TimestampParseStatus.INVALID]
        # The "NOT_A_TIMESTAMP" row should be kept
        assert len(invalid) >= 1

    def test_original_record_has_data(self, malformed_html: Path) -> None:
        _, gen = extract_file(malformed_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        assert all(r.original_record for r in records)


class TestExtractEmptyTable:
    def test_empty_table_skipped_gracefully(self, empty_table_html: Path) -> None:
        report, gen = extract_file(empty_table_html, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        # Only the valid_after_empty table should contribute records
        assert len(records) == 1

    def test_empty_tables_in_report(self, empty_table_html: Path) -> None:
        report, gen = extract_file(empty_table_html, NODE_ID, DUMMY_HASH)
        list(gen)
        assert len(report.tables) == 3  # all 3 tables discovered


class TestSyntheticLargeFile:
    def test_large_file_processed_in_batches(self, tmp_input_dir: Path) -> None:
        """12k-row file should be processed without loading everything at once."""
        html_path = make_large_html(tmp_input_dir / "large.html", n_rows=12000)
        report, gen = extract_file(html_path, NODE_ID, DUMMY_HASH)
        total = 0
        for batch in gen:
            assert len(batch) <= 10001  # batch size + possible partial
            total += len(batch)
        assert total == 12000

    def test_all_records_have_provenance(self, tmp_input_dir: Path) -> None:
        html_path = make_html_with_iso_timestamps(tmp_input_dir / "prov.html", n_rows=20)
        _, gen = extract_file(html_path, NODE_ID, DUMMY_HASH)
        records = [r for batch in gen for r in batch]
        for r in records:
            assert r.source_file
            assert r.source_file_hash
            assert r.source_table_id
            assert r.source_row_number >= 0
