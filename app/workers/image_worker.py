"""
image_worker.py

QThread yang mengunduh gambar cover (header image) untuk daftar game hasil
pencarian, secara berurutan di background, dan mengirim tiap gambar begitu
selesai diunduh lewat signal -- supaya UI bisa langsung update per kartu
tanpa menunggu semua gambar selesai, dan tanpa memblokir GUI thread.
"""

from __future__ import annotations

from typing import List, Tuple

from PySide6.QtCore import QThread, Signal

from app.api.steam_api import SteamAPIError, SteamStoreClient


class ImageLoaderWorker(QThread):
    image_loaded = Signal(str, bytes)   # appid, image_bytes
    image_failed = Signal(str)          # appid

    def __init__(self, client: SteamStoreClient, targets: List[Tuple[str, str]], parent=None):
        """
        targets: list of (appid, image_url)
        """
        super().__init__(parent)
        self.client = client
        self.targets = targets
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        for appid, url in self.targets:
            if self._is_cancelled:
                return
            if not url:
                self.image_failed.emit(appid)
                continue
            try:
                image_bytes = self.client.fetch_image_bytes(url)
                self.image_loaded.emit(appid, image_bytes)
            except SteamAPIError:
                self.image_failed.emit(appid)
