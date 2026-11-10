"""
parser.py

Parsing HTML dari endpoint search Steam Store (results_html) menjadi
data mentah per game. Ditulis defensif karena ini bergantung pada markup
HTML Steam yang tidak resmi didokumentasikan dan bisa berubah sewaktu-waktu.

Setiap baris yang gagal di-parse akan dilewati (di-skip), bukan membuat
seluruh proses gagal.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


def parse_price_to_int(price_text: str) -> Optional[int]:
    """Ubah string harga seperti 'Rp 149.500' menjadi integer 149500.

    Mengembalikan None jika teks tidak mengandung angka yang bisa diparse.
    """
    if not price_text:
        return None
    digits = re.sub(r"[^0-9]", "", price_text)
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _is_free_text(text: str) -> bool:
    text_lower = text.strip().lower()
    return any(
        keyword in text_lower
        for keyword in ("gratis untuk dimainkan", "free to play", "play for free", "gratis")
    )


def parse_search_results_html(html: str) -> List[Dict[str, Any]]:
    """Parse potongan HTML results_html dari Steam search menjadi list dict mentah.

    Setiap dict berisi:
        appid, name, store_url, header_image, is_free,
        discount_percent, initial_price_text, final_price_text
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("a.search_result_row")

    parsed: List[Dict[str, Any]] = []

    for row in rows:
        try:
            appid = row.get("data-ds-appid")
            if not appid:
                continue
            # Bundle bisa punya beberapa appid dipisah koma, ambil yang pertama saja.
            appid = appid.split(",")[0].strip()

            store_url = row.get("href", "").split("?")[0]

            title_tag = row.select_one(".title")
            name = title_tag.get_text(strip=True) if title_tag else None
            if not name:
                continue

            img_tag = row.select_one("img")
            header_image = img_tag.get("src", "") if img_tag else ""

            price_block = (
                row.select_one(".search_price_discount_combined")
                or row.select_one(".discount_block")
                or row.select_one(".search_price")
            )

            discount_percent = 0
            initial_price_text = ""
            final_price_text = ""
            is_free = False

            if price_block is not None:
                discount_tag = price_block.select_one(".discount_pct")
                if discount_tag:
                    discount_match = re.search(r"-?(\d+)%", discount_tag.get_text(strip=True))
                    if discount_match:
                        discount_percent = int(discount_match.group(1))

                original_tag = price_block.select_one(".discount_original_price")
                final_tag = price_block.select_one(".discount_final_price")

                if final_tag:
                    final_price_text = final_tag.get_text(strip=True)
                else:
                    # Tidak ada elemen diskon, ambil teks harga polos.
                    plain_text = price_block.get_text(strip=True)
                    final_price_text = plain_text

                if original_tag:
                    initial_price_text = original_tag.get_text(strip=True)
                else:
                    initial_price_text = final_price_text

                if _is_free_text(final_price_text) or _is_free_text(
                    price_block.get_text(strip=True)
                ):
                    is_free = True

            parsed.append(
                {
                    "appid": appid,
                    "name": name,
                    "store_url": store_url,
                    "header_image": header_image,
                    "is_free": is_free,
                    "discount_percent": discount_percent,
                    "initial_price_text": initial_price_text,
                    "final_price_text": final_price_text,
                }
            )
        except Exception:
            # Baris bermasalah dilewati saja, tidak menghentikan parsing keseluruhan.
            continue

    return parsed
