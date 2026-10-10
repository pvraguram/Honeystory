"""
FlightStory AI — Standalone Aircraft Data Ingestion Engine.

Public surface for programmatic use by a future UI layer.
"""

from .models import IngestionRecord, TimestampParseStatus
from .orchestrator import IngestionOrchestrator
from .recon import HtmlRecon

__version__ = "0.1.0"
__all__ = [
    "IngestionOrchestrator",
    "HtmlRecon",
    "IngestionRecord",
    "TimestampParseStatus",
]
