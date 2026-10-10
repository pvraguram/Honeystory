"""
Shared pytest fixtures for the FlightStory test suite.

Provides:
- tmp_input_dir / tmp_output_dir: isolated temporary directories
- Static fixture HTML paths
- Helper factories for synthetic HTML files
- A pre-configured node mapping JSON file
- A DuckDB connection pointed at an isolated test database
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make the src package importable without pip install -e
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ---------------------------------------------------------------------------
# Paths to static fixtures
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_table_html() -> Path:
    return FIXTURES_DIR / "simple_table.html"


@pytest.fixture
def multi_table_html() -> Path:
    return FIXTURES_DIR / "multi_table.html"


@pytest.fixture
def no_timestamp_html() -> Path:
    return FIXTURES_DIR / "no_timestamp.html"


@pytest.fixture
def malformed_html() -> Path:
    return FIXTURES_DIR / "malformed.html"


@pytest.fixture
def empty_table_html() -> Path:
    return FIXTURES_DIR / "empty_table.html"


@pytest.fixture
def all_fixture_paths() -> list[Path]:
    return [
        FIXTURES_DIR / "simple_table.html",
        FIXTURES_DIR / "multi_table.html",
        FIXTURES_DIR / "no_timestamp.html",
        FIXTURES_DIR / "malformed.html",
        FIXTURES_DIR / "empty_table.html",
    ]


# ---------------------------------------------------------------------------
# Temporary directories
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_input_dir(tmp_path: Path) -> Path:
    d = tmp_path / "input_html"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """A complete isolated data directory structure."""
    for sub in ("input_html", "raw_archive", "nodes", "manifests", "database"):
        (tmp_path / sub).mkdir(parents=True)
    return tmp_path


# ---------------------------------------------------------------------------
# Synthetic HTML helpers
# ---------------------------------------------------------------------------

def make_html_with_iso_timestamps(
    output_path: Path,
    *,
    n_rows: int = 10,
    table_id: str = "test_table",
    ms_precision: bool = True,
) -> Path:
    """Write a minimal HTML file with ISO timestamps to *output_path*."""
    rows = []
    for i in range(n_rows):
        ts = f"2024-01-15T08:{i:02d}:00.{(i * 100):03d}" if ms_precision else f"2024-01-15T08:{i:02d}:00"
        rows.append(f"<tr><td>{ts}</td><td>SYS_{i}</td><td>{i * 10}</td></tr>")

    html = f"""<!DOCTYPE html>
<html><body>
<table id="{table_id}">
<thead><tr><th>timestamp</th><th>system</th><th>value</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
</body></html>"""
    output_path.write_text(html, encoding="utf-8")
    return output_path


def make_html_no_timestamps(output_path: Path) -> Path:
    """Write an HTML file with no timestamp columns."""
    html = """<!DOCTYPE html>
<html><body>
<table id="config">
<thead><tr><th>param</th><th>value</th></tr></thead>
<tbody>
<tr><td>MAX_ALTITUDE</td><td>41000</td></tr>
<tr><td>MAX_SPEED</td><td>340</td></tr>
</tbody>
</table>
</body></html>"""
    output_path.write_text(html, encoding="utf-8")
    return output_path


def make_large_html(output_path: Path, n_rows: int = 15000) -> Path:
    """Write a large HTML file for memory-safety tests."""
    rows = [
        f"<tr><td>2024-01-15T{(i // 3600):02d}:{(i % 3600 // 60):02d}:{i % 60:02d}.{i % 1000:03d}</td>"
        f"<td>SYS</td><td>{i}</td></tr>"
        for i in range(n_rows)
    ]
    html = (
        "<!DOCTYPE html><html><body>"
        '<table id="large_table">'
        "<thead><tr><th>timestamp</th><th>system</th><th>value</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody>"
        "</table></body></html>"
    )
    output_path.write_text(html, encoding="utf-8")
    return output_path


# Expose helpers as fixtures too
@pytest.fixture
def synthetic_iso_html(tmp_input_dir: Path) -> Path:
    return make_html_with_iso_timestamps(
        tmp_input_dir / "synthetic_iso.html", n_rows=5
    )


@pytest.fixture
def synthetic_no_ts_html(tmp_input_dir: Path) -> Path:
    return make_html_no_timestamps(tmp_input_dir / "synthetic_no_ts.html")


@pytest.fixture
def large_html_file(tmp_input_dir: Path) -> Path:
    return make_large_html(tmp_input_dir / "large_file.html", n_rows=12000)


# ---------------------------------------------------------------------------
# Node mapping fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def node_mapping_file(tmp_path: Path) -> Path:
    """A valid node mapping JSON for simple_table.html → NODE_A."""
    mapping = {
        "simple_table.html": "NODE_A",
        "multi_table.html": "NODE_B",
        "no_timestamp.html": "NODE_C",
        "malformed.html": "NODE_A",
        "empty_table.html": "NODE_B",
    }
    p = tmp_path / "node_mapping.json"
    p.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    return p


@pytest.fixture
def partial_mapping_file(tmp_path: Path) -> Path:
    """A mapping that intentionally omits some files."""
    mapping = {
        "simple_table.html": "NODE_A",
        # multi_table.html intentionally unmapped
    }
    p = tmp_path / "partial_mapping.json"
    p.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# DuckDB test fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def test_duckdb(tmp_path: Path):
    """Open an isolated DuckDB connection for testing."""
    import duckdb
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))
    yield conn
    conn.close()
