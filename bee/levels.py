"""Recognition levels (S1 Statement 000 cl. 8.2.1). Level 9 means non-compliant."""

NON_COMPLIANT = 9

# (minimum points, level, procurement recognition %)
LEVELS: tuple[tuple[float, int, int], ...] = (
    (100, 1, 135),
    (95, 2, 125),
    (90, 3, 110),
    (80, 4, 100),
    (75, 5, 80),
    (70, 6, 60),
    (55, 7, 50),
    (40, 8, 10),
)
RECOGNITION = {lvl: pct for _, lvl, pct in LEVELS} | {NON_COMPLIANT: 0}


def level_from_points(points: float) -> int:
    for minimum, level, _ in LEVELS:
        if points >= minimum - 1e-9:
            return level
    return NON_COMPLIANT


def recognition(level: int) -> int:
    return RECOGNITION[level]


def discount(level: int, steps: int = 1) -> int:
    """Move down ``steps`` levels; Level 8 discounted becomes non-compliant."""
    return min(level + steps, NON_COMPLIANT)


def uplift(level: int, steps: int) -> int:
    """Move up ``steps`` levels, capped at Level 1 (D3)."""
    return max(level - steps, 1)
