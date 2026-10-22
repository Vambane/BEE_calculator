"""Sector registry. Sectors are data configs (bee/sectors/configs.py); 'generic' is the
default. Add a sector with ``register_sector(SectorConfig(...))``."""

from __future__ import annotations

from bee.models import EnterpriseSize
from bee.rules import Scorecard
from bee.sectors.base import SectorConfig
from bee.sectors.configs import SECTORS

DEFAULT_SECTOR = "generic"
ALIASES = {
    "fsc": "financial",
    "financial_services": "financial",
    "agribee": "agri",
    "agriculture": "agri",
    "ca": "chartered_accountancy",
    "bep": "construction",
}


def _key(sector: str) -> str:
    k = sector.lower().strip().replace(" ", "_").replace("-", "_")
    return ALIASES.get(k, k)


def register_sector(cfg: SectorConfig) -> None:
    SECTORS[_key(cfg.key)] = cfg


def get_sector(sector: str = DEFAULT_SECTOR) -> SectorConfig:
    k = _key(sector)
    if k not in SECTORS:
        raise KeyError(f"Unknown sector {sector!r}; known: {sectors()}")
    return SECTORS[k]


def sectors() -> list[str]:
    return sorted(SECTORS)


def register(sector: str, size: EnterpriseSize, card: Scorecard) -> None:
    """Register a single scorecard (creates a minimal sector config if needed)."""
    k = _key(sector)
    if k not in SECTORS:
        base = SECTORS[DEFAULT_SECTOR]
        SECTORS[k] = SectorConfig(k, sector, "custom", "unverified", dict(base.cards))
    SECTORS[k].cards[(size, None)] = card


def get_scorecard(
    size: EnterpriseSize, sector: str = DEFAULT_SECTOR, variant: str | None = None
) -> Scorecard:
    cfg = get_sector(sector)
    return cfg.card(size, cfg.resolve_variant(variant))
