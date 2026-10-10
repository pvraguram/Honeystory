"""
Module D — Timestamp preservation and normalisation.

Design rules (non-negotiable):
1. ``timestamp_raw`` is ALWAYS the unmodified cell string.
2. Millisecond and sub-millisecond precision is never rounded away.
3. Timezone information is never invented.  Naive timestamps stay naive.
4. Parsing failures produce TimestampParseStatus.INVALID with a reason;
   the originating record is still kept intact.
5. Empty / None cells produce TimestampParseStatus.MISSING — distinct from
   a cell that has content but cannot be parsed.
6. No time-window grouping, correlation, or cross-node sequencing here.

Supported formats (discovered heuristically; expand as real data arrives):
- ISO-8601 variants: 2024-01-15T12:34:56.789, 2024-01-15 12:34:56.789Z, …
- Date-only: 2024-01-15
- Compact: 20240115T123456, 20240115123456
- Unix timestamps (int seconds, int milliseconds, float seconds)
- Common aviation formats: DD/MM/YYYY HH:MM:SS.mmm, MM/DD/YYYY HH:MM:SS, …
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .models import TimestampParseStatus

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class TimestampResult:
    """Outcome of one normalisation attempt."""

    raw: str | None
    """Exact original cell text — preserved regardless of parse outcome."""

    normalized: str | None
    """ISO-8601 string if parsing succeeded, else None."""

    status: TimestampParseStatus

    error: str | None = None
    """Human-readable reason for INVALID or AMBIGUOUS status."""


# ---------------------------------------------------------------------------
# Format patterns (ordered from most to least specific)
# ---------------------------------------------------------------------------

# Precompile patterns once.  Each entry is (regex, strptime_format | None,
# special_handler_name | None).  When strptime_format is None the handler
# takes over.

_PATTERNS: list[tuple[re.Pattern, str | None, str | None]] = []


def _add(pattern: str, fmt: str | None = None, handler: str | None = None) -> None:
    _PATTERNS.append((re.compile(pattern, re.ASCII), fmt, handler))


# ISO-8601 with T separator and optional timezone
_add(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?"                   # optional fractional seconds
    r"(?:Z|[+-]\d{2}:?\d{2})?$",   # optional timezone
    handler="iso8601",
)

# Aviation format: YYYY-MM-DD HH:MM:SS AM/PM (optional fractional seconds)
_add(
    r"^\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\s+[APap][Mm]$",
    handler="ymd_hms_ampm",
)

# Date-only ISO
_add(r"^\d{4}-\d{2}-\d{2}$", "%Y-%m-%d")

# Compact ISO without separators: 20240115T123456 or 20240115T123456.789
_add(
    r"^\d{8}T\d{6}(?:\.\d+)?(?:Z|[+-]\d{4})?$",
    handler="compact_iso",
)

# DD/MM/YYYY HH:MM:SS(.mmm)
_add(
    r"^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?$",
    handler="dmy_hms",
)

# MM/DD/YYYY HH:MM:SS(.mmm) — same regex; handler tries both orders
_add(
    r"^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?$",
    handler="mdy_hms",
)

# DD-MON-YYYY HH:MM:SS  (e.g. 15-JAN-2024 12:34:56)
_add(
    r"^\d{2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?$",
    handler="dmonY_hms",
)

# Unix integer seconds (10 digits) or milliseconds (13 digits)
_add(r"^\d{10}$", handler="unix_sec")
_add(r"^\d{13}$", handler="unix_ms")

# Unix float seconds (e.g. 1705312496.789)
_add(r"^\d{10}\.\d+$", handler="unix_float")


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _iso8601(raw: str) -> str:
    """
    Parse an ISO-8601 string preserving sub-second precision.

    Uses ``datetime.fromisoformat`` (Python 3.11+ accepts 'Z' suffix).
    Returns the value normalised to ISO-8601 with the original precision.
    """
    from datetime import datetime, timezone

    s = raw.strip()
    # Python 3.10 doesn't accept 'Z'; normalise for compatibility
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    dt = datetime.fromisoformat(s)
    return dt.isoformat(timespec="microseconds")


def _compact_iso(raw: str) -> str:
    from datetime import datetime

    s = raw.strip()
    # Normalise: 20240115T123456.789Z → parseable
    s2 = re.sub(r"[+-]\d{4}$", "", s)  # strip bare offset (+0530)
    has_tz = s != s2 or s.endswith("Z")
    if s2.endswith("Z"):
        s2 = s2[:-1]
    # Inject separators
    core = s2[:8] + "T" + s2[9:] if "T" in s2 else s2[:8] + "T" + s2[8:]
    date_part = core[:8]
    time_part = core[9:] if "T" in core else core[8:]
    fmt_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
    fmt_time = f"{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
    frac = ""
    if "." in time_part:
        frac = "." + time_part.split(".", 1)[1]
    assembled = f"{fmt_date}T{fmt_time}{frac}"
    from datetime import datetime
    dt = datetime.fromisoformat(assembled)
    return dt.isoformat(timespec="microseconds")


def _dmy_hms(raw: str) -> str:
    from datetime import datetime
    parts = raw.strip().split()
    date_part, time_part = parts[0], parts[1]
    d, m, y = date_part.split("/")
    if int(m) > 12:
        raise ValueError(f"Month {m} out of range for DD/MM/YYYY")
    frac = ""
    if "." in time_part:
        time_part, frac = time_part.split(".", 1)
        frac = f".{frac}"
    assembled = f"{y}-{m}-{d}T{time_part}{frac}"
    dt = datetime.fromisoformat(assembled)
    return dt.isoformat(timespec="microseconds")


def _mdy_hms(raw: str) -> str:
    from datetime import datetime
    parts = raw.strip().split()
    date_part, time_part = parts[0], parts[1]
    m, d, y = date_part.split("/")
    if int(m) > 12:
        raise ValueError(f"Month {m} out of range for MM/DD/YYYY")
    frac = ""
    if "." in time_part:
        time_part, frac = time_part.split(".", 1)
        frac = f".{frac}"
    assembled = f"{y}-{m}-{d}T{time_part}{frac}"
    dt = datetime.fromisoformat(assembled)
    return dt.isoformat(timespec="microseconds")


def _dmonY_hms(raw: str) -> str:
    from datetime import datetime
    dt = datetime.strptime(raw.strip(), "%d-%b-%Y %H:%M:%S")
    return dt.isoformat(timespec="microseconds")


def _unix_sec(raw: str) -> str:
    from datetime import datetime, timezone
    dt = datetime.fromtimestamp(int(raw), tz=timezone.utc)
    return dt.isoformat(timespec="microseconds")


def _unix_ms(raw: str) -> str:
    from datetime import datetime, timezone
    dt = datetime.fromtimestamp(int(raw) / 1000.0, tz=timezone.utc)
    return dt.isoformat(timespec="microseconds")


def _unix_float(raw: str) -> str:
    from datetime import datetime, timezone
    dt = datetime.fromtimestamp(float(raw), tz=timezone.utc)
    return dt.isoformat(timespec="microseconds")


def _ymd_hms_ampm(raw: str) -> str:
    from datetime import datetime
    s = raw.strip()
    parts = s.split()
    date_part = parts[0]
    time_part = parts[1]
    ampm = parts[2].upper()
    frac = ""
    if "." in time_part:
        time_part, frac = time_part.split(".", 1)
        frac = f".{frac}"

    base_str = f"{date_part} {time_part} {ampm}"
    dt = datetime.strptime(base_str, "%Y-%m-%d %I:%M:%S %p")
    base_iso = dt.strftime("%Y-%m-%dT%H:%M:%S")
    if frac:
        return f"{base_iso}{frac}"
    return dt.isoformat(timespec="microseconds")


_HANDLER_MAP: dict[str, object] = {
    "iso8601": _iso8601,
    "compact_iso": _compact_iso,
    "dmy_hms": _dmy_hms,
    "mdy_hms": _mdy_hms,
    "dmonY_hms": _dmonY_hms,
    "unix_sec": _unix_sec,
    "unix_ms": _unix_ms,
    "unix_float": _unix_float,
    "ymd_hms_ampm": _ymd_hms_ampm,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_timestamp(raw: str | None) -> TimestampResult:
    """
    Attempt to normalise *raw* into a consistent ISO-8601 representation.

    The original string is preserved in the returned ``TimestampResult.raw``
    regardless of success or failure.

    Parameters
    ----------
    raw : str | None
        The exact cell value from the HTML table.  ``None`` or whitespace-
        only values produce ``TimestampParseStatus.MISSING``.

    Returns
    -------
    TimestampResult
        Always returned (never raises).
    """
    # -- MISSING --------------------------------------------------------
    if raw is None or raw.strip() == "":
        return TimestampResult(
            raw=raw,
            normalized=None,
            status=TimestampParseStatus.MISSING,
        )

    stripped = raw.strip()

    # -- Try each pattern in order ----------------------------------------
    successes: list[str] = []
    last_error: str | None = None

    seen_handlers: set[str] = set()

    for pattern, fmt, handler_name in _PATTERNS:
        if not pattern.match(stripped):
            continue

        # Deduplicate same-handler matches (e.g. DD/MM and MM/DD same regex)
        key = handler_name or fmt or "unknown"
        if key in seen_handlers:
            continue
        seen_handlers.add(key)

        try:
            if handler_name:
                fn = _HANDLER_MAP[handler_name]
                normalized = fn(stripped)  # type: ignore[operator]
            elif fmt:
                from datetime import datetime
                normalized = datetime.strptime(stripped, fmt).isoformat(
                    timespec="microseconds"
                )
            else:
                continue
            successes.append(normalized)
        except (ValueError, KeyError, OverflowError, OSError) as exc:
            last_error = str(exc)

    if len(successes) == 1:
        return TimestampResult(
            raw=raw,
            normalized=successes[0],
            status=TimestampParseStatus.VALID,
        )
    if len(successes) > 1:
        # Multiple distinct interpretations — flag as ambiguous
        if len(set(successes)) == 1:
            # All handlers agree — treat as valid
            return TimestampResult(
                raw=raw,
                normalized=successes[0],
                status=TimestampParseStatus.VALID,
            )
        return TimestampResult(
            raw=raw,
            normalized=successes[0],  # keep first; caller can inspect error
            status=TimestampParseStatus.AMBIGUOUS,
            error=f"Multiple interpretations: {successes}",
        )

    return TimestampResult(
        raw=raw,
        normalized=None,
        status=TimestampParseStatus.INVALID,
        error=last_error or "No pattern matched",
    )


# ---------------------------------------------------------------------------
# Heuristic: is a column a candidate timestamp column?
# ---------------------------------------------------------------------------

# Words that suggest a timestamp column by name
_TS_NAME_HINTS: frozenset[str] = frozenset(
    {
        "time", "timestamp", "datetime", "date", "ts",
        "recorded_at", "logged_at", "event_time", "utc",
        "zulu", "epoch", "toc", "event_date",
    }
)

# Minimum fraction of non-empty rows that must parse successfully for a column
# to be confirmed as a timestamp column during reconnaissance.
MIN_TIMESTAMP_CONFIDENCE: float = 0.50


def is_candidate_timestamp_column(col_name: str) -> bool:
    """
    Return True if *col_name* looks like a timestamp column by name alone.

    This is a weak heuristic used only in the initial reconnaissance scan.
    The extraction pipeline validates actual cell values before committing.
    """
    lower = col_name.lower().replace("-", "_").replace(" ", "_")
    return any(hint in lower for hint in _TS_NAME_HINTS)


def confirm_timestamp_column(
    values: list[str | None],
    *,
    min_confidence: float = MIN_TIMESTAMP_CONFIDENCE,
) -> tuple[bool, float, list[str]]:
    """
    Validate whether *values* from a column are genuinely timestamps.

    Parameters
    ----------
    values : list[str | None]
        Sample cell values (up to ~100 rows is sufficient).
    min_confidence : float
        Fraction of non-empty rows that must parse successfully.

    Returns
    -------
    (confirmed, confidence, example_normalized)
        confirmed : bool
        confidence : fraction of non-empty rows that parsed
        example_normalized : up to 3 normalised examples
    """
    non_empty = [v for v in values if v and v.strip()]
    if not non_empty:
        return False, 0.0, []

    parsed = [parse_timestamp(v) for v in non_empty]
    valid_count = sum(
        1 for r in parsed if r.status == TimestampParseStatus.VALID
    )
    confidence = valid_count / len(non_empty)
    examples = [
        r.normalized
        for r in parsed[:10]
        if r.status == TimestampParseStatus.VALID and r.normalized
    ][:3]

    return confidence >= min_confidence, confidence, examples
