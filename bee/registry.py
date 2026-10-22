"""Scorecard registry keyed by (sector, size). 'generic' is the default sector.

Sector codes are not implemented. To add one later, build a ``Scorecard`` (in Python or
loaded from a data file) and call ``register("ict", EnterpriseSize.GENERIC, card)``.
"""

from __future__ import annotations

from bee.models import EnterpriseSize
from bee.rules import Scorecard
from bee.scorecards import generic, qse

DEFAULT_SECTOR = "generic"

_REGISTRY: dict[tuple[str, EnterpriseSize], Scorecard] = {
    (DEFAULT_SECTOR, EnterpriseSize.GENERIC): generic.SCORECARD,
    (DEFAULT_SECTOR, EnterpriseSize.QSE): qse.SCORECARD,
    # EMEs opting to be scored use the QSE scorecard (S5 cl. 4.5).
    (DEFAULT_SECTOR, EnterpriseSize.EME): qse.SCORECARD,
}


def register(sector: str, size: EnterpriseSize, card: Scorecard) -> None:
    _REGISTRY[(sector.lower(), size)] = card


def sectors() -> list[str]:
    return sorted({s for s, _ in _REGISTRY})


def get_scorecard(size: EnterpriseSize, sector: str = DEFAULT_SECTOR) -> Scorecard:
    key = (sector.lower(), size)
    if key not in _REGISTRY:
        raise KeyError(f"No scorecard registered for sector={sector!r}, size={size}")
    return _REGISTRY[key]
