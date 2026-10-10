"""
Tests for the HTML Reconnaissance Module (Phase 2).

Covers:
- File size reported
- Table count reported
- Column names reported
- Timestamp column identified and confirmed
- Confidence score present
- Row counts: valid / missing / invalid timestamps
- Structural anomalies detected
- Tables without timestamps included in report (not silently dropped)
- Malformed HTML does not crash the recon
- JSON serialisation and deserialisation works
- Summary output produced without error
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flightstory.recon import HtmlRecon, inspect_file
from tests.conftest import (
    FIXTURES_DIR,
    make_html_with_iso_timestamps,
    make_html_no_timestamps,
)


class TestInspectFile:
    def test_reports_filename(self, simple_table_html: Path) -> None:
        report = inspect_file(simple_table_html)
        assert report.filename == "simple_table.html"

    def test_reports_file_size(self, simple_table_html: Path) -> None:
        report = inspect_file(simple_table_html)
        assert report.file_size_bytes > 0

    def test_reports_table_count(self, simple_table_html: Path) -> None:
        report = inspect_file(simple_table_html)
        assert report.table_count == 1

    def test_reports_column_names(self, simple_table_html: Path) -> None:
        report = inspect_file(simple_table_html)
        tbl = report.tables[0]
        assert "timestamp" in tbl.headers

    def test_timestamp_column_confirmed(self, simple_table_html: Path) -> None:
        report = inspect_file(simple_table_html)
        tbl = report.tables[0]
        assert tbl.has_confirmed_ts_col is True
        assert tbl.confirmed_ts_col == "timestamp"

    def test_confidence_score(self, simple_table_html: Path) -> None:
        report = inspect_file(simple_table_html)
        tbl = report.tables[0]
        assert tbl.ts_col_confidence >= 0.9

    def test_valid_row_count(self, simple_table_html: Path) -> None:
        report = inspect_file(simple_table_html)
        tbl = report.tables[0]
        assert tbl.rows_with_ts == 4  # 4 rows in simple_table.html

    def test_no_invalid_rows(self, simple_table_html: Path) -> None:
        report = inspect_file(simple_table_html)
        tbl = report.tables[0]
        assert tbl.rows_ts_invalid == 0

    def test_multi_table_all_reported(self, multi_table_html: Path) -> None:
        """All tables including the config table must appear in the report."""
        report = inspect_file(multi_table_html)
        assert report.table_count == 3
        assert len(report.tables) == 3

    def test_no_timestamp_table_in_report(self, multi_table_html: Path) -> None:
        report = inspect_file(multi_table_html)
        skipped = [t for t in report.tables if not t.has_confirmed_ts_col]
        assert len(skipped) >= 1  # config_params table

    def test_no_crash_on_malformed(self, malformed_html: Path) -> None:
        report = inspect_file(malformed_html)
        assert isinstance(report.table_count, int)

    def test_no_crash_on_empty(self, empty_table_html: Path) -> None:
        report = inspect_file(empty_table_html)
        assert report.table_count == 3

    def test_empty_table_anomaly_flagged(self, empty_table_html: Path) -> None:
        report = inspect_file(empty_table_html)
        empty_tables = [t for t in report.tables if t.skipped_reason]
        assert len(empty_tables) >= 2  # empty_data and totally_empty

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        report = inspect_file(tmp_path / "does_not_exist.html")
        assert report.file_error is not None

    def test_column_info_populated(self, simple_table_html: Path) -> None:
        report = inspect_file(simple_table_html)
        tbl = report.tables[0]
        assert len(tbl.columns) > 0
        ts_col_infos = [c for c in tbl.columns if c.ts_confirmed]
        assert len(ts_col_infos) == 1

    def test_sample_values_present(self, simple_table_html: Path) -> None:
        report = inspect_file(simple_table_html)
        tbl = report.tables[0]
        # The timestamp column should have sample values
        ts_col = next(c for c in tbl.columns if c.ts_confirmed)
        assert len(ts_col.sample_values) > 0

    def test_example_timestamps_normalised(self, simple_table_html: Path) -> None:
        report = inspect_file(simple_table_html)
        tbl = report.tables[0]
        ts_col = next(c for c in tbl.columns if c.ts_confirmed)
        assert len(ts_col.ts_example_normalized) > 0


class TestHtmlReconRun:
    def test_run_reports_file_count(self, tmp_input_dir: Path) -> None:
        make_html_with_iso_timestamps(tmp_input_dir / "f1.html", n_rows=3)
        make_html_with_iso_timestamps(tmp_input_dir / "f2.html", n_rows=3)
        recon = HtmlRecon(input_dir=tmp_input_dir)
        report = recon.run()
        assert report.files_inspected == 2

    def test_run_counts_ts_tables(self, tmp_input_dir: Path) -> None:
        make_html_with_iso_timestamps(tmp_input_dir / "ts.html")
        make_html_no_timestamps(tmp_input_dir / "no_ts.html")
        recon = HtmlRecon(input_dir=tmp_input_dir)
        report = recon.run()
        assert report.total_tables_with_ts == 1
        assert report.total_tables_without_ts == 1

    def test_json_roundtrip(self, tmp_input_dir: Path, tmp_path: Path) -> None:
        make_html_with_iso_timestamps(tmp_input_dir / "rt.html")
        recon = HtmlRecon(input_dir=tmp_input_dir)
        report = recon.run()
        out = tmp_path / "report.json"
        HtmlRecon.save_json(report, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["files_inspected"] == 1
        assert isinstance(data["file_reports"], list)

    def test_print_summary_no_crash(
        self, tmp_input_dir: Path, capsys: pytest.CaptureFixture
    ) -> None:
        make_html_with_iso_timestamps(tmp_input_dir / "summary.html")
        recon = HtmlRecon(input_dir=tmp_input_dir)
        report = recon.run()
        HtmlRecon.print_summary(report)
        captured = capsys.readouterr()
        assert "RECONNAISSANCE" in captured.out

    def test_empty_directory_no_crash(self, tmp_input_dir: Path) -> None:
        recon = HtmlRecon(input_dir=tmp_input_dir)
        report = recon.run()
        assert report.files_inspected == 0
        assert report.files_errored == 0
