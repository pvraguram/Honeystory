"""
Tests for Module B — Node mapping.

Covers:
- Valid mapping files load correctly
- Multiple files can map to the same node
- Unmapped files are flagged (not silently dropped)
- Missing mapping file raises FileNotFoundError
- Malformed JSON raises ValueError
- Empty filename / node_id keys raise ValueError
- Template generation
- resolve_node_mapping cross-reference logic
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flightstory.node_mapping import (
    load_node_mapping,
    resolve_node_mapping,
    write_template_mapping,
)


class TestLoadNodeMapping:
    def test_valid_mapping_loads(self, tmp_path: Path) -> None:
        config = tmp_path / "mapping.json"
        config.write_text(
            json.dumps({"file_a.html": "NODE_A", "file_b.html": "NODE_B"}),
            encoding="utf-8",
        )
        mapping = load_node_mapping(config)
        assert mapping["file_a.html"] == "NODE_A"
        assert mapping["file_b.html"] == "NODE_B"

    def test_multiple_files_same_node(self, tmp_path: Path) -> None:
        config = tmp_path / "mapping.json"
        config.write_text(
            json.dumps({"f1.html": "NODE_A", "f2.html": "NODE_A", "f3.html": "NODE_B"}),
            encoding="utf-8",
        )
        mapping = load_node_mapping(config)
        assert mapping["f1.html"] == "NODE_A"
        assert mapping["f2.html"] == "NODE_A"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_node_mapping(tmp_path / "does_not_exist.json")

    def test_non_object_json_raises(self, tmp_path: Path) -> None:
        config = tmp_path / "bad.json"
        config.write_text('["list", "not", "object"]', encoding="utf-8")
        with pytest.raises(ValueError, match="JSON object"):
            load_node_mapping(config)

    def test_non_string_value_raises(self, tmp_path: Path) -> None:
        config = tmp_path / "bad_value.json"
        config.write_text('{"file.html": 123}', encoding="utf-8")
        with pytest.raises(ValueError, match="strings"):
            load_node_mapping(config)

    def test_empty_node_id_raises(self, tmp_path: Path) -> None:
        config = tmp_path / "empty_node.json"
        config.write_text('{"file.html": ""}', encoding="utf-8")
        with pytest.raises(ValueError, match="empty"):
            load_node_mapping(config)

    def test_empty_filename_raises(self, tmp_path: Path) -> None:
        config = tmp_path / "empty_filename.json"
        config.write_text('{"": "NODE_A"}', encoding="utf-8")
        with pytest.raises(ValueError, match="empty"):
            load_node_mapping(config)

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        config = tmp_path / "malformed.json"
        config.write_text("{not: valid json}", encoding="utf-8")
        with pytest.raises(Exception):  # json.JSONDecodeError
            load_node_mapping(config)


class TestResolveNodeMapping:
    def test_all_mapped(self, tmp_path: Path) -> None:
        config = tmp_path / "m.json"
        config.write_text(
            json.dumps({"a.html": "NODE_A", "b.html": "NODE_B"}), encoding="utf-8"
        )
        result = resolve_node_mapping(["a.html", "b.html"], config)
        assert result.mapped == {"a.html": "NODE_A", "b.html": "NODE_B"}
        assert result.unmapped == []

    def test_unmapped_files_reported(self, tmp_path: Path) -> None:
        config = tmp_path / "m.json"
        config.write_text(json.dumps({"a.html": "NODE_A"}), encoding="utf-8")
        result = resolve_node_mapping(["a.html", "b.html"], config)
        assert "b.html" in result.unmapped
        assert "a.html" not in result.unmapped

    def test_mapping_file_not_found(self, tmp_path: Path) -> None:
        result = resolve_node_mapping(
            ["a.html"], tmp_path / "missing.json"
        )
        assert result.load_error is not None
        assert result.mapped == {}
        assert "a.html" in result.unmapped

    def test_node_id_for_helper(self, tmp_path: Path) -> None:
        config = tmp_path / "m.json"
        config.write_text(json.dumps({"f.html": "NODE_X"}), encoding="utf-8")
        result = resolve_node_mapping(["f.html"], config)
        assert result.node_id_for("f.html") == "NODE_X"
        assert result.node_id_for("other.html") is None

    def test_extra_mapping_entries_ignored(self, tmp_path: Path) -> None:
        """Files in the mapping but not discovered are silently ignored."""
        config = tmp_path / "m.json"
        config.write_text(
            json.dumps({"a.html": "NODE_A", "z_not_here.html": "NODE_Z"}),
            encoding="utf-8",
        )
        result = resolve_node_mapping(["a.html"], config)
        assert result.mapped == {"a.html": "NODE_A"}


class TestWriteTemplateMappig:
    def test_template_written(self, tmp_path: Path) -> None:
        out = tmp_path / "template.json"
        write_template_mapping(["b.html", "a.html"], out)
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "a.html" in data
        assert "b.html" in data
        # Values should contain the placeholder marker
        assert "???" in data["a.html"]

    def test_template_sorted(self, tmp_path: Path) -> None:
        out = tmp_path / "template.json"
        write_template_mapping(["z.html", "a.html", "m.html"], out)
        data = json.loads(out.read_text(encoding="utf-8"))
        keys = list(data.keys())
        assert keys == sorted(keys)
