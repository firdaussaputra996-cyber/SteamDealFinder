"""
models.py

Berisi dataclass Game yang merepresentasikan satu hasil pencarian deal Steam,
sudah dalam bentuk ternormalisasi (harga sebagai integer Rupiah, dsb.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Game:
    appid: str
    name: str
    store_url: str
    header_image: str
    is_free: bool
    discount_percent: int          # 0 jika tidak ada diskon
    initial_price: Optional[int]   # dalam Rupiah, None jika free / tidak diketahui
    final_price: Optional[int]     # dalam Rupiah, None jika free / tidak diketahui
    currency: str = "IDR"

    @property
    def display_price(self) -> str:
        if self.is_free:
            return "Gratis"
        if self.final_price is None:
            return "-"
        return f"Rp {self.final_price:,}".replace(",", ".")

    @property
    def display_initial_price(self) -> str:
        if self.is_free or self.initial_price is None:
            return ""
        if self.initial_price == self.final_price:
            return ""
        return f"Rp {self.initial_price:,}".replace(",", ".")
