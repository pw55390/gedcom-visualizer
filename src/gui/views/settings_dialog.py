"""
Categorized Modern Preferences & Settings Dialog.
"""

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QComboBox, QSpinBox, QCheckBox, QPushButton,
    QGroupBox, QFormLayout, QApplication
)
from PySide6.QtCore import Qt, Signal

from src.gui.styles.theme_manager import ThemeManager
from src.gui.styles.icons import IconManager


class SettingsDialog(QDialog):
    """Categorized Enterprise Settings and Preferences modal."""

    theme_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia i Preferencje Aplikacji")
        self.resize(750, 480)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left Category Navigation List
        self.category_list = QListWidget()
        self.category_list.setFixedWidth(200)
        self.category_list.setStyleSheet("""
            QListWidget {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 10px 14px;
                border-radius: 6px;
                font-weight: 600;
                margin-bottom: 4px;
            }
            QListWidget::item:selected {
                background-color: #89b4fa;
                color: #11111b;
            }
        """)

        categories = [
            ("🎨  Wygląd & Motyw", 0),
            ("💾  Baza & GEDCOM", 1),
            ("📄  Eksport & PDF", 2),
            ("⚙  Ogólne & Siatka", 3)
        ]

        for title, idx in categories:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.category_list.addItem(item)

        self.category_list.currentRowChanged.connect(self._on_category_changed)
        layout.addWidget(self.category_list)

        # Right Stacked Pages Area
        right_layout = QVBoxLayout()

        self.stacked_pages = QStackedWidget()
        self.stacked_pages.addWidget(self._create_appearance_page())
        self.stacked_pages.addWidget(self._create_database_page())
        self.stacked_pages.addWidget(self._create_reports_page())
        self.stacked_pages.addWidget(self._create_general_page())

        right_layout.addWidget(self.stacked_pages)

        # Bottom Actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_close = QPushButton("Zamknij")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        right_layout.addLayout(btn_layout)
        layout.addLayout(right_layout)

        self.category_list.setCurrentRow(0)

    def _on_category_changed(self, row: int):
        self.stacked_pages.setCurrentIndex(row)

    def _create_appearance_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        group = QGroupBox("Motyw Interfejsu Użytkownika")
        form = QFormLayout(group)

        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Catppuccin Dark (Ciemny)", "Fluent Light (Jasny)", "Automatyczny (Windows 11 System)"])
        
        current = ThemeManager.current_mode
        if current == "light":
            self.combo_theme.setCurrentIndex(1)
        elif current == "auto":
            self.combo_theme.setCurrentIndex(2)
        else:
            self.combo_theme.setCurrentIndex(0)

        self.combo_theme.currentIndexChanged.connect(self._on_theme_selection_changed)

        form.addRow("Wybierz Motyw Visual:", self.combo_theme)

        chk_animations = QCheckBox("Włącz płynne animacje przejść Qt")
        chk_animations.setChecked(True)
        form.addRow("Animacje UI:", chk_animations)

        layout.addWidget(group)
        layout.addStretch()
        return page

    def _on_theme_selection_changed(self, idx: int):
        app = QApplication.instance()
        if idx == 1:
            ThemeManager.apply_light_theme(app)
            self.theme_changed.emit("light")
        elif idx == 2:
            ThemeManager.apply_auto_theme(app)
            self.theme_changed.emit("auto")
        else:
            ThemeManager.apply_dark_theme(app)
            self.theme_changed.emit("dark")

    def _create_database_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        group = QGroupBox("Parametry Importu Plików GEDCOM")
        form = QFormLayout(group)

        combo_enc = QComboBox()
        combo_enc.addItems(["Automatyczne Wykrywanie (UTF-8 / ANSEL / Windows-1250)", "Wymuś UTF-8", "Wymuś ANSEL (Diakrytyki)", "Wymuś Windows-1250"])
        form.addRow("Detekcja Kodowania:", combo_enc)

        chk_fts = QCheckBox("Automatyczne indeksowanie FTS5 przy starcie")
        chk_fts.setChecked(True)
        form.addRow("Pełnotekstowy Index:", chk_fts)

        layout.addWidget(group)
        layout.addStretch()
        return page

    def _create_reports_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        group = QGroupBox("Konfiguracja Wyglądu Raportów PDF")
        form = QFormLayout(group)

        combo_font = QComboBox()
        combo_font.addItems(["Arial / Segoe UI (Zalecane)", "Tahoma UTF-8", "DejaVu Sans TrueType"])
        form.addRow("Główna Czcionka PDF:", combo_font)

        chk_cover = QCheckBox("Dołączaj okładkę tytułową do raportu osobowego")
        chk_cover.setChecked(True)
        form.addRow("Strona Tytułowa:", chk_cover)

        layout.addWidget(group)
        layout.addStretch()
        return page

    def _create_general_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        group = QGroupBox("Domyślne Głębokości Wizualizacji Drzewa")
        form = QFormLayout(group)

        spin_p = QSpinBox()
        spin_p.setRange(1, 15)
        spin_p.setValue(4)

        spin_d = QSpinBox()
        spin_d.setRange(0, 10)
        spin_d.setValue(1)

        form.addRow("Domyślne Pokolenia Przodków:", spin_p)
        form.addRow("Domyślne Pokolenia Potomków:", spin_d)

        layout.addWidget(group)
        layout.addStretch()
        return page
