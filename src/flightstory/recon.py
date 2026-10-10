"""
Phase 2 — HTML Reconnaissance Module.

Inspects HTML files and produces a detailed structural report without
performing full ingestion.  The report answers:

- How many tables are in each file?
- What are the column names and dimensions?
- Which columns look like timestamps (by name and by value)?
- What timestamp formats and precisions are present?
- How many rows have parseable vs unparseable timestamps?
- Are there structural anomalies (missing headers, empty tables, etc.)?

Output is a machine-readable JSON report plus an optional human-readable
text summary.  Nothing is written to the ingestion store.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

from .timestamps import (
    confirm_timestamp_column,
    is_candidate_timestamp_column,
    parse_timestamp,
)
from .models import TimestampParseStatus

log = logging.getLogger(__name__)

# How many rows to fully sample per table
_FULL_SAMPLE = 20
# How many rows to scan for timestamp value statistics
_TS_STAT_ROWS = 200


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ColumnInfo:
    name: str
    is_ts_name_hint: bool          # name looks like a timestamp column
    ts_confirmed: bool             # values confirmed as timestamps
    ts_confidence: float           # fraction of non-empty rows that parsed
    ts_parse_status_counts: dict[str, int] = field(default_factory=dict)
    ts_example_raw: list[str] = field(default_factory=list)
    ts_example_normalized: list[str] = field(default_factory=list)
    sample_values: list[str | None] = field(default_factory=list)


@dataclass
class TableInfo:
    table_id: str
    row_count: int
    col_count: int
    headers: list[str]
    headers_source: str            # "thead", "th_first_row", "td_first_row", "none"
    columns: list[ColumnInfo] = field(default_factory=list)
    has_confirmed_ts_col: bool = False
    confirmed_ts_col: str | None = None
    ts_col_confidence: float = 0.0
    rows_with_ts: int = 0
    rows_without_ts: int = 0
    rows_ts_invalid: int = 0
    anomalies: list[str] = field(default_factory=list)
    skipped_reason: str | None = None


@dataclass
class FileReconReport:
    filename: str
    filepath: str
    file_size_bytes: int
    table_count: int
    tables: list[TableInfo] = field(default_factory=list)
    file_error: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class ReconReport:
    """Top-level report covering all inspected files."""

    input_dir: str
    files_inspected: int
    files_errored: int
    total_tables: int
    total_tables_with_ts: int
    total_tables_without_ts: int
    file_reports: list[FileReconReport] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_headers(table_tag: Tag) -> tuple[list[str], str]:
    """Return (headers, source_description)."""
    thead = table_tag.find("thead")
    if thead:
        ths = thead.find_all(["th", "td"])
        if ths:
            return [th.get_text(strip=True) for th in ths], "thead"

    rows = table_tag.find_all("tr")
    if not rows:
        return [], "none"

    first = rows[0]
    ths = first.find_all("th")
    if ths:
        return [th.get_text(strip=True) for th in ths], "th_first_row"

    tds = first.find_all("td")
    if tds:
        return [td.get_text(strip=True) for td in tds], "td_first_row"

    return [], "none"


def _get_cell_values(rows: list[Tag], col_index: int, max_rows: int) -> list[str | None]:
    out: list[str | None] = []
    for row in rows[:max_rows]:
        cells = row.find_all(["td", "th"])
        if col_index < len(cells):
            val = cells[col_index].get_text(strip=True) or None
        else:
            val = None
        out.append(val)
    return out


def _data_rows_for_recon(table_tag: Tag, has_thead: bool, first_row_is_header: bool) -> list[Tag]:
    all_rows = table_tag.find_all("tr")
    if has_thead:
        tbody = table_tag.find("tbody")
        if tbody:
            return tbody.find_all("tr")
        thead = table_tag.find("thead")
        if thead:
            skip = len(thead.find_all("tr"))
            return all_rows[skip:]
        return all_rows[1:]
    if first_row_is_header:
        return all_rows[1:]
    return all_rows


def _table_id(idx: int, table_tag: Tag) -> str:
    if table_tag.get("id"):
        return str(table_tag["id"])
    cap = table_tag.find("caption")
    if cap and cap.get_text(strip=True):
        return f"caption_{cap.get_text(strip=True)[:30].replace(' ', '_')}"
    return f"table_{idx}"


# ---------------------------------------------------------------------------
# Core inspection
# ---------------------------------------------------------------------------

def _inspect_table(idx: int, table_tag: Tag, filename: str) -> TableInfo:
    has_thead = bool(table_tag.find("thead"))
    headers, headers_source = _detect_headers(table_tag)

    first_row_is_header = (not has_thead) and (headers_source in ("th_first_row", "td_first_row"))
    data_rows = _data_rows_for_recon(table_tag, has_thead, first_row_is_header)

    tbl = TableInfo(
        table_id=_table_id(idx, table_tag),
        row_count=len(data_rows),
        col_count=len(headers),
        headers=headers,
        headers_source=headers_source,
    )

    if not data_rows:
        tbl.skipped_reason = "No data rows"
        tbl.anomalies.append("Empty table (no data rows)")
        return tbl

    if not headers:
        tbl.anomalies.append("No headers detected")
        # Still analyse the first few rows for any timestamps
        headers = [f"col_{i}" for i in range(
            len(data_rows[0].find_all(["td", "th"]))
        )]
        tbl.col_count = len(headers)

    # -- Analyse each column ------------------------------------------------
    best_ts_col: str | None = None
    best_confidence = 0.0

    for col_idx, col_name in enumerate(headers):
        # Full sample for display
        sample_vals = _get_cell_values(data_rows, col_idx, _FULL_SAMPLE)

        # Larger sample for statistics
        stat_vals = _get_cell_values(data_rows, col_idx, _TS_STAT_ROWS)
        non_empty = [v for v in stat_vals if v and v.strip()]

        name_hint = is_candidate_timestamp_column(col_name)
        confirmed, confidence, examples_norm = confirm_timestamp_column(stat_vals)

        # Gather parse status breakdown
        status_counts: dict[str, int] = {}
        raw_examples: list[str] = []
        norm_examples: list[str] = []

        for v in stat_vals[:_TS_STAT_ROWS]:
            if v and v.strip():
                result = parse_timestamp(v)
                key = result.status.value
                status_counts[key] = status_counts.get(key, 0) + 1
                if result.status == TimestampParseStatus.VALID and len(raw_examples) < 3:
                    raw_examples.append(v)
                    if result.normalized:
                        norm_examples.append(result.normalized)

        col_info = ColumnInfo(
            name=col_name,
            is_ts_name_hint=name_hint,
            ts_confirmed=confirmed,
            ts_confidence=confidence,
            ts_parse_status_counts=status_counts,
            ts_example_raw=raw_examples,
            ts_example_normalized=norm_examples,
            sample_values=sample_vals,
        )
        tbl.columns.append(col_info)

        if confidence > best_confidence:
            best_confidence = confidence
            best_ts_col = col_name if confirmed else None

    # -- Timestamp summary for the winning column ---------------------------
    tbl.has_confirmed_ts_col = best_ts_col is not None
    tbl.confirmed_ts_col = best_ts_col
    tbl.ts_col_confidence = best_confidence

    if best_ts_col is not None:
        ts_idx = headers.index(best_ts_col)
        all_ts_vals = _get_cell_values(data_rows, ts_idx, len(data_rows))
        for v in all_ts_vals:
            if not v or not v.strip():
                tbl.rows_without_ts += 1
            else:
                result = parse_timestamp(v)
                if result.status == TimestampParseStatus.VALID:
                    tbl.rows_with_ts += 1
                elif result.status == TimestampParseStatus.MISSING:
                    tbl.rows_without_ts += 1
                else:
                    tbl.rows_ts_invalid += 1
    else:
        tbl.skipped_reason = "No column with ≥50% parseable timestamps"

    # -- Structural anomalies -----------------------------------------------
    for row_idx, row in enumerate(data_rows[:10]):
        cells = row.find_all(["td", "th"])
        if len(cells) != tbl.col_count:
            tbl.anomalies.append(
                f"Row {row_idx}: {len(cells)} cells ≠ {tbl.col_count} headers"
            )

    return tbl


def inspect_file(html_path: Path) -> FileReconReport:
    """Inspect one HTML file and return a :class:`FileReconReport`."""
    try:
        size = html_path.stat().st_size
    except OSError:
        size = 0

    report = FileReconReport(
        filename=html_path.name,
        filepath=str(html_path),
        file_size_bytes=size,
        table_count=0,
    )

    try:
        with html_path.open("r", encoding="utf-8", errors="replace") as fh:
            soup = BeautifulSoup(fh, "lxml")
    except OSError as exc:
        report.file_error = str(exc)
        return report

    tables: list[Tag] = soup.find_all("table")
    report.table_count = len(tables)

    for idx, table_tag in enumerate(tables):
        try:
            tbl = _inspect_table(idx, table_tag, html_path.name)
            report.tables.append(tbl)
        except Exception as exc:  # noqa: BLE001
            report.warnings.append(f"Table {idx}: inspection failed: {exc}")
            log.warning("[%s] Table %d inspection failed: %s", html_path.name, idx, exc)

    return report


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class HtmlRecon:
    """
    HTML reconnaissance engine.

    Usage::

        recon = HtmlRecon(input_dir=Path("data/input_html"))
        report = recon.run()
        recon.save_json(report, Path("recon_report.json"))
        recon.print_summary(report)
    """

    def __init__(self, input_dir: Path) -> None:
        self.input_dir = input_dir

    def run(self) -> ReconReport:
        """Inspect all HTML files in ``self.input_dir`` and return a report."""
        html_files = sorted(
            p for p in self.input_dir.rglob("*")
            if p.suffix.lower() in {".html", ".htm"} and p.is_file()
        )

        file_reports: list[FileReconReport] = []
        errored = 0

        for html_path in html_files:
            log.info("Inspecting: %s", html_path.name)
            fr = inspect_file(html_path)
            file_reports.append(fr)
            if fr.file_error:
                errored += 1

        total_tables = sum(fr.table_count for fr in file_reports)
        total_with_ts = sum(
            sum(1 for t in fr.tables if t.has_confirmed_ts_col)
            for fr in file_reports
        )

        return ReconReport(
            input_dir=str(self.input_dir),
            files_inspected=len(html_files),
            files_errored=errored,
            total_tables=total_tables,
            total_tables_with_ts=total_with_ts,
            total_tables_without_ts=total_tables - total_with_ts,
            file_reports=file_reports,
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    @staticmethod
    def save_json(report: ReconReport, output_path: Path) -> None:
        """Save *report* as a JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(report)
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False, default=str)
        log.info("Recon report saved to %s", output_path)

    @staticmethod
    def print_summary(report: ReconReport, *, width: int = 72) -> None:
        """Print a human-readable summary of *report*."""
        sep = "=" * width
        thin = "-" * width

        print(sep)
        print("FlightStory HTML RECONNAISSANCE REPORT")
        print(sep)
        print(f"Input dir   : {report.input_dir}")
        print(f"Files found : {report.files_inspected}  (errors: {report.files_errored})")
        print(f"Tables total: {report.total_tables}")
        print(
            f"  with timestamp col : {report.total_tables_with_ts}"
        )
        print(
            f"  without timestamp  : {report.total_tables_without_ts}"
        )

        for fr in report.file_reports:
            print(thin)
            print(f"FILE: {fr.filename}  ({fr.file_size_bytes:,} bytes)")
            if fr.file_error:
                print(f"  ERROR: {fr.file_error}")
                continue
            print(f"  Tables: {fr.table_count}")
            for tbl in fr.tables:
                ts_indicator = "+" if tbl.has_confirmed_ts_col else "-"
                print(
                    f"  [{ts_indicator}] {tbl.table_id}: "
                    f"{tbl.row_count} rows x {tbl.col_count} cols"
                )
                if tbl.confirmed_ts_col:
                    print(
                        f"      ts_col='{tbl.confirmed_ts_col}'  "
                        f"confidence={tbl.ts_col_confidence:.0%}  "
                        f"valid={tbl.rows_with_ts}  "
                        f"missing={tbl.rows_without_ts}  "
                        f"invalid={tbl.rows_ts_invalid}"
                    )
                if tbl.skipped_reason:
                    print(f"      SKIPPED: {tbl.skipped_reason}")
                if tbl.anomalies:
                    for a in tbl.anomalies[:3]:
                        print(f"      [!] {a}")
            if fr.warnings:
                for w in fr.warnings:
                    print(f"  [!] WARNING: {w}")

        print(sep)
