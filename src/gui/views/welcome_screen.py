"""
Modern Welcome / Start Screen Dashboard Widget for Genealogy Enterprise.
Provides Quick Launch Cards, Recent Files History, and Documentation Links.
"""

import os
from typing import Callable, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QListWidget, QListWidgetItem, QGraphicsDropShadowEffect, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from src.gui.styles.icons import IconManager


class QuickCard(QFrame):
    """Interactive Card component for Welcome Screen actions."""

    def __init__(self, title: str, description: str, icon_name: str, callback: Callable, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("QuickCard")
        self.setStyleSheet("""
            QFrame#QuickCard {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 10px;
                padding: 16px;
            }
            QFrame#QuickCard:hover {
                background-color: #313244;
                border-color: #89b4fa;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # Icon Label
        icon_lbl = QLabel()
        icon = IconManager.get_icon(icon_name, color="#89b4fa", size=32)
        icon_lbl.setPixmap(icon.pixmap(32, 32))
        layout.addWidget(icon_lbl)

        # Text Layout
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #cdd6f4;")
        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("font-size: 12px; color: #a6adc8;")
        desc_lbl.setWordWrap(True)

        text_layout.addWidget(title_lbl)
        text_layout.addWidget(desc_lbl)

        layout.addLayout(text_layout)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback()
            event.accept()
        else:
            super().mousePressEvent(event)


class WelcomeScreen(QWidget):
    """Start Dashboard with Quick Start Cards and Recent Project Files."""

    open_gedcom_requested = Signal()
    new_project_requested = Signal()
    help_requested = Signal()
    settings_requested = Signal()
    about_requested = Signal()
    open_recent_file_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recent_files = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        # Header Section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)

        title = QLabel("GEDCOM Visualizer 2026")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #89b4fa;")
        
        subtitle = QLabel("Witaj w profesjonalnym środowisku analizy i wizualizacji danych genealogicznych.")
        subtitle.setStyleSheet("font-size: 14px; color: #a6adc8;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)

        # Content Split Layout (Cards on Left, Recent Files on Right)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)

        # Left Column: Quick Actions Cards
        cards_column = QVBoxLayout()
        cards_column.setSpacing(12)

        card_open = QuickCard(
            "Otwórz GEDCOM",
            "Wczytaj plik struktury drzewa genealogicznego (.ged / .gedcom)",
            "folder_open",
            self.open_gedcom_requested.emit
        )
        card_new = QuickCard(
            "Nowy Projekt / Baza",
            "Utwórz nową czystą relacyjną bazę genealogiczną",
            "new_project",
            self.new_project_requested.emit
        )
        card_help = QuickCard(
            "Dokumentacja & Słownik GEDCOM",
            "Przeglądaj opisy tagów, modyfikatorów dat oraz skrótów (F1)",
            "help",
            self.help_requested.emit
        )
        card_settings = QuickCard(
            "Ustawienia Aplikacji",
            "Dostosuj motyw, kodowanie plików, bazę danych oraz parametry wizualizacji",
            "settings",
            self.settings_requested.emit
        )
        card_about = QuickCard(
            "O Programie",
            "Specyfikacja techniczna, wersje silników i licencje",
            "info",
            self.about_requested.emit
        )

        cards_column.addWidget(card_open)
        cards_column.addWidget(card_new)
        cards_column.addWidget(card_help)
        cards_column.addWidget(card_settings)
        cards_column.addWidget(card_about)
        cards_column.addStretch()

        content_layout.addLayout(cards_column, stretch=2)

        # Right Column: Recent Files History Panel
        recent_frame = QFrame()
        recent_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 10px;
                padding: 16px;
            }
        """)
        recent_layout = QVBoxLayout(recent_frame)
        recent_layout.setSpacing(12)

        recent_header = QHBoxLayout()
        recent_title = QLabel("Ostatnie Pliki & Projekty")
        recent_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #cdd6f4;")
        recent_header.addWidget(recent_title)
        recent_layout.addLayout(recent_header)

        self.recent_list = QListWidget()
        self.recent_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 6px;
                margin-bottom: 4px;
            }
            QListWidget::item:hover {
                background-color: #313244;
                color: #89b4fa;
            }
        """)
        self.recent_list.itemDoubleClicked.connect(self._on_recent_file_clicked)
        recent_layout.addWidget(self.recent_list)

        content_layout.addWidget(recent_frame, stretch=1)

        main_layout.addLayout(content_layout)

    def add_recent_file(self, file_path: str):
        if file_path in self._recent_files:
            self._recent_files.remove(file_path)
        self._recent_files.insert(0, file_path)

        self.recent_list.clear()
        for path in self._recent_files[:10]:
            filename = os.path.basename(path)
            item = QListWidgetItem(f"📄 {filename}\n   {path}")
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.recent_list.addItem(item)

    def _on_recent_file_clicked(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and os.path.exists(path):
            self.open_recent_file_requested.emit(path)
