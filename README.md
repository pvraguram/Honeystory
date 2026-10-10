# FlightStory AI — Ingestion Engine

A standalone, modular Python ingestion engine that transforms raw aircraft-system HTML logs into structured, queryable Parquet/DuckDB storage. This is the data-foundation layer; story generation and UI belong to future phases.

## Project Layout

```
FlightStory/
├── pyproject.toml              # Project metadata and dependencies
├── requirements.txt            # Pinned runtime deps (for pip install)
├── README.md
├── main.py                     # CLI entry point
│
├── src/
│   └── flightstory/
│       ├── __init__.py
│       ├── cli.py              # Command-line interface (Module G surface)
│       ├── config.py           # Settings, paths, constants
│       ├── models.py           # Common record representation (Module E)
│       │
│       ├── discovery.py        # Module A: File discovery
│       ├── node_mapping.py     # Module B: Node mapping
│       ├── extractor.py        # Module C: HTML extraction
│       ├── timestamps.py       # Module D: Timestamp preservation/normalisation
│       ├── storage.py          # Module F: Parquet + DuckDB storage
│       ├── orchestrator.py     # Module G: Ingestion orchestration
│       └── recon.py            # Phase 2: HTML reconnaissance module
│
├── data/
│   ├── input_html/             # Drop HTML source files here
│   ├── raw_archive/            # Preserved originals (read-only copies)
│   ├── nodes/
│   │   ├── node_a/             # Per-node Parquet output
│   │   ├── node_b/
│   │   └── node_c/
│   ├── manifests/              # Per-run JSON manifests
│   └── database/
│       └── flightstory.duckdb  # Unified DuckDB analytical layer
│
├── config/
│   └── node_mapping.json       # Explicit filename → node_id mapping
│
└── tests/
    ├── conftest.py             # Shared fixtures (synthetic HTML, temp dirs)
    ├── fixtures/               # Static test HTML files
    │   ├── simple_table.html
    │   ├── multi_table.html
    │   ├── no_timestamp.html
    │   ├── malformed.html
    │   └── empty_table.html
    ├── test_discovery.py       # Module A tests
    ├── test_node_mapping.py    # Module B tests
    ├── test_extractor.py       # Module C tests
    ├── test_timestamps.py      # Module D tests
    ├── test_storage.py         # Module F tests
    ├── test_orchestrator.py    # Module G integration tests
    └── test_recon.py           # Reconnaissance module tests
```

## Quick Start

### 1. Install dependencies

```bash
pip install -e ".[dev]"
# or
pip install -r requirements.txt
pip install pytest pytest-cov
```

### 2. Place HTML input files

Copy your 15 aircraft HTML logs into:
```
data/input_html/
```

### 3. Configure node mapping

Edit `config/node_mapping.json`:
```json
{
  "acars_log_01.html": "NODE_A",
  "acars_log_02.html": "NODE_A",
  "fdr_data_01.html":  "NODE_B"
}
```

### 4. Inspect the dataset (reconnaissance)

```bash
python main.py inspect --input data/input_html/
python main.py inspect --input data/input_html/ --output recon_report.json
```

### 5. Run ingestion

```bash
python main.py ingest --config config/node_mapping.json
python main.py ingest --config config/node_mapping.json --force   # reprocess changed files
```

### 6. Check status

```bash
python main.py status
```

### 7. Validate stored data

```bash
python main.py validate
```

### 8. Run the test suite

```bash
pytest tests/ -v
pytest tests/ -v --cov=src/flightstory --cov-report=term-missing
```

## Design Principles

- **Schema-agnostic extraction**: each HTML table is parsed independently; heterogeneous columns are preserved in `original_record` (JSON).
- **Timestamp safety**: original strings are always preserved; normalisation is additive and never lossy.
- **Idempotent ingestion**: source-file SHA-256 hashes prevent duplicate batch writes on rerun.
- **Traceable records**: every row carries `source_file`, `source_table_id`, `source_row_number` provenance.
- **Explicit node assignment**: node identity comes only from `config/node_mapping.json`, never from filename heuristics.
- **Single DuckDB**: one database with views across all node Parquet folders.

## Scope

This engine covers **ingestion only**:
- HTML discovery, parsing, and extraction
- Timestamp normalisation and preservation
- Parquet storage (per node)
- DuckDB unified query layer
- Manifests and integrity validation
- CLI and automated tests

**Not in scope** (future phases): timestamp correlation, cross-node event grouping, fault diagnosis, LLM reasoning, narrative generation, frontend/UI.
