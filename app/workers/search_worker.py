"""
search_worker.py

QThread yang menjalankan pencarian game diskon Steam secara bertahap
(per halaman/batch) di background, supaya GUI utama tidak freeze.

Alur:
    1. Ambil halaman specials (up to `page_size` game per request)
    2. Parse HTML -> data mentah -> Game object
    3. Terapkan filter harga & diskon
    4. Ulangi sampai:
        - total_count Steam habis, atau
        - sudah mencapai `max_pages` (batas keamanan jumlah request), atau
        - sudah mendapat >= `max_results` game yang cocok
    5. Emit hasil akhir (sudah difilter & dibatasi max_results)
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QThread, Signal

from app.api.parser import parse_price_to_int, parse_search_results_html
from app.api.steam_api import SteamAPIError, SteamStoreClient
from app.core.filters import filter_games
from app.core.models import Game


class SearchWorker(QThread):
    progress = Signal(str)               # pesan status untuk ditampilkan ke user
    finished_search = Signal(list)        # List[Game] hasil akhir
    error_occurred = Signal(str)          # pesan error

    def __init__(
        self,
        client: SteamStoreClient,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_discount: Optional[int] = None,
        max_results: int = 60,
        page_size: int = 100,
        max_pages: int = 20,
        cc: str = "id",
        language: str = "indonesian",
        parent=None,
    ):
        super().__init__(parent)
        self.client = client
        self.min_price = min_price
        self.max_price = max_price
        self.min_discount = min_discount
        self.max_results = max_results
        self.page_size = page_size
        self.max_pages = max_pages
        self.cc = cc
        self.language = language

        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def _build_game(self, raw: dict) -> Optional[Game]:
        initial_price = parse_price_to_int(raw.get("initial_price_text", ""))
        final_price = parse_price_to_int(raw.get("final_price_text", ""))

        if not raw.get("is_free") and final_price is None:
            # Tidak bisa menentukan harga, lewati agar filter tetap akurat.
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

    def run(self):
        matched: List[Game] = []
        start = 0
        page_number = 0

        try:
            while True:
                if self._is_cancelled:
                    return

                page_number += 1
                self.progress.emit(
                    f"Mengambil halaman {page_number} (mulai dari item {start})..."
                )

                data = self.client.fetch_specials_page(
                    start=start,
                    count=self.page_size,
                    cc=self.cc,
                    language=self.language,
                )

                total_count = data.get("total_count", 0)
                html = data.get("results_html", "")

                raw_items = parse_search_results_html(html)

                if not raw_items:
                    # Tidak ada lagi data untuk diparse, hentikan.
                    break

                games_this_page: List[Game] = []
                for raw in raw_items:
                    game = self._build_game(raw)
                    if game is not None:
                        games_this_page.append(game)

                filtered_this_page = filter_games(
                    games_this_page,
                    min_price=self.min_price,
                    max_price=self.max_price,
                    min_discount=self.min_discount,
                )
                matched.extend(filtered_this_page)

                self.progress.emit(
                    f"Halaman {page_number}: ditemukan {len(filtered_this_page)} deal cocok "
                    f"(total cocok sejauh ini: {len(matched)})"
                )

                start += self.page_size

                if len(matched) >= self.max_results:
                    matched = matched[: self.max_results]
                    break
                if start >= total_count:
                    break
                if page_number >= self.max_pages:
                    self.progress.emit(
                        "Mencapai batas maksimum halaman pencarian, menghentikan pencarian."
                    )
                    break

            self.progress.emit(f"Selesai. Total deal ditemukan: {len(matched)}")
            self.finished_search.emit(matched)

        except SteamAPIError as exc:
            self.error_occurred.emit(str(exc))
        except Exception as exc:  # pengaman terakhir agar thread tidak crash diam-diam
            self.error_occurred.emit(f"Terjadi kesalahan tak terduga: {exc}")
