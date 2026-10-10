"""
FlightStory — Central configuration and path management.

All configurable paths and constants live here. Modules import from this
file rather than hard-coding paths, so the project root can be relocated
without touching ingestion logic.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root: the directory that contains src/, data/, config/, tests/
# ---------------------------------------------------------------------------
# When run from anywhere, resolve relative to this file's location.
_THIS_FILE = Path(__file__).resolve()
# src/flightstory/config.py  →  ../../  =  project root
PROJECT_ROOT: Path = _THIS_FILE.parent.parent.parent

# ---------------------------------------------------------------------------
# Data directories
# ---------------------------------------------------------------------------
DATA_DIR: Path = PROJECT_ROOT / "data"
INPUT_HTML_DIR: Path = DATA_DIR / "input_html"
RAW_ARCHIVE_DIR: Path = DATA_DIR / "raw_archive"
NODES_DIR: Path = DATA_DIR / "nodes"
MANIFESTS_DIR: Path = DATA_DIR / "manifests"
DATABASE_DIR: Path = DATA_DIR / "database"

DUCKDB_PATH: Path = DATABASE_DIR / "flightstory.duckdb"

# ---------------------------------------------------------------------------
# Configuration directory
# ---------------------------------------------------------------------------
CONFIG_DIR: Path = PROJECT_ROOT / "config"
DEFAULT_NODE_MAPPING_PATH: Path = CONFIG_DIR / "node_mapping.json"

# ---------------------------------------------------------------------------
# Supported input extensions
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".html", ".htm"})

# ---------------------------------------------------------------------------
# Output subdirectory markers used to avoid re-ingesting generated outputs.
# Any file whose resolved path is inside one of these directories is excluded
# from file discovery regardless of extension.
# ---------------------------------------------------------------------------
OUTPUT_DIR_MARKERS: tuple[Path, ...] = (
    RAW_ARCHIVE_DIR,
    NODES_DIR,
    DATABASE_DIR,
)

# ---------------------------------------------------------------------------
# Ingestion batch sizing
# ---------------------------------------------------------------------------
# Maximum number of DataFrame rows to accumulate before writing a Parquet batch.
BATCH_SIZE: int = int(os.environ.get("FLIGHTSTORY_BATCH_SIZE", "10000"))

# ---------------------------------------------------------------------------
# Timestamp parsing
# ---------------------------------------------------------------------------
# When True, naive timestamps (no tzinfo) are stored as-is without assuming UTC.
# Set False to coerce to UTC during normalisation (NOT recommended for aircraft data).
PRESERVE_NAIVE_TZ: bool = True

# ---------------------------------------------------------------------------
# Workspace identifier (optional, populated by a future UI layer)
# ---------------------------------------------------------------------------
WORKSPACE_ID: str | None = os.environ.get("FLIGHTSTORY_WORKSPACE_ID")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_data_dirs() -> None:
    """Create all required data directories if they do not exist."""
    for path in (
        INPUT_HTML_DIR,
        RAW_ARCHIVE_DIR,
        NODES_DIR,
        MANIFESTS_DIR,
        DATABASE_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def node_output_dir(node_id: str) -> Path:
    """Return (and create) the Parquet output directory for *node_id*."""
    p = NODES_DIR / node_id.lower()
    p.mkdir(parents=True, exist_ok=True)
    return p
