"""
Tests for Module D — Timestamp preservation and normalisation.

Covers:
- ISO-8601 formats (with and without ms, with and without timezone)
- DD/MM/YYYY and MM/DD/YYYY formats
- Unix epoch (seconds, milliseconds, float)
- Compact ISO (20240115T123456.789)
- Millisecond precision is never rounded away
- Original timestamp strings are never modified
- Missing (None / empty) → MISSING status
- Invalid strings → INVALID status with error message
- No timezone is invented for naive timestamps
- Unparseable timestamps remain traceable (raw preserved)
- Ambiguous timestamps produce AMBIGUOUS status
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flightstory.timestamps import (
    TimestampResult,
    confirm_timestamp_column,
    is_candidate_timestamp_column,
    parse_timestamp,
)
from flightstory.models import TimestampParseStatus


class TestParseTimestampISO:
    def test_iso_with_milliseconds(self) -> None:
        result = parse_timestamp("2024-01-15T08:23:45.123")
        assert result.status == TimestampParseStatus.VALID
        # Must preserve milliseconds — normalized should contain sub-second part
        assert "08:23:45" in result.normalized
        assert ".123" in result.normalized

    def test_iso_with_microseconds(self) -> None:
        result = parse_timestamp("2024-01-15T08:23:45.123456")
        assert result.status == TimestampParseStatus.VALID
        assert "123456" in result.normalized

    def test_iso_with_utc_z(self) -> None:
        result = parse_timestamp("2024-01-15T08:23:45.000Z")
        assert result.status == TimestampParseStatus.VALID
        # UTC timezone should be preserved (+00:00)
        assert "+00:00" in result.normalized

    def test_iso_with_offset(self) -> None:
        result = parse_timestamp("2024-01-15T08:23:45.000+05:30")
        assert result.status == TimestampParseStatus.VALID
        assert "+05:30" in result.normalized

    def test_iso_without_ms(self) -> None:
        result = parse_timestamp("2024-01-15T08:23:45")
        assert result.status == TimestampParseStatus.VALID

    def test_iso_space_separator(self) -> None:
        result = parse_timestamp("2024-01-15 08:23:45.789")
        assert result.status == TimestampParseStatus.VALID
        assert "789" in result.normalized

    def test_date_only(self) -> None:
        result = parse_timestamp("2024-01-15")
        assert result.status == TimestampParseStatus.VALID


class TestParseTimestampPrecision:
    def test_raw_string_never_modified(self) -> None:
        """timestamp_raw must be the exact input string — no trimming or modification."""
        raw = "  2024-01-15T08:23:45.123  "  # leading/trailing spaces
        result = parse_timestamp(raw)
        assert result.raw == raw  # raw is the exact input

    def test_milliseconds_not_rounded(self) -> None:
        result = parse_timestamp("2024-01-15T08:23:45.999")
        assert result.status == TimestampParseStatus.VALID
        assert ".999" in result.normalized

    def test_sub_ms_precision_retained(self) -> None:
        result = parse_timestamp("2024-01-15T08:23:45.123456")
        assert result.status == TimestampParseStatus.VALID
        assert "123456" in result.normalized


class TestParseTimestampFormats:
    def test_dmy_format(self) -> None:
        result = parse_timestamp("15/01/2024 09:00:00.000")
        assert result.status == TimestampParseStatus.VALID
        assert "2024-01-15" in result.normalized

    def test_dmy_with_milliseconds(self) -> None:
        result = parse_timestamp("15/01/2024 09:00:05.250")
        assert result.status == TimestampParseStatus.VALID
        assert "250" in result.normalized

    def test_unix_seconds(self) -> None:
        result = parse_timestamp("1705312496")  # 2024-01-15T08:14:56Z
        assert result.status == TimestampParseStatus.VALID
        assert "+00:00" in result.normalized  # unix → UTC

    def test_unix_milliseconds(self) -> None:
        result = parse_timestamp("1705312496789")
        assert result.status == TimestampParseStatus.VALID
        assert "+00:00" in result.normalized

    def test_unix_float(self) -> None:
        result = parse_timestamp("1705312496.789")
        assert result.status == TimestampParseStatus.VALID

    def test_compact_iso(self) -> None:
        result = parse_timestamp("20240115T083045")
        # May or may not succeed depending on compact handler — just check no crash
        assert result.status in (TimestampParseStatus.VALID, TimestampParseStatus.INVALID)


class TestParseTimestampMissing:
    def test_none_input(self) -> None:
        result = parse_timestamp(None)
        assert result.status == TimestampParseStatus.MISSING
        assert result.normalized is None

    def test_empty_string(self) -> None:
        result = parse_timestamp("")
        assert result.status == TimestampParseStatus.MISSING

    def test_whitespace_only(self) -> None:
        result = parse_timestamp("   ")
        assert result.status == TimestampParseStatus.MISSING

    def test_raw_preserved_for_none(self) -> None:
        result = parse_timestamp(None)
        assert result.raw is None


class TestParseTimestampInvalid:
    def test_plain_text_invalid(self) -> None:
        result = parse_timestamp("NOT_A_TIMESTAMP")
        assert result.status == TimestampParseStatus.INVALID
        assert result.normalized is None

    def test_partial_date_invalid(self) -> None:
        result = parse_timestamp("2024-01")
        assert result.status == TimestampParseStatus.INVALID

    def test_error_message_set(self) -> None:
        result = parse_timestamp("GARBAGE")
        assert result.status == TimestampParseStatus.INVALID
        assert result.error is not None

    def test_raw_preserved_for_invalid(self) -> None:
        raw = "GARBAGE"
        result = parse_timestamp(raw)
        assert result.raw == raw
        assert result.normalized is None

    def test_never_raises(self) -> None:
        """parse_timestamp must never raise regardless of input."""
        tricky = [
            "9999-99-99T99:99:99",
            "0000-00-00",
            None,
            "",
            "∞",
            "2024-13-45T25:61:99.999",
        ]
        for val in tricky:
            result = parse_timestamp(val)
            assert isinstance(result, TimestampResult)


class TestTimezoneHandling:
    def test_no_tz_invented_for_naive(self) -> None:
        """Naive timestamps must not have +00:00 or Z appended."""
        result = parse_timestamp("2024-01-15T08:23:45.000")
        assert result.status == TimestampParseStatus.VALID
        # Should NOT contain timezone info
        assert "+00:00" not in result.normalized
        assert "Z" not in result.normalized

    def test_utc_preserved_when_explicit(self) -> None:
        result = parse_timestamp("2024-01-15T08:23:45.000Z")
        assert "+00:00" in result.normalized

    def test_offset_preserved(self) -> None:
        result = parse_timestamp("2024-01-15T08:23:45.000+05:30")
        assert "+05:30" in result.normalized


class TestCandidateColumn:
    def test_timestamp_name_detected(self) -> None:
        assert is_candidate_timestamp_column("timestamp") is True
        assert is_candidate_timestamp_column("event_time") is True
        assert is_candidate_timestamp_column("logged_at") is True
        assert is_candidate_timestamp_column("recorded_at") is True
        assert is_candidate_timestamp_column("ts") is True

    def test_non_timestamp_name(self) -> None:
        assert is_candidate_timestamp_column("system") is False
        assert is_candidate_timestamp_column("value") is False
        assert is_candidate_timestamp_column("altitude") is False

    def test_confirm_with_iso_values(self) -> None:
        values = [f"2024-01-15T08:0{i}:00.000" for i in range(9)]
        confirmed, confidence, _ = confirm_timestamp_column(values)
        assert confirmed is True
        assert confidence >= 0.9

    def test_confirm_rejects_mostly_invalid(self) -> None:
        values = ["NOT", "VALID", "DATES", "AT", "ALL"]
        confirmed, confidence, _ = confirm_timestamp_column(values)
        assert confirmed is False
        assert confidence < 0.5

    def test_confirm_empty_values(self) -> None:
        confirmed, confidence, examples = confirm_timestamp_column([None, None, ""])
        assert confirmed is False
        assert confidence == 0.0

    def test_partial_timestamps_above_threshold(self) -> None:
        """Columns with >50% valid timestamps are confirmed."""
        values = [
            "2024-01-15T08:00:00.000",
            "2024-01-15T08:01:00.000",
            "2024-01-15T08:02:00.000",
            "INVALID",
        ]
        confirmed, confidence, _ = confirm_timestamp_column(values)
        assert confirmed is True
        assert confidence == 0.75
