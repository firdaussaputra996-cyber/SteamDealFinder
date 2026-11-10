"""
main_window.py

Window utama Steam Deal Finder: form filter pencarian, tombol cari,
area hasil (scrollable list of GameCardWidget), dan status bar.
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.api.steam_api import SteamStoreClient
from app.core.models import Game
from app.gui.game_card import GameCardWidget
from app.workers.image_worker import ImageLoaderWorker
from app.workers.search_worker import SearchWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Deal Finder")
        self.resize(760, 640)
        self.setStyleSheet("background-color: #0e1b25;")

        self.client = SteamStoreClient()
        self.search_worker: Optional[SearchWorker] = None
        self.image_worker: Optional[ImageLoaderWorker] = None
        self.card_widgets: dict[str, GameCardWidget] = {}

        self._build_ui()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title_label = QLabel("Steam Deal Finder")
        title_label.setStyleSheet(
            "color: white; font-size: 22px; font-weight: 700;"
        )
        main_layout.addWidget(title_label)

        subtitle_label = QLabel(
            "Cari game diskon Steam berdasarkan harga & persentase diskon (harga regional Indonesia)"
        )
        subtitle_label.setStyleSheet("color: #8fa3b8; font-size: 12px;")
        main_layout.addWidget(subtitle_label)

        # --- Form filter ---
        form_frame = QFrame()
        form_frame.setStyleSheet(
            "background-color: #1b2838; border-radius: 8px;"
        )
        form_layout = QHBoxLayout(form_frame)
        form_layout.setContentsMargins(14, 14, 14, 14)
        form_layout.setSpacing(16)

        label_style = "color: #c7d5e0; font-size: 12px;"
        spin_style = (
            "QSpinBox { background-color: #0e1b25; color: white; "
            "border: 1px solid #2a3f5a; border-radius: 4px; padding: 4px; }"
        )

        min_price_box = QVBoxLayout()
        min_price_label = QLabel("Harga Minimum (Rp)")
        min_price_label.setStyleSheet(label_style)
        self.min_price_spin = QSpinBox()
        self.min_price_spin.setRange(0, 5_000_000)
        self.min_price_spin.setSingleStep(5000)
        self.min_price_spin.setStyleSheet(spin_style)
        min_price_box.addWidget(min_price_label)
        min_price_box.addWidget(self.min_price_spin)
        form_layout.addLayout(min_price_box)

        max_price_box = QVBoxLayout()
        max_price_label = QLabel("Harga Maksimum (Rp)")
        max_price_label.setStyleSheet(label_style)
        self.max_price_spin = QSpinBox()
        self.max_price_spin.setRange(0, 5_000_000)
        self.max_price_spin.setSingleStep(5000)
        self.max_price_spin.setValue(100_000)
        self.max_price_spin.setStyleSheet(spin_style)
        max_price_box.addWidget(max_price_label)
        max_price_box.addWidget(self.max_price_spin)
        form_layout.addLayout(max_price_box)

        discount_box = QVBoxLayout()
        discount_label = QLabel("Diskon Minimum (%)")
        discount_label.setStyleSheet(label_style)
        self.min_discount_spin = QSpinBox()
        self.min_discount_spin.setRange(0, 100)
        self.min_discount_spin.setSingleStep(5)
        self.min_discount_spin.setValue(50)
        self.min_discount_spin.setStyleSheet(spin_style)
        discount_box.addWidget(discount_label)
        discount_box.addWidget(self.min_discount_spin)
        form_layout.addLayout(discount_box)

        self.search_button = QPushButton("Cari Deal")
        self.search_button.setCursor(Qt.PointingHandCursor)
        self.search_button.setStyleSheet(
            "QPushButton { background-color: #66c0f4; color: #0e1b25; "
            "border-radius: 6px; padding: 10px 20px; font-weight: 700; } "
            "QPushButton:disabled { background-color: #3a4b5c; color: #7d8b9a; }"
        )
        self.search_button.clicked.connect(self.start_search)
        form_layout.addWidget(self.search_button, alignment=Qt.AlignBottom)

        main_layout.addWidget(form_frame)

        # --- Status label ---
        self.status_label = QLabel("Siap mencari. Atur filter lalu klik \"Cari Deal\".")
        self.status_label.setStyleSheet("color: #8fa3b8; font-size: 12px;")
        main_layout.addWidget(self.status_label)

        # --- Area hasil ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setSpacing(10)
        self.results_layout.addStretch(1)

        self.scroll_area.setWidget(self.results_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

    # -------------------------------------------------------------- Search

    def start_search(self):
        # Hentikan worker sebelumnya bila masih berjalan
        if self.search_worker is not None and self.search_worker.isRunning():
            self.search_worker.cancel()
            self.search_worker.wait()
        if self.image_worker is not None and self.image_worker.isRunning():
            self.image_worker.cancel()
            self.image_worker.wait()

        self._clear_results()

        min_price = self.min_price_spin.value()
        max_price = self.max_price_spin.value()
        min_discount = self.min_discount_spin.value()

        if max_price > 0 and min_price > max_price:
            self.status_label.setText(
                "Harga minimum tidak boleh lebih besar dari harga maksimum."
            )
            return

        self.search_button.setEnabled(False)
        self.status_label.setText("Memulai pencarian...")

        self.search_worker = SearchWorker(
            client=self.client,
            min_price=min_price if min_price > 0 else None,
            max_price=max_price if max_price > 0 else None,
            min_discount=min_discount if min_discount > 0 else None,
        )
        self.search_worker.progress.connect(self._on_progress)
        self.search_worker.finished_search.connect(self._on_search_finished)
        self.search_worker.error_occurred.connect(self._on_search_error)
        self.search_worker.start()

    def _on_progress(self, message: str):
        self.status_label.setText(message)

    def _on_search_error(self, message: str):
        self.status_label.setText(f"Terjadi kesalahan: {message}")
        self.search_button.setEnabled(True)

    def _on_search_finished(self, games: List[Game]):
        self.search_button.setEnabled(True)

        if not games:
            self.status_label.setText(
                "Tidak ada game yang cocok dengan kriteria. Coba longgarkan filter."
            )
            return

        self.status_label.setText(f"Ditemukan {len(games)} deal. Memuat gambar...")

        for game in games:
            card = GameCardWidget(game)
            self.card_widgets[game.appid] = card
            # Sisipkan sebelum stretch terakhir
            self.results_layout.insertWidget(self.results_layout.count() - 1, card)

        image_targets = [(g.appid, g.header_image) for g in games]
        self.image_worker = ImageLoaderWorker(self.client, image_targets)
        self.image_worker.image_loaded.connect(self._on_image_loaded)
        self.image_worker.image_failed.connect(self._on_image_failed)
        self.image_worker.start()

    def _on_image_loaded(self, appid: str, image_bytes: bytes):
        card = self.card_widgets.get(appid)
        if card is not None:
            card.set_image_bytes(image_bytes)

    def _on_image_failed(self, appid: str):
        card = self.card_widgets.get(appid)
        if card is not None:
            card.set_image_failed()

    def _clear_results(self):
        self.card_widgets.clear()
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def closeEvent(self, event):
        if self.search_worker is not None and self.search_worker.isRunning():
            self.search_worker.cancel()
            self.search_worker.wait(2000)
        if self.image_worker is not None and self.image_worker.isRunning():
            self.image_worker.cancel()
            self.image_worker.wait(2000)
        super().closeEvent(event)
