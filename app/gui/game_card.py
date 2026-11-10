"""
game_card.py

Widget QFrame yang menampilkan satu hasil game: gambar cover, nama,
harga (awal & final), badge diskon, dan tombol untuk membuka halaman Steam.
"""

from __future__ import annotations

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from app.core.models import Game

COVER_WIDTH = 160
COVER_HEIGHT = 75


class GameCardWidget(QFrame):
    def __init__(self, game: Game, parent=None):
        super().__init__(parent)
        self.game = game

        self.setObjectName("gameCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            """
            #gameCard {
                background-color: #1b2838;
                border-radius: 8px;
                border: 1px solid #2a3f5a;
            }
            QLabel#nameLabel {
                color: #ffffff;
                font-size: 15px;
                font-weight: 600;
            }
            QLabel#priceLabel {
                color: #a4d007;
                font-size: 14px;
                font-weight: 600;
            }
            QLabel#originalPriceLabel {
                color: #7d8b9a;
                font-size: 12px;
                text-decoration: line-through;
            }
            QLabel#discountLabel {
                color: #ffffff;
                background-color: #4c6b22;
                border-radius: 4px;
                padding: 2px 6px;
                font-weight: 700;
                font-size: 12px;
            }
            QPushButton#openButton {
                background-color: #66c0f4;
                color: #0e1b25;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 600;
            }
            QPushButton#openButton:hover {
                background-color: #8fd4ff;
            }
            """
        )

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(14)

        # --- Gambar cover ---
        self.image_label = QLabel()
        self.image_label.setFixedSize(COVER_WIDTH, COVER_HEIGHT)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "background-color: #0e1b25; border-radius: 4px; color: #556678;"
        )
        self.image_label.setText("Memuat...")
        root_layout.addWidget(self.image_label)

        # --- Info tengah (nama, harga) ---
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.name_label = QLabel(game.name)
        self.name_label.setObjectName("nameLabel")
        self.name_label.setWordWrap(True)
        info_layout.addWidget(self.name_label)

        price_row = QHBoxLayout()
        price_row.setSpacing(8)

        if game.discount_percent > 0:
            discount_label = QLabel(f"-{game.discount_percent}%")
            discount_label.setObjectName("discountLabel")
            price_row.addWidget(discount_label)

        if game.display_initial_price:
            original_price_label = QLabel(game.display_initial_price)
            original_price_label.setObjectName("originalPriceLabel")
            price_row.addWidget(original_price_label)

        final_price_label = QLabel(game.display_price)
        final_price_label.setObjectName("priceLabel")
        price_row.addWidget(final_price_label)

        price_row.addStretch(1)
        info_layout.addLayout(price_row)
        info_layout.addStretch(1)

        root_layout.addLayout(info_layout, stretch=1)

        # --- Tombol buka Steam ---
        self.open_button = QPushButton("Buka di Steam")
        self.open_button.setObjectName("openButton")
        self.open_button.setCursor(Qt.PointingHandCursor)
        self.open_button.clicked.connect(self._open_store_page)
        self.open_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        root_layout.addWidget(self.open_button, alignment=Qt.AlignVCenter)

    def _open_store_page(self):
        if self.game.store_url:
            QDesktopServices.openUrl(QUrl(self.game.store_url))

    def set_image_bytes(self, image_bytes: bytes):
        pixmap = QPixmap()
        if pixmap.loadFromData(image_bytes):
            scaled = pixmap.scaled(
                COVER_WIDTH,
                COVER_HEIGHT,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
            self.image_label.setText("")
        else:
            self.set_image_failed()

    def set_image_failed(self):
        self.image_label.setText("Tidak ada\ngambar")
