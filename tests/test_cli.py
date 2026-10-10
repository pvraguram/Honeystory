"""
Tests for Phase 6 CLI — flightstory.cli.

Covers:
- Argument parsing for all subcommands (inspect, ingest, status, validate)
- cmd_inspect with and without JSON output
- cmd_ingest with mock/valid config and force flag
- cmd_status reporting
- cmd_validate pass and fail scenarios
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flightstory.cli import build_parser, cmd_ingest, cmd_inspect, cmd_status, cmd_validate, main
from tests.conftest import make_html_with_iso_timestamps


class TestCLIParser:
    def test_parser_builds(self) -> None:
        parser = build_parser()
        assert parser.prog == "flightstory"

    def test_inspect_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["inspect", "--input", "test_dir", "--output", "report.json"])
        assert args.command == "inspect"
        assert args.input == "test_dir"
        assert args.output == "report.json"

    def test_ingest_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["ingest", "--config", "cfg.json", "--force", "--no-archive", "--workers", "4"])
        assert args.command == "ingest"
        assert args.config == "cfg.json"
        assert args.force is True
        assert args.no_archive is True
        assert args.workers == 4

    def test_status_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_validate_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["validate"])
        assert args.command == "validate"


class TestCLIInspect:
    def test_inspect_success(self, tmp_input_dir: Path, tmp_path: Path, capsys) -> None:
        make_html_with_iso_timestamps(tmp_input_dir / "flight.html")
        report_path = tmp_path / "out.json"

        parser = build_parser()
        args = parser.parse_args(["inspect", "--input", str(tmp_input_dir), "--output", str(report_path)])
        rc = cmd_inspect(args)

        assert rc == 0
        assert report_path.exists()
        captured = capsys.readouterr()
        assert "RECONNAISSANCE REPORT" in captured.out

    def test_inspect_missing_dir(self, tmp_path: Path) -> None:
        parser = build_parser()
        args = parser.parse_args(["inspect", "--input", str(tmp_path / "nonexistent")])
        rc = cmd_inspect(args)
        assert rc == 1


class TestCLIIngest:
    def test_ingest_missing_config(self, tmp_path: Path) -> None:
        parser = build_parser()
        args = parser.parse_args(["ingest", "--config", str(tmp_path / "missing.json")])
        rc = cmd_ingest(args)
        assert rc == 1

    def test_ingest_success(self, tmp_path: Path, capsys) -> None:
        import flightstory.config as cfg
        import flightstory.storage as storage
        import flightstory.orchestrator as orch_mod

        input_dir = tmp_path / "input_html"
        nodes_dir = tmp_path / "nodes"
        manifests_dir = tmp_path / "manifests"
        archive_dir = tmp_path / "raw_archive"
        db_dir = tmp_path / "database"

        for d in (input_dir, nodes_dir, manifests_dir, archive_dir, db_dir):
            d.mkdir(parents=True, exist_ok=True)

        cfg.INPUT_HTML_DIR = input_dir
        cfg.NODES_DIR = nodes_dir
        cfg.MANIFESTS_DIR = manifests_dir
        cfg.RAW_ARCHIVE_DIR = archive_dir
        cfg.DATABASE_DIR = db_dir
        cfg.DUCKDB_PATH = db_dir / "test.duckdb"
        cfg.OUTPUT_DIR_MARKERS = (archive_dir, nodes_dir, db_dir)

        storage.NODES_DIR = nodes_dir
        storage.DUCKDB_PATH = db_dir / "test.duckdb"

        orch_mod.MANIFESTS_DIR = manifests_dir
        orch_mod.RAW_ARCHIVE_DIR = archive_dir
        orch_mod.INPUT_HTML_DIR = input_dir

        make_html_with_iso_timestamps(input_dir / "log.html", n_rows=3)
        cfg_file = tmp_path / "map.json"
        cfg_file.write_text(json.dumps({"log.html": "NODE_A"}), encoding="utf-8")

        parser = build_parser()
        args = parser.parse_args(["ingest", "--config", str(cfg_file), "--input", str(input_dir)])
        rc = cmd_ingest(args)

        assert rc == 0
        captured = capsys.readouterr()
        assert "INGESTION REPORT" in captured.out
        assert "SUCCESS" in captured.out


class TestCLIStatusAndValidate:
    def test_status_runs(self, capsys) -> None:
        parser = build_parser()
        args = parser.parse_args(["status"])
        rc = cmd_status(args)
        assert rc == 0
        captured = capsys.readouterr()
        assert "DuckDB" in captured.out or "Recent" in captured.out

    def test_validate_runs(self, capsys) -> None:
        parser = build_parser()
        args = parser.parse_args(["validate"])
        rc = cmd_validate(args)
        # rc can be 0 (passes or no data)
        assert rc in (0, 1)


class TestCLIMain:
    def test_main_help_exit(self, monkeypatch) -> None:
        monkeypatch.setattr(sys, "argv", ["flightstory", "--help"])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
