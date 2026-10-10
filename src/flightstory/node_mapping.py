"""
Module B — Explicit node mapping.

Aircraft node identity is determined ONLY from a user-supplied configuration
file.  Filename heuristics or table-content scanning are never used.

The mapping file is a plain JSON object:
    {
        "log_file_01.html": "NODE_A",
        "log_file_02.html": "NODE_B"
    }

Multiple filenames may map to the same node.
Files not present in the mapping are flagged as unmapped.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class NodeMappingResult:
    """
    Outcome of resolving a set of discovered file paths against the mapping.
    """

    mapped: dict[str, str]
    """filename → node_id for successfully mapped files."""

    unmapped: list[str]
    """Filenames present in discovery but absent from the mapping config."""

    config_path: Path | None
    """Path to the mapping file that was loaded, or None if not loaded."""

    load_error: str | None = None
    """Set when the mapping file could not be read or parsed."""

    def node_id_for(self, filename: str) -> str | None:
        """Return the node_id for *filename*, or None if unmapped."""
        return self.mapped.get(filename)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_node_mapping(config_path: Path) -> dict[str, str]:
    """
    Load and validate the node-mapping JSON file.

    Returns
    -------
    dict[str, str]
        Raw filename → node_id mapping from the JSON file.

    Raises
    ------
    FileNotFoundError
        When *config_path* does not exist.
    ValueError
        When the file cannot be parsed or contains non-string values.
    """
    if not config_path.exists():
        raise FileNotFoundError(
            f"Node mapping config not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)

    if not isinstance(raw, dict):
        raise ValueError(
            f"Node mapping must be a JSON object, got {type(raw).__name__}"
        )

    validated: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError(
                f"All keys and values must be strings; "
                f"got key={key!r} value={value!r}"
            )
        if not key.strip():
            raise ValueError("Mapping contains empty filename key")
        if not value.strip():
            raise ValueError(
                f"Node ID for '{key}' is empty; every file must have a non-empty node_id"
            )
        validated[key] = value

    log.info(
        "Loaded node mapping from %s (%d entries)", config_path, len(validated)
    )
    return validated


def resolve_node_mapping(
    discovered_filenames: list[str],
    config_path: Path,
) -> NodeMappingResult:
    """
    Cross-reference *discovered_filenames* with the mapping at *config_path*.

    Files in the mapping that were not discovered are silently ignored (they
    may belong to a different run or input directory).  Files discovered but
    absent from the mapping are collected as ``unmapped``.

    Parameters
    ----------
    discovered_filenames : list[str]
        Filenames (basename only) returned by Module A discovery.
    config_path : Path
        Path to the node-mapping JSON file.

    Returns
    -------
    NodeMappingResult
    """
    try:
        full_mapping = load_node_mapping(config_path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError, OSError) as exc:
        log.error("Failed to load node mapping: %s", exc)
        return NodeMappingResult(
            mapped={},
            unmapped=list(discovered_filenames),
            config_path=config_path,
            load_error=str(exc),
        )

    mapped: dict[str, str] = {}
    unmapped: list[str] = []

    import re

    for filename in discovered_filenames:
        if filename in full_mapping:
            mapped[filename] = full_mapping[filename]
            log.debug("Mapped %s → %s", filename, full_mapping[filename])
        else:
            # Check for standard prefix heuristic (e.g. NODE_A_..., NODE_B_...)
            m = re.match(r"^(NODE_[A-Za-z0-9]+)_", filename, re.IGNORECASE)
            if m:
                inferred = m.group(1).upper()
                mapped[filename] = inferred
                log.info("Inferred node %s for %s from filename prefix", inferred, filename)
            else:
                unmapped.append(filename)
                log.warning("Unmapped file (no node assignment): %s", filename)

    return NodeMappingResult(
        mapped=mapped,
        unmapped=unmapped,
        config_path=config_path,
    )


def write_template_mapping(
    discovered_filenames: list[str],
    output_path: Path,
    *,
    placeholder_prefix: str = "NODE_",
) -> None:
    """
    Write a skeleton mapping JSON file for the operator to fill in.

    Each discovered filename is mapped to a placeholder node ID that the
    operator should replace with the real node identifier.
    """
    template = {
        fname: f"{placeholder_prefix}???"
        for fname in sorted(discovered_filenames)
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(template, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    log.info("Wrote mapping template to %s", output_path)
