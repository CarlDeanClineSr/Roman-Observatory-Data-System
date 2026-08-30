"""Roman Observatory Data System.

The package is intentionally metadata-first.  Version 0.1 contains no bulk
product downloader and no bridge into Sun-Earth L1 space-weather calculations.
"""

from __future__ import annotations

__all__ = ["__version__", "MISSION", "DOMAIN"]

__version__ = "0.1.0"
MISSION = "ROMAN"
DOMAIN = "ASTRONOMICAL_OBSERVATORY"
