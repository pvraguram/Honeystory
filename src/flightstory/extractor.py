"""
Module C — HTML extraction.

Responsibilities:
- Parse each HTML file independently using BeautifulSoup.
- Discover ALL tables (none silently discarded at this stage).
- For each table, extract headers and rows.
- Identify timestamp columns by validating actual cell values (not just names).
- Yield IngestionRecord objects for rows from timestamp-confirmed tables.
- Record every table that could not be classified or had extraction errors.
- Process tables in memory-safe row batches.
- Never require all files to share the same schema.

Tables without a confirmed timestamp column are still recorded in the
extraction report so they appear in manifests for later review.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, Iterator

from bs4 import BeautifulSoup, Tag

from .config import BATCH_SIZE, WORKSPACE_ID
from .models import IngestionRecord, TimestampParseStatus
from .timestamps import (
    confirm_timestamp_column,
    is_candidate_timestamp_column,
    parse_timestamp,
)

log = logging.getLogger(__name__)

# How many rows to sample when confirming a timestamp column
_SAMPLE_SIZE = 50

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class TableReport:
    """Metadata about one HTML table encountered during extraction."""

    table_id: str
    row_count: int           # data rows (header excluded)
    col_count: int
    headers: list[str]
    has_timestamp_col: bool
    timestamp_col_name: str | None
    timestamp_confidence: float
    skipped_reason: str | None = None  # set when table was NOT extracted
    extraction_errors: list[str] = field(default_factory=list)
    rows_extracted: int = 0
    rows_failed: int = 0


@dataclass
class ExtractionReport:
    """Aggregated extraction outcome for one HTML file."""

    source_file: Path
    source_file_hash: str
    node_id: str
    tables: list[TableReport] = field(default_factory=list)
    file_error: str | None = None   # set when the file itself couldn't be parsed

    @property
    def total_extracted(self) -> int:
        return sum(t.rows_extracted for t in self.tables)

    @property
    def total_failed(self) -> int:
        return sum(t.rows_failed for t in self.tables)

    @property
    def extracted_tables(self) -> list[TableReport]:
        return [t for t in self.tables if t.has_timestamp_col]

    @property
    def skipped_tables(self) -> list[TableReport]:
        return [t for t in self.tables if not t.has_timestamp_col]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_table_id(index: int, table_tag: Tag) -> str:
    """
    Derive a human-readable ID for a table.

    Prefers an HTML id attribute, caption text, or a summary attribute.
    Falls back to a positional index.
    """
    if table_tag.get("id"):
        return str(table_tag["id"])
    caption = table_tag.find("caption")
    if caption and caption.get_text(strip=True):
        raw = caption.get_text(strip=True)[:40].replace(" ", "_")
        return f"caption_{raw}"
    if table_tag.get("summary"):
        raw = str(table_tag["summary"])[:40].replace(" ", "_")
        return f"summary_{raw}"
    return f"table_{index}"


def _extract_headers(table_tag: Tag) -> list[str]:
    """
    Extract column headers from a table.

    Strategy (in order):
    1. <thead> <th> elements.
    2. First <tr> if it contains <th> elements.
    3. First <tr> <td> elements (treat first row as header if no <th> found).
    Returns [] if the table has no discernible header.
    """
    # Try thead first
    thead = table_tag.find("thead")
    if thead:
        ths = thead.find_all(["th", "td"])
        if ths:
            return [th.get_text(strip=True) for th in ths]

    # Try first row
    rows = table_tag.find_all("tr")
    if not rows:
        return []

    first_row = rows[0]
    ths = first_row.find_all("th")
    if ths:
        return [th.get_text(strip=True) for th in ths]

    # Fallback: treat first row of <td>s as header
    tds = first_row.find_all("td")
    if tds:
        return [td.get_text(strip=True) for td in tds]

    return []


def _data_rows(table_tag: Tag, has_thead: bool, first_row_is_header: bool) -> list[Tag]:
    """Return the data <tr> elements (headers excluded)."""
    all_rows: list[Tag] = table_tag.find_all("tr")

    if has_thead:
        # Rows in <tbody> (or outside thead)
        tbody = table_tag.find("tbody")
        if tbody:
            return tbody.find_all("tr")
        # No explicit tbody: skip the first row from thead
        thead_rows = table_tag.find("thead")
        if thead_rows:
            thead_tr_count = len(thead_rows.find_all("tr"))
            return all_rows[thead_tr_count:]
        return all_rows[1:]

    if first_row_is_header:
        return all_rows[1:]

    return all_rows


def _row_to_dict(
    row_tag: Tag, headers: list[str], row_index: int
) -> tuple[dict[str, str | None], list[str]]:
    """
    Convert a <tr> to a dict keyed by header name.

    Returns (record_dict, warnings).
    Handles row length mismatches by padding or truncating.
    """
    cells = row_tag.find_all(["td", "th"])
    values: list[str | None] = []
    for c in cells:
        if c.find(["ul", "ol", "li", "br"]):
            val = c.decode_contents().strip() or None
        else:
            val = c.get_text(strip=True) or None
        values.append(val)

    warnings: list[str] = []
    n_headers = len(headers)
    n_values = len(values)

    if n_values < n_headers:
        warnings.append(
            f"Row {row_index}: {n_values} cells < {n_headers} headers; padding with None"
        )
        values.extend([None] * (n_headers - n_values))
    elif n_values > n_headers:
        warnings.append(
            f"Row {row_index}: {n_values} cells > {n_headers} headers; extra cells dropped"
        )
        values = values[:n_headers]

    # If no headers at all, generate positional keys
    if not headers:
        headers = [f"col_{i}" for i in range(n_values)]

    return dict(zip(headers, values)), warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_file(
    html_path: Path,
    node_id: str,
    file_hash: str,
) -> tuple[ExtractionReport, Generator[list[IngestionRecord], None, None]]:
    """
    Parse *html_path* and return an :class:`ExtractionReport` plus a
    generator that yields batches of :class:`IngestionRecord` objects.

    The generator is lazy: records are not built until iterated.  Callers
    can consume batches without holding all records in memory.

    Parameters
    ----------
    html_path : Path
        Absolute path to the HTML source file.
    node_id : str
        Node identifier from the explicit mapping configuration.
    file_hash : str
        SHA-256 hex digest of the file (pre-computed by Module A).

    Returns
    -------
    (report, record_generator)
    """
    report = ExtractionReport(
        source_file=html_path,
        source_file_hash=file_hash,
        node_id=node_id,
    )

    # -- Parse HTML ----------------------------------------------------------
    try:
        with html_path.open("r", encoding="utf-8", errors="replace") as fh:
            soup = BeautifulSoup(fh, "lxml")
    except OSError as exc:
        report.file_error = str(exc)
        log.error("Cannot open %s: %s", html_path, exc)
        return report, _empty_gen()

    tables: list[Tag] = soup.find_all("table")

    if not tables:
        log.info("No tables found in %s", html_path.name)
        return report, _empty_gen()

    log.info("Found %d table(s) in %s", len(tables), html_path.name)

    def _record_generator() -> Generator[list[IngestionRecord], None, None]:
        for idx, table_tag in enumerate(tables):
            table_id = _make_table_id(idx, table_tag)
            tbl_report, batch_gen = _process_table(
                table_tag=table_tag,
                table_id=table_id,
                table_index=idx,
                source_file=html_path,
                file_hash=file_hash,
                node_id=node_id,
            )
            report.tables.append(tbl_report)
            if tbl_report.has_timestamp_col:
                yield from batch_gen

    return report, _record_generator()


def _empty_gen() -> Generator[list[IngestionRecord], None, None]:
    return
    yield  # make this a generator


def _process_table(
    *,
    table_tag: Tag,
    table_id: str,
    table_index: int,
    source_file: Path,
    file_hash: str,
    node_id: str,
) -> tuple[TableReport, Generator[list[IngestionRecord], None, None]]:
    """
    Inspect one HTML table and decide whether to extract records from it.
    """
    # -- Headers -------------------------------------------------------------
    has_thead = bool(table_tag.find("thead"))
    headers = _extract_headers(table_tag)
    first_row_is_header = (not has_thead) and bool(headers)

    # -- Data rows -----------------------------------------------------------
    data_rows = _data_rows(table_tag, has_thead, first_row_is_header)

    tbl_report = TableReport(
        table_id=table_id,
        row_count=len(data_rows),
        col_count=len(headers),
        headers=headers,
        has_timestamp_col=False,
        timestamp_col_name=None,
        timestamp_confidence=0.0,
    )

    if not data_rows:
        tbl_report.skipped_reason = "No data rows"
        log.debug("[%s] Table '%s': no data rows", source_file.name, table_id)
        return tbl_report, _empty_gen()

    # -- Identify timestamp column -------------------------------------------
    ts_col, ts_confidence = _find_timestamp_column(
        headers=headers,
        data_rows=data_rows,
        table_id=table_id,
        source_file_name=source_file.name,
    )

    tbl_report.timestamp_col_name = ts_col
    tbl_report.timestamp_confidence = ts_confidence
    tbl_report.has_timestamp_col = ts_col is not None

    if ts_col is None:
        tbl_report.skipped_reason = (
            "No column with ≥50% parseable timestamps found"
        )
        log.info(
            "[%s] Table '%s': skipped (no timestamp column)",
            source_file.name,
            table_id,
        )
        return tbl_report, _empty_gen()

    log.info(
        "[%s] Table '%s': extracting %d rows (ts_col='%s', confidence=%.0f%%)",
        source_file.name,
        table_id,
        len(data_rows),
        ts_col,
        ts_confidence * 100,
    )

    # -- Build record generator ----------------------------------------------
    def _gen() -> Generator[list[IngestionRecord], None, None]:
        batch: list[IngestionRecord] = []
        for row_idx, row_tag in enumerate(data_rows):
            try:
                record_dict, row_warnings = _row_to_dict(row_tag, headers, row_idx)
                if row_warnings:
                    tbl_report.extraction_errors.extend(row_warnings)

                raw_ts = record_dict.get(ts_col)
                ts_result = parse_timestamp(raw_ts)

                record = IngestionRecord(
                    node_id=node_id,
                    source_file=str(source_file),
                    source_file_hash=file_hash,
                    source_table_id=table_id,
                    source_row_number=row_idx,
                    timestamp_raw=ts_result.raw,
                    timestamp_normalized=ts_result.normalized,
                    timestamp_parse_status=ts_result.status,
                    timestamp_parse_error=ts_result.error,
                    original_record=record_dict,
                    workspace_id=WORKSPACE_ID,
                )
                batch.append(record)
                tbl_report.rows_extracted += 1

            except Exception as exc:  # noqa: BLE001
                err_msg = f"Row {row_idx}: {exc}"
                tbl_report.extraction_errors.append(err_msg)
                tbl_report.rows_failed += 1
                log.warning("[%s/%s] %s", source_file.name, table_id, err_msg)

            if len(batch) >= BATCH_SIZE:
                yield batch
                batch = []

        if batch:
            yield batch

    return tbl_report, _gen()


def _find_timestamp_column(
    headers: list[str],
    data_rows: list[Tag],
    table_id: str,
    source_file_name: str,
) -> tuple[str | None, float]:
    """
    Identify the best timestamp column in a table.

    Strategy:
    1. Collect candidate columns by name hint.
    2. If no name hints found, check ALL columns.
    3. For each candidate, sample cell values and call confirm_timestamp_column.
    4. Return the column with the highest confidence (if ≥ threshold).

    Returns
    -------
    (column_name, confidence)  — column_name is None if nothing qualifies.
    """
    if not headers:
        return None, 0.0

    # Build column → sample values map from the first _SAMPLE_SIZE rows
    col_samples: dict[str, list[str | None]] = {h: [] for h in headers}
    for row_tag in data_rows[:_SAMPLE_SIZE]:
        cells = row_tag.find_all(["td", "th"])
        values = [(c.get_text(strip=True) or None) for c in cells]
        for i, header in enumerate(headers):
            col_samples[header].append(values[i] if i < len(values) else None)

    # Step 1: candidates by name
    name_candidates = [h for h in headers if is_candidate_timestamp_column(h)]
    if not name_candidates:
        # Step 2: check every column
        log.debug(
            "[%s/%s] No name-hint columns; checking all %d columns",
            source_file_name, table_id, len(headers),
        )
        name_candidates = headers

    best_col: str | None = None
    best_confidence = 0.0

    for col in name_candidates:
        confirmed, confidence, _ = confirm_timestamp_column(col_samples[col])
        if confidence > best_confidence:
            best_confidence = confidence
            best_col = col if confirmed else None

    if best_col:
        log.debug(
            "[%s/%s] Timestamp column confirmed: '%s' (confidence=%.0f%%)",
            source_file_name, table_id, best_col, best_confidence * 100,
        )
    return best_col, best_confidence
