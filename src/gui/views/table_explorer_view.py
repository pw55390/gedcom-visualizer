"""
ArcGIS Pro / Excel Style Professional Data Grid View for Person Records.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QComboBox
)
from PySide6.QtCore import Qt, Signal

from src.gui.styles.icons import IconManager


class TableExplorerView(QWidget):
    """Grid view displaying database person entities in an ArcGIS Pro / Excel tabular format."""

    person_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_persons_data: List[dict] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Toolbar & Filter Row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        search_icon_lbl = QLabel()
        icon = IconManager.get_icon("search", color="#89b4fa", size=18)
        search_icon_lbl.setPixmap(icon.pixmap(18, 18))

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filtruj tabelę (wpisz imię, nazwisko, płeć...)...")
        self.filter_input.textChanged.connect(self._apply_filter)

        self.sex_filter_combo = QComboBox()
        self.sex_filter_combo.addItems(["Wszystkie płcie", "Mężczyźni (M)", "Kobiety (F)", "Nieokreślone (U)"])
        self.sex_filter_combo.currentIndexChanged.connect(self._apply_filter)

        self.btn_refresh = QPushButton("Odśwież Tabelę")
        self.btn_refresh.setIcon(IconManager.get_icon("refresh", color="#11111b", size=16))

        filter_row.addWidget(search_icon_lbl)
        filter_row.addWidget(self.filter_input, stretch=2)
        filter_row.addWidget(self.sex_filter_combo)
        filter_row.addWidget(self.btn_refresh)

        layout.addLayout(filter_row)

        # Table Grid
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID Encji", "Imię i Nazwisko", "Płeć", "Urodzenie / Szczegóły", "Zgon / Informacje"
        ])
        
        # Grid settings
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

    def load_persons(self, graph_engine):
        """Populates the table grid from graph_engine nodes data."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        if not graph_engine or not hasattr(graph_engine, "nodes_data"):
            return

        self.all_persons_data = list(graph_engine.nodes_data.values())
        self.table.setRowCount(len(self.all_persons_data))

        for row, data in enumerate(self.all_persons_data):
            p_id = data.get("id", "")
            name = data.get("name", "Brak nazwiska")
            sex = data.get("sex", "U")
            birth = data.get("birth_info", "")
            death = data.get("death_info", "")

            item_id = QTableWidgetItem(p_id[:8] + "...")
            item_id.setData(Qt.ItemDataRole.UserRole, p_id)
            item_name = QTableWidgetItem(name)
            item_sex = QTableWidgetItem("♂ Mężczyzna" if sex == "M" else ("♀ Kobieta" if sex == "F" else "Nieznana"))
            item_birth = QTableWidgetItem(birth)
            item_death = QTableWidgetItem(death)

            self.table.setItem(row, 0, item_id)
            self.table.setItem(row, 1, item_name)
            self.table.setItem(row, 2, item_sex)
            self.table.setItem(row, 3, item_birth)
            self.table.setItem(row, 4, item_death)

        self.table.setSortingEnabled(True)

    def _apply_filter(self):
        filter_text = self.filter_input.text().lower().strip()
        sex_filter_idx = self.sex_filter_combo.currentIndex()

        for row in range(self.table.rowCount()):
            name = self.table.item(row, 1).text().lower() if self.table.item(row, 1) else ""
            sex_text = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
            birth = self.table.item(row, 3).text().lower() if self.table.item(row, 3) else ""

            match_text = not filter_text or (filter_text in name or filter_text in birth)
            match_sex = True
            if sex_filter_idx == 1:
                match_sex = "♂" in sex_text
            elif sex_filter_idx == 2:
                match_sex = "♀" in sex_text
            elif sex_filter_idx == 3:
                match_sex = "Nieznana" in sex_text

            self.table.setRowHidden(row, not (match_text and match_sex))

    def _on_selection_changed(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            id_item = self.table.item(row, 0)
            if id_item:
                p_id = id_item.data(Qt.ItemDataRole.UserRole)
                if p_id:
                    self.person_selected.emit(p_id)
