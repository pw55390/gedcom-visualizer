"""
Demographic & Statistics Overview Panel with Metric Cards and Top Surnames.
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from src.statistics.stats_engine import DemographicStatsEngine
from src.gui.styles.icons import IconManager


class MetricCard(QFrame):
    """Modern dashboard KPI metric card."""

    def __init__(self, title: str, value_str: str, subtitle: str, color_accent: str = "#89b4fa", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-top: 3px solid {color_accent};
                border-radius: 8px;
                padding: 14px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #a6adc8;")

        val_lbl = QLabel(value_str)
        val_lbl.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {color_accent};")

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("font-size: 11px; color: #6c7086;")

        layout.addWidget(title_lbl)
        layout.addWidget(val_lbl)
        layout.addWidget(sub_lbl)

    def set_value(self, value_str: str, subtitle: str = ""):
        labels = self.findChildren(QLabel)
        if len(labels) >= 2:
            labels[1].setText(value_str)
        if len(labels) >= 3 and subtitle:
            labels[2].setText(subtitle)


class StatsView(QWidget):
    """Statistics and demographic analytics tab view."""

    def __init__(self, session=None, parent=None):
        super().__init__(parent)
        self.session = session
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header_row = QHBoxLayout()
        header_title = QLabel("Analiza Demograficzna i Statystyki Bazy")
        header_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #89b4fa;")

        btn_refresh = QPushButton("Przelicz Statystyki")
        btn_refresh.setIcon(IconManager.get_icon("refresh", color="#11111b", size=16))
        btn_refresh.clicked.connect(self.refresh_stats)

        header_row.addWidget(header_title)
        header_row.addStretch()
        header_row.addWidget(btn_refresh)

        layout.addLayout(header_row)

        # KPI Metric Cards Row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self.card_total = MetricCard("TOTAL OSOB W BAZIE", "0", "Zarejestrowane rekordy", "#89b4fa")
        self.card_males = MetricCard("MĘŻCZYŹNI", "0", "0% populacji", "#38bdf8")
        self.card_females = MetricCard("KOBIETY", "0", "0% populacji", "#f472b6")
        self.card_lifespan = MetricCard("ŚREDNIA DŁUGOŚĆ ŻYCIA", "0 lat", "Na podstawie dat zgonu/urodzenia", "#a6e3a1")

        cards_row.addWidget(self.card_total)
        cards_row.addWidget(self.card_males)
        cards_row.addWidget(self.card_females)
        cards_row.addWidget(self.card_lifespan)

        layout.addLayout(cards_row)

        # Surnames Table Section
        table_group = QFrame()
        table_group.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        table_layout = QVBoxLayout(table_group)
        table_layout.setSpacing(10)

        table_title = QLabel("Najpopularniejsze Nazwiska w Bazie Rodzinnej")
        table_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #cdd6f4;")
        table_layout.addWidget(table_title)

        self.table_surnames = QTableWidget()
        self.table_surnames.setColumnCount(3)
        self.table_surnames.setHorizontalHeaderLabels(["Lp.", "Nazwisko Rodowe", "Liczba Wystąpień w Bazie"])
        self.table_surnames.setAlternatingRowColors(True)
        self.table_surnames.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        header = self.table_surnames.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        table_layout.addWidget(self.table_surnames)
        layout.addWidget(table_group)

    def refresh_stats(self):
        if not self.session:
            return

        engine = DemographicStatsEngine(self.session)
        summary = engine.get_summary_statistics()

        total = summary.get("total_persons", 0)
        males = summary.get("male_count", 0)
        females = summary.get("female_count", 0)
        m_pct = summary.get("sex_ratio_male_pct", 0.0)
        f_pct = round(100.0 - m_pct, 1) if total > 0 else 0.0
        lifespan = summary.get("avg_lifespan", 0.0)

        self.card_total.set_value(str(total), "Zarejestrowane rekordy")
        self.card_males.set_value(str(males), f"{m_pct}% populacji")
        self.card_females.set_value(str(females), f"{f_pct}% populacji")
        self.card_lifespan.set_value(f"{lifespan} lat", "Średni wiek przeżycia")

        top_surnames = engine.get_top_surnames(limit=15)
        self.table_surnames.setRowCount(len(top_surnames))

        for idx, item in enumerate(top_surnames):
            self.table_surnames.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            self.table_surnames.setItem(idx, 1, QTableWidgetItem(item.get("surname", "")))
            self.table_surnames.setItem(idx, 2, QTableWidgetItem(str(item.get("count", 0))))
