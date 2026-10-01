"""
VS Code / JetBrains Style Command Palette & Quick Search Overlay Dialog.
"""

from typing import List, Dict, Any, Optional, Callable
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent

from src.gui.styles.icons import IconManager


class QuickSearchDialog(QDialog):
    """Floating overlay quick search bar for fast entity and action navigation."""

    person_selected = Signal(str)

    def __init__(self, main_viewmodel, graph_engine, parent=None):
        super().__init__(parent)
        self.vm = main_viewmodel
        self.graph_engine = graph_engine

        self.setWindowTitle("Szybkie Wyszukiwanie (Ctrl+P)")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(650, 420)

        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                border: 1px solid #89b4fa;
                border-radius: 10px;
            }
            QLineEdit {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                color: #cdd6f4;
            }
            QLineEdit:focus {
                border-color: #89b4fa;
            }
            QListWidget {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #89b4fa;
                color: #11111b;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Search Input with Icon
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        search_icon_lbl = QLabel()
        search_icon = IconManager.get_icon("search", color="#89b4fa", size=20)
        search_icon_lbl.setPixmap(search_icon.pixmap(20, 20))

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Wpisz imię, nazwisko lub frazę do wyszukania...")
        self.input_field.textChanged.connect(self._on_search_text_changed)

        search_row.addWidget(search_icon_lbl)
        search_row.addWidget(self.input_field)
        layout.addLayout(search_row)

        # Results List
        self.results_list = QListWidget()
        self.results_list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self.results_list)

        # Footer Shortcut Hint
        footer_lbl = QLabel("⬆ ⬇ Wybierz  |  ↵ Zatwierdź  |  Esc Zamknij")
        footer_lbl.setStyleSheet("color: #a6adc8; font-size: 11px; margin-top: 4px;")
        footer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer_lbl)

        # Initial populate
        self._populate_initial()

    def _populate_initial(self):
        self._on_search_text_changed("")

    def _on_search_text_changed(self, query: str):
        self.results_list.clear()
        query_str = query.strip().lower()

        matched = []
        if self.graph_engine and hasattr(self.graph_engine, "nodes_data"):
            for node_id, data in self.graph_engine.nodes_data.items():
                name = data.get("name", "")
                if not query_str or query_str in name.lower():
                    matched.append((node_id, name, data.get("sex", "U"), data.get("birth_info", "")))
                    if len(matched) >= 100:
                        break

        for node_id, name, sex, birth in matched:
            sex_str = "♂" if sex == "M" else ("♀" if sex == "F" else "👤")
            info_str = f"   {birth}" if birth else ""
            item = QListWidgetItem(f"{sex_str}  {name}{info_str}")
            item.setData(Qt.ItemDataRole.UserRole, node_id)
            self.results_list.addItem(item)

        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def _on_item_activated(self, item: QListWidgetItem):
        node_id = item.data(Qt.ItemDataRole.UserRole)
        if node_id:
            self.person_selected.emit(node_id)
            self.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self.results_list.keyPressEvent(event)
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current = self.results_list.currentItem()
            if current:
                self._on_item_activated(current)
        else:
            super().keyPressEvent(event)
