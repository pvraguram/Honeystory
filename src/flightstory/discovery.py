"""
Module A — File discovery.

Responsibilities:
- Discover supported HTML files from a configured input directory.
- Record each file's path, size, and SHA-256 content hash.
- Handle missing, unreadable, and malformed (zero-byte) files gracefully.
- Exclude generated output files (anything inside OUTPUT_DIR_MARKERS).
- Return structured FileRecord objects; never raise on individual file errors.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from .config import OUTPUT_DIR_MARKERS, SUPPORTED_EXTENSIONS

log = logging.getLogger(__name__)

# Buffer size for streaming SHA-256 computation (1 MiB)
_HASH_CHUNK = 1 << 20


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class FileRecord:
    """Metadata for one discovered input file."""

    path: Path
    size_bytes: int
    sha256: str
    error: str | None = None  # set when the file could not be read

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def is_readable(self) -> bool:
        return self.error is None


@dataclass
class DiscoveryResult:
    """Aggregated result of one discovery run over an input directory."""

    input_dir: Path
    discovered: list[FileRecord] = field(default_factory=list)
    skipped_outputs: list[Path] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)

    @property
    def readable_files(self) -> list[FileRecord]:
        return [f for f in self.discovered if f.is_readable]

    @property
    def unreadable_files(self) -> list[FileRecord]:
        return [f for f in self.discovered if not f.is_readable]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256_file(path: Path) -> str:
    """Return the hex SHA-256 digest of *path*, reading in chunks."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(_HASH_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def _is_output_file(path: Path) -> bool:
    """Return True if *path* lives inside any of the generated-output directories."""
    resolved = path.resolve()
    for marker in OUTPUT_DIR_MARKERS:
        try:
            resolved.relative_to(marker.resolve())
            return True
        except ValueError:
            pass
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def discover_files(
    input_dir: Path,
    *,
    extensions: frozenset[str] | None = None,
    recursive: bool = True,
) -> DiscoveryResult:
    """
    Walk *input_dir* and return a :class:`DiscoveryResult`.

    Parameters
    ----------
    input_dir : Path
        Directory to scan.  Must exist and be a directory.
    extensions : frozenset[str] | None
        File extensions to include (e.g. ``frozenset({".html", ".htm"})``.
        Defaults to ``SUPPORTED_EXTENSIONS`` from config.
    recursive : bool
        Whether to descend into subdirectories.  Default: True.
    """
    if extensions is None:
        extensions = SUPPORTED_EXTENSIONS

    result = DiscoveryResult(input_dir=input_dir)

    if not input_dir.exists():
        log.warning("Input directory does not exist: %s", input_dir)
        return result

    if not input_dir.is_dir():
        log.error("Input path is not a directory: %s", input_dir)
        return result

    glob_fn = input_dir.rglob if recursive else input_dir.glob
    candidates: Iterator[Path] = (
        p for ext in extensions for p in glob_fn(f"*{ext}")
        if p.is_file()
    )

    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)

        # Exclude generated output files
        if _is_output_file(path):
            log.debug("Skipping output file: %s", path)
            result.skipped_outputs.append(path)
            continue

        try:
            size = path.stat().st_size
            sha = _sha256_file(path)
            result.discovered.append(
                FileRecord(path=path, size_bytes=size, sha256=sha)
            )
            log.debug("Discovered: %s (%d bytes)", path.name, size)

        except PermissionError as exc:
            msg = f"Permission denied: {exc}"
            log.warning("Cannot read %s — %s", path, msg)
            result.discovered.append(
                FileRecord(path=path, size_bytes=0, sha256="", error=msg)
            )
            result.errors.append((path, msg))

        except OSError as exc:
            msg = f"OS error: {exc}"
            log.warning("Cannot read %s — %s", path, msg)
            result.discovered.append(
                FileRecord(path=path, size_bytes=0, sha256="", error=msg)
            )
            result.errors.append((path, msg))

    # Sort deterministically
    result.discovered.sort(key=lambda f: f.path.name)
    result.skipped_outputs.sort()

    log.info(
        "Discovery complete: %d discovered, %d output-skipped, %d errors in %s",
        len(result.discovered),
        len(result.skipped_outputs),
        len(result.errors),
        input_dir,
    )
    return result
