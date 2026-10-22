"""Enterprise classification by Total Revenue (S5 cl. 4.1, 5.1, 6.1; rules-baseline §1)."""

from bee.models import EnterpriseSize

EME_MAX = 10_000_000  # "R10 million or less" -> EME
GENERIC_MIN = 50_000_000  # "R50 million and more" -> Generic


def classify(total_revenue: float) -> EnterpriseSize:
    if total_revenue < 0:
        raise ValueError("total_revenue must be >= 0")
    if total_revenue <= EME_MAX:
        return EnterpriseSize.EME
    if total_revenue < GENERIC_MIN:
        return EnterpriseSize.QSE
    return EnterpriseSize.GENERIC


def classify_for_sector(total_revenue: float, sector: str = "generic",
                        variant: str | None = None) -> EnterpriseSize:
    from bee.registry import get_sector

    cfg = get_sector(sector)
    return cfg.threshold(cfg.resolve_variant(variant)).classify(total_revenue)
