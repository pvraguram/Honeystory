"""
Module E — Common record representation.

Every extracted row, regardless of source HTML schema, is wrapped in an
``IngestionRecord``. The original column names and cell values are stored
verbatim inside ``original_record`` (a plain dict) so heterogeneous tables
never lose fields. Shared metadata fields are queryable directly in Parquet
and DuckDB without unpacking JSON.

Design constraints:
- No field coercion of ``original_record`` values.
- timestamp_raw is always the exact string from the HTML cell.
- timestamp_normalized may be None when parsing fails or the value is absent.
- timestamp_parse_status discriminates missing / valid / invalid / ambiguous.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TimestampParseStatus(str, Enum):
    """Outcome of timestamp normalisation for a single record."""

    VALID = "valid"          # Parsed successfully; timestamp_normalized is set
    MISSING = "missing"      # Cell was empty / None; no timestamp to parse
    INVALID = "invalid"      # Cell had content but could not be parsed
    AMBIGUOUS = "ambiguous"  # Multiple plausible parses; original preserved


@dataclass
class IngestionRecord:
    """
    One row extracted from one HTML table, enriched with ingestion metadata.

    Parameters
    ----------
    node_id : str
        Identifier from the explicit node-mapping configuration.
    source_file : str
        Absolute path of the originating HTML file.
    source_file_hash : str
        SHA-256 hex digest of the source file at ingestion time.
    source_table_id : str
        Human-readable table identifier (e.g. ``"table_0"`` or a caption).
    source_row_number : int
        0-based row index within the source table (header excluded).
    timestamp_raw : str | None
        Exact cell text of the candidate timestamp column, including
        milliseconds and any trailing characters as they appeared in the HTML.
    timestamp_normalized : str | None
        ISO-8601 string produced by normalisation, or ``None``.
    timestamp_parse_status : TimestampParseStatus
        Outcome of the normalisation attempt.
    timestamp_parse_error : str | None
        Error message when status is INVALID or AMBIGUOUS.
    original_record : dict[str, Any]
        Mapping of original column header → raw cell value for every column
        in the source row.  Keys are the exact header strings; values are
        always strings (or None for empty cells).
    workspace_id : str | None
        Populated by the future UI layer; None during standalone ingestion.
    event_id : str
        UUID4 assigned at extraction time.  Stable across re-reads of the
        same Parquet batch; not a content-based hash.
    """

    node_id: str
    source_file: str
    source_file_hash: str
    source_table_id: str
    source_row_number: int
    timestamp_raw: str | None
    timestamp_normalized: str | None
    timestamp_parse_status: TimestampParseStatus
    original_record: dict[str, Any]

    # Optional / derived fields
    timestamp_parse_error: str | None = None
    workspace_id: str | None = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Return a flat dict suitable for building a pandas DataFrame row.

        ``original_record`` is serialised as a JSON string so it can be
        stored in a single Parquet column without a nested schema.
        """
        import json

        return {
            "event_id": self.event_id,
            "workspace_id": self.workspace_id,
            "node_id": self.node_id,
            "source_file": self.source_file,
            "source_file_hash": self.source_file_hash,
            "source_table_id": self.source_table_id,
            "source_row_number": self.source_row_number,
            "timestamp_raw": self.timestamp_raw,
            "timestamp_normalized": self.timestamp_normalized,
            "timestamp_parse_status": self.timestamp_parse_status.value,
            "timestamp_parse_error": self.timestamp_parse_error,
            "original_record": json.dumps(
                self.original_record, ensure_ascii=False, default=str
            ),
        }

    @classmethod
    def column_dtypes(cls) -> dict[str, str]:
        """
        Return the preferred pandas dtype string for each column.

        Used when constructing DataFrames from lists of records so that
        Parquet writes use consistent types across batches.
        """
        return {
            "event_id": "string",
            "workspace_id": "string",
            "node_id": "string",
            "source_file": "string",
            "source_file_hash": "string",
            "source_table_id": "string",
            "source_row_number": "int64",
            "timestamp_raw": "string",
            "timestamp_normalized": "string",
            "timestamp_parse_status": "string",
            "timestamp_parse_error": "string",
            "original_record": "string",
        }
