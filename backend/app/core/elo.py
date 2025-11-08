from __future__ import annotations


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def k_factor(comparisons: int) -> float:
    if comparisons < 20:
        return 40.0
    if comparisons < 50:
        return 20.0
    return 10.0


def update_elo(rating_a: float, rating_b: float, score_a: float, count_a: int, count_b: int) -> tuple[float, float]:
    ea = expected_score(rating_a, rating_b)
    eb = 1.0 - ea

    ka = k_factor(count_a)
    kb = k_factor(count_b)

    new_a = rating_a + ka * (score_a - ea)
    new_b = rating_b + kb * ((1.0 - score_a) - eb)
    return new_a, new_b


def elo_to_100(elo: float) -> float:
    # Map Elo to 0-100 using a squashed curve so typical collections have a spread and clear top tier.
    x = (elo - 1500.0) / 120.0
    score = 50.0 + 45.0 * (x / (1.0 + abs(x)))
    return round(max(0.0, min(100.0, score)), 1)
