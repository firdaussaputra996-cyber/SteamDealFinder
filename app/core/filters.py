"""
filters.py

Logika filtering daftar Game berdasarkan kriteria:
- harga minimum (Rupiah)
- harga maksimum (Rupiah)
- persentase diskon minimum
"""

from __future__ import annotations

from typing import List, Optional

from app.core.models import Game


def filter_games(
    games: List[Game],
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_discount: Optional[int] = None,
) -> List[Game]:
    """Kembalikan subset game yang sesuai kriteria.

    Game gratis (is_free=True) hanya diikutkan jika min_price bernilai 0
    atau None, karena harga Rp 0 tidak selalu relevan dengan pencarian deal.
    """
    result: List[Game] = []

    for game in games:
        if game.is_free:
            # Game gratis dianggap tidak relevan untuk pencarian "deal diskon",
            # kecuali user secara eksplisit tidak memberi batas harga minimum.
            if min_price not in (None, 0):
                continue
            if min_discount:
                continue  # game gratis tidak punya diskon persentase yang berarti
            result.append(game)
            continue

        if game.final_price is None:
            continue

        if min_price is not None and game.final_price < min_price:
            continue
        if max_price is not None and game.final_price > max_price:
            continue
        if min_discount is not None and game.discount_percent < min_discount:
            continue

        result.append(game)

    return result
