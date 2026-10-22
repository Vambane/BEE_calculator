"""EME deemed recognition (S5 cl. 4.3-4.4). EMEs are not scored unless they opt in to the
QSE scorecard (S5 cl. 4.5)."""


def deemed_level(black_ownership_pct: float) -> int:
    if black_ownership_pct >= 100:
        return 1  # cl. 4.4.1
    if black_ownership_pct >= 51:
        return 2  # cl. 4.4.2
    return 4  # cl. 4.3
