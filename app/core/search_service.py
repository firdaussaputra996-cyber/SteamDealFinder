"""
search_service.py

Logika pencarian Steam yang dapat dipakai oleh web backend maupun antarmuka
lain. Ini memindahkan alur dari worker Qt tanpa bergantung pada PySide6.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Optional

from app.api.parser import parse_price_to_int, parse_search_results_html
from app.api.steam_api import SteamStoreClient
from app.core.filters import filter_games
from app.core.models import Game


def build_game(raw: dict) -> Optional[Game]:
    initial_price = parse_price_to_int(raw.get("initial_price_text", ""))
    final_price = parse_price_to_int(raw.get("final_price_text", ""))

    if not raw.get("is_free") and final_price is None:
        return None

    return Game(
        appid=raw["appid"],
        name=raw["name"],
        store_url=raw["store_url"],
        header_image=raw.get("header_image", ""),
        is_free=raw.get("is_free", False),
        discount_percent=raw.get("discount_percent", 0),
        initial_price=initial_price,
        final_price=final_price,
    )


def game_to_dict(game: Game) -> Dict[str, object]:
    payload = asdict(game)
    payload["display_price"] = game.display_price
    payload["display_initial_price"] = game.display_initial_price
    return payload


def search_deals(
    client: SteamStoreClient,
    query: str = "",
    tag_id: Optional[int] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_discount: Optional[int] = None,
    max_results: int = 60,
    page_size: int = 100,
    max_pages: int = 20,
    cc: str = "id",
    language: str = "indonesian",
) -> List[Game]:
    matched: List[Game] = []
    start = 0
    page_number = 0
    normalized_query = query.strip().casefold()
    specials_only = min_discount is not None and min_discount > 0
    is_price_only_search = (
        not normalized_query and not specials_only and max_price is not None
    )
    sort_by = "_ASC"

    while True:
        page_number += 1
        data = client.fetch_specials_page(
            query=query,
            start=start,
            count=page_size,
            specials_only=specials_only,
            tag_id=tag_id,
            max_price_filter=max_price if is_price_only_search else None,
            hide_free_to_play=is_price_only_search,
            cc=cc,
            language=language,
            sort_by=sort_by,
        )

        total_count = data.get("total_count", 0)
        html = data.get("results_html", "")
        raw_items = parse_search_results_html(html)

        if not raw_items:
            break

        games_this_page = [
            game for raw in raw_items if (game := build_game(raw)) is not None
        ]
        if normalized_query:
            games_this_page = [
                game for game in games_this_page if normalized_query in game.name.casefold()
            ]

        matched.extend(
            filter_games(
                games_this_page,
                min_price=min_price,
                max_price=max_price,
                min_discount=min_discount,
            )
        )

        start += page_size

        if len(matched) >= max_results:
            break
        if start >= total_count:
            break
        if page_number >= max_pages:
            break

    if is_price_only_search:
        matched.sort(
            key=lambda game: (
                game.discount_percent > 0,
                game.final_price if game.final_price is not None else 0,
                game.name.casefold(),
            )
        )

    return matched[:max_results]
