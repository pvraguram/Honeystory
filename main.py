"""
FlightStory AI — CLI entry point.

This thin wrapper lets the engine be invoked as:
    python main.py <command> [options]

It delegates entirely to flightstory.cli.main().
"""

import sys
from pathlib import Path

# Ensure src/ is on the path when running directly (without pip install -e)
sys.path.insert(0, str(Path(__file__).parent / "src"))

from flightstory.cli import main

if __name__ == "__main__":
    main()
