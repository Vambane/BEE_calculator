"""Sector-code configs. Each sector is data: thresholds, deemed levels, scorecards per
(size, variant), sub-minimums, level rescaling and warnings.

Sources and status: bee-team/compliance/sector-codes.md (23 Oct 2026). Sector codes are
aligned to the 2013 Amended Codes; the 2019 generic amendments (GG 42496) are NOT applied.
"""

from bee.sectors.base import (
    SectorConfig,
    SectorExcludedError,
    Thresholds,
)

__all__ = ["SectorConfig", "SectorExcludedError", "Thresholds"]
