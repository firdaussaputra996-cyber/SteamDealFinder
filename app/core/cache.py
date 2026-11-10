"""
cache.py

Cache sederhana berbasis file JSON dengan TTL (time-to-live).
Dipakai untuk menyimpan hasil request Steam Store search sementara,
supaya pencarian ulang dengan parameter yang sama tidak selalu memukul
jaringan Steam berkali-kali dalam rentang waktu singkat.

Tidak memakai library eksternal (tidak butuh diskcache/appdirs) supaya
dependensi proyek tetap minim.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


class SimpleCache:
    """Cache berbasis file JSON di disk, key -> (timestamp, data)."""

    def __init__(self, cache_dir: Optional[Path] = None, ttl_seconds: int = 900):
        if cache_dir is None:
            cache_dir = Path.home() / ".steam_deal_finder_cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def _key_to_path(self, key: str) -> Path:
        digest = hashlib.md5(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def get(self, key: str) -> Optional[Any]:
        """Ambil data dari cache jika ada dan belum kedaluwarsa."""
        path = self._key_to_path(key)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
        except (json.JSONDecodeError, OSError):
            # File korup, anggap cache miss dan bersihkan.
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            return None

        timestamp = payload.get("timestamp", 0)
        if time.time() - timestamp > self.ttl_seconds:
            return None  # Kedaluwarsa

        return payload.get("data")

    def set(self, key: str, data: Any) -> None:
        """Simpan data ke cache."""
        path = self._key_to_path(key)
        payload = {"timestamp": time.time(), "data": data}
        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(payload, f)
        except OSError:
            # Gagal menulis cache bukan error fatal, cukup diabaikan.
            pass

    def clear(self) -> None:
        """Hapus seluruh isi cache."""
        for file in self.cache_dir.glob("*.json"):
            try:
                file.unlink()
            except OSError:
                pass
