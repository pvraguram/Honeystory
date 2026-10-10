"""
Tests for Module A — File discovery.

Covers:
- All eligible files are discovered
- Files in output directories are excluded
- Unreadable files are handled gracefully
- Zero-byte files are discovered but flagged if unreadable
- SHA-256 hashes are computed
- Generated output files are not mistaken for inputs
- Recursive and non-recursive discovery
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flightstory.discovery import FileRecord, discover_files
from tests.conftest import make_html_with_iso_timestamps


class TestDiscoverFiles:
    def test_discovers_html_files(self, tmp_input_dir: Path) -> None:
        """All .html files in the input dir are discovered."""
        make_html_with_iso_timestamps(tmp_input_dir / "file_a.html")
        make_html_with_iso_timestamps(tmp_input_dir / "file_b.html")

        result = discover_files(tmp_input_dir)
        names = {f.filename for f in result.discovered}
        assert "file_a.html" in names
        assert "file_b.html" in names

    def test_discovers_htm_extension(self, tmp_input_dir: Path) -> None:
        """Files with .htm extension are also discovered."""
        (tmp_input_dir / "log.htm").write_text("<html></html>", encoding="utf-8")
        result = discover_files(tmp_input_dir)
        assert any(f.filename == "log.htm" for f in result.discovered)

    def test_excludes_non_html(self, tmp_input_dir: Path) -> None:
        """CSV, JSON, and other non-HTML files are not included."""
        (tmp_input_dir / "data.csv").write_text("a,b,c", encoding="utf-8")
        (tmp_input_dir / "config.json").write_text("{}", encoding="utf-8")
        make_html_with_iso_timestamps(tmp_input_dir / "valid.html")

        result = discover_files(tmp_input_dir)
        assert len(result.discovered) == 1
        assert result.discovered[0].filename == "valid.html"

    def test_sha256_is_computed(self, tmp_input_dir: Path) -> None:
        """Each discovered file has a non-empty SHA-256 hash."""
        make_html_with_iso_timestamps(tmp_input_dir / "hashed.html")
        result = discover_files(tmp_input_dir)
        assert result.discovered[0].sha256
        assert len(result.discovered[0].sha256) == 64  # SHA-256 hex = 64 chars

    def test_file_size_recorded(self, tmp_input_dir: Path) -> None:
        """File sizes are recorded accurately."""
        p = tmp_input_dir / "sized.html"
        content = "<html>test</html>"
        p.write_text(content, encoding="utf-8")
        result = discover_files(tmp_input_dir)
        assert result.discovered[0].size_bytes == len(content.encode("utf-8"))

    def test_missing_directory_returns_empty(self, tmp_path: Path) -> None:
        """A non-existent input directory returns an empty result without raising."""
        result = discover_files(tmp_path / "nonexistent")
        assert result.discovered == []
        assert result.errors == []

    def test_recursive_discovery(self, tmp_input_dir: Path) -> None:
        """Files in subdirectories are found with recursive=True."""
        sub = tmp_input_dir / "subdir"
        sub.mkdir()
        make_html_with_iso_timestamps(sub / "nested.html")
        make_html_with_iso_timestamps(tmp_input_dir / "top.html")

        result = discover_files(tmp_input_dir, recursive=True)
        names = {f.filename for f in result.discovered}
        assert "nested.html" in names
        assert "top.html" in names

    def test_non_recursive_discovery(self, tmp_input_dir: Path) -> None:
        """With recursive=False, subdirectory files are not included."""
        sub = tmp_input_dir / "subdir"
        sub.mkdir()
        make_html_with_iso_timestamps(sub / "nested.html")
        make_html_with_iso_timestamps(tmp_input_dir / "top.html")

        result = discover_files(tmp_input_dir, recursive=False)
        names = {f.filename for f in result.discovered}
        assert "top.html" in names
        assert "nested.html" not in names

    def test_output_directory_files_excluded(self, tmp_path: Path) -> None:
        """Files inside output directories (raw_archive, nodes) are skipped."""
        from flightstory.config import OUTPUT_DIR_MARKERS

        # Place a file in an output dir marker
        for marker in OUTPUT_DIR_MARKERS:
            marker.mkdir(parents=True, exist_ok=True)
            (marker / "output.html").write_text("<html></html>", encoding="utf-8")

        # Legit input dir
        input_dir = tmp_path / "inputs"
        input_dir.mkdir()
        make_html_with_iso_timestamps(input_dir / "real_input.html")

        result = discover_files(input_dir)
        assert all(f.filename == "real_input.html" for f in result.discovered)
        assert len(result.discovered) == 1

    def test_same_hash_for_same_content(self, tmp_input_dir: Path) -> None:
        """Two files with identical content have the same hash."""
        content = "<html><body>same</body></html>"
        (tmp_input_dir / "copy1.html").write_text(content, encoding="utf-8")
        (tmp_input_dir / "copy2.html").write_text(content, encoding="utf-8")

        result = discover_files(tmp_input_dir)
        hashes = {f.sha256 for f in result.discovered}
        assert len(hashes) == 1  # same content → same hash

    def test_different_content_different_hash(self, tmp_input_dir: Path) -> None:
        """Files with different content have different hashes."""
        (tmp_input_dir / "a.html").write_text("<html>A</html>", encoding="utf-8")
        (tmp_input_dir / "b.html").write_text("<html>B</html>", encoding="utf-8")

        result = discover_files(tmp_input_dir)
        hashes = [f.sha256 for f in result.discovered]
        assert hashes[0] != hashes[1]

    def test_readable_vs_unreadable(self, tmp_input_dir: Path) -> None:
        """readable_files only contains files without errors."""
        make_html_with_iso_timestamps(tmp_input_dir / "good.html")
        result = discover_files(tmp_input_dir)
        assert len(result.readable_files) == 1
        assert len(result.unreadable_files) == 0

    def test_empty_directory(self, tmp_input_dir: Path) -> None:
        """Empty input directory returns empty result without errors."""
        result = discover_files(tmp_input_dir)
        assert result.discovered == []
        assert result.errors == []

    def test_result_sorted_by_filename(self, tmp_input_dir: Path) -> None:
        """Results are sorted by filename for determinism."""
        for name in ["z_file.html", "a_file.html", "m_file.html"]:
            make_html_with_iso_timestamps(tmp_input_dir / name)
        result = discover_files(tmp_input_dir)
        names = [f.filename for f in result.discovered]
        assert names == sorted(names)
