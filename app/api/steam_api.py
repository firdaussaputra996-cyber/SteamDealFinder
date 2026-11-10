"""
steam_api.py

Client untuk mengambil data "specials" (game diskon) dari Steam Store
menggunakan endpoint pencarian internal Steam:

    https://store.steampowered.com/search/results/

Endpoint ini mengembalikan banyak game sekaligus (per halaman/batch) lengkap
dengan harga regional, diskon, dan gambar cover -- sehingga kita TIDAK perlu
mengambil seluruh daftar AppID lalu memanggil appdetails satu per satu.

Fitur:
- Timeout per request
- Retry sederhana (baik di level urllib3 Retry maupun retry manual)
- Cache hasil per halaman (lihat app/core/cache.py) untuk mengurangi beban
  request saat parameter pencarian sama diulang dalam rentang waktu singkat
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.cache import SimpleCache

SEARCH_URL = "https://store.steampowered.com/search/results/"
TAGS_URL_TEMPLATE = "https://store.steampowered.com/tagdata/populartags/{language}"


class SteamAPIError(Exception):
    """Error umum saat berkomunikasi dengan Steam Store."""


class SteamStoreClient:
    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        cache: Optional[SimpleCache] = None,
        cache_ttl_seconds: int = 600,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache = cache or SimpleCache(ttl_seconds=cache_ttl_seconds)

        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "SteamDealFinder/1.0"
                )
            }
        )

    def fetch_specials_page(
        self,
        query: str = "",
        start: int = 0,
        count: int = 100,
        specials_only: bool = True,
        tag_id: Optional[int] = None,
        max_price_filter: Optional[int] = None,
        hide_free_to_play: bool = False,
        cc: str = "id",
        language: str = "indonesian",
        sort_by: str = "_ASC",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Ambil satu halaman hasil pencarian game yang sedang diskon (specials).

        Mengembalikan dict hasil parse JSON Steam, contoh field penting:
            - success (int)
            - total_count (int) -> total game diskon yang tersedia
            - results_html (str) -> potongan HTML berisi daftar game
        """
        normalized_query = (query or "").strip()
        params = {
            "term": normalized_query,
            "start": start,
            "count": count,
            "cc": cc,
            "l": language,
            "sort_by": sort_by,
            "infinite": 1,
        }
        if specials_only:
            params["specials"] = 1
        if tag_id is not None:
            params["tags"] = tag_id
        if max_price_filter is not None:
            params["maxprice"] = max_price_filter
        if hide_free_to_play:
            params["hidef2p"] = 1

        cache_key = (
            "search-v2::"
            f"{int(specials_only)}::{normalized_query}::{start}::{count}::"
            f"{tag_id}::{max_price_filter}::{int(hide_free_to_play)}::"
            f"{cc}::{language}::{sort_by}"
        )

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        last_error: Optional[Exception] = None
        attempts = max(1, self.max_retries)

        for attempt in range(attempts):
            try:
                response = self.session.get(
                    SEARCH_URL, params=params, timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                if not isinstance(data, dict) or "results_html" not in data:
                    raise SteamAPIError(
                        "Format respons Steam tidak sesuai yang diharapkan."
                    )

                if use_cache:
                    self.cache.set(cache_key, data)

                return data

            except requests.exceptions.RequestException as exc:
                last_error = exc
            except ValueError as exc:
                # response.json() gagal parse
                last_error = SteamAPIError(f"Gagal parse JSON dari Steam: {exc}")
            except SteamAPIError as exc:
                last_error = exc

            # Tunggu sebentar sebelum mencoba lagi (selain percobaan terakhir)
            if attempt < attempts - 1:
                time.sleep(0.6 * (attempt + 1))

        raise SteamAPIError(
            f"Gagal mengambil data dari Steam setelah {attempts} percobaan: {last_error}"
        )

    def fetch_popular_tags(
        self,
        language: str = "indonesian",
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """Ambil daftar tag/genre Steam beserta ID-nya."""
        normalized_language = (language or "indonesian").strip()
        cache_key = f"tags::{normalized_language}"

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        try:
            response = self.session.get(
                TAGS_URL_TEMPLATE.format(language=normalized_language),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as exc:
            raise SteamAPIError(f"Gagal mengambil daftar genre/tag Steam: {exc}") from exc
        except ValueError as exc:
            raise SteamAPIError(f"Gagal parse daftar genre/tag Steam: {exc}") from exc

        if not isinstance(data, list):
            raise SteamAPIError("Format daftar genre/tag Steam tidak sesuai.")

        tags: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            tagid = item.get("tagid")
            name = item.get("name")
            if tagid is None or not name:
                continue
            try:
                tagid = int(tagid)
            except (TypeError, ValueError):
                continue
            tags.append({"tagid": tagid, "name": str(name)})

        if use_cache:
            self.cache.set(cache_key, tags)

        return tags

    def fetch_image_bytes(self, url: str) -> bytes:
        """Unduh gambar cover game. Melempar SteamAPIError jika gagal."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as exc:
            raise SteamAPIError(f"Gagal mengunduh gambar: {exc}") from exc
