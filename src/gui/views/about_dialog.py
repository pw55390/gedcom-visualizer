"""
Commercial Grade "About" Dialog for Genealogy Enterprise.
"""

import sys
import platform
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QApplication, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.gui.styles.icons import IconManager


class AboutDialog(QDialog):
    """Enterprise Product information dialog displaying system environment and licenses."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("O Programie — GEDCOM Visualizer 2026")
        self.setFixedSize(600, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Section with Branding
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        logo_lbl = QLabel()
        logo_icon = IconManager.get_icon("tree_view", color="#89b4fa", size=56)
        logo_lbl.setPixmap(logo_icon.pixmap(56, 56))

        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(4)

        title = QLabel("GEDCOM Visualizer")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #89b4fa;")

        version = QLabel("Wersja: 2026 Edition v2.5.0")
        version.setStyleSheet("font-size: 13px; font-weight: 600; color: #cdd6f4;")

        subtitle = QLabel("Zaawansowane Środowisko Analizy i Wizualizacji Genealogicznej")
        subtitle.setStyleSheet("font-size: 12px; color: #a6adc8;")

        info_vbox.addWidget(title)
        info_vbox.addWidget(version)
        info_vbox.addWidget(subtitle)

        header_layout.addWidget(logo_lbl)
        header_layout.addLayout(info_vbox)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #313244;")
        layout.addWidget(line)

        # System Information Box
        sys_frame = QFrame()
        sys_frame.setStyleSheet("""
            QFrame {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 12px;
            }
            QLabel {
                font-size: 12px;
                color: #cdd6f4;
            }
        """)
        sys_layout = QVBoxLayout(sys_frame)
        sys_layout.setSpacing(6)

        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        os_ver = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"

        sys_layout.addWidget(QLabel(f"<b>System Operacyjny:</b> {os_ver}"))
        sys_layout.addWidget(QLabel(f"<b>Środowisko Python:</b> v{python_ver}"))
        sys_layout.addWidget(QLabel("<b>Framework GUI:</b> PySide6 / Qt 6 (Native Windows 11 Fluent)"))
        sys_layout.addWidget(QLabel("<b>Silnik Bazy & Grafu:</b> SQLite3 FTS5, SQLAlchemy 2.0, NetworkX 3"))
        sys_layout.addWidget(QLabel("<b>Silnik Raportowania:</b> ReportLab PDF Engine TrueType"))

        layout.addWidget(sys_frame)

        # Copyright & License
        copyright_lbl = QLabel("© 2026 GEDCOM Visualizer Systems Inc. Wszelkie prawa zastrzeżone.")
        copyright_lbl.setStyleSheet("font-size: 11px; color: #a6adc8;")
        copyright_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_lbl)

        # Actions
        btn_layout = QHBoxLayout()

        btn_copy = QPushButton("Kopiuj Informacje Systemowe")
        btn_copy.clicked.connect(self._copy_system_info)

        btn_close = QPushButton("Zamknij")
        btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(btn_copy)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _copy_system_info(self):
        info = f"""GEDCOM Visualizer 2026 v2.5.0
OS: {platform.system()} {platform.release()}
Python: {sys.version}
Qt: PySide6 / Qt6
DB: SQLite FTS5 / SQLAlchemy 2.0
Graph: NetworkX DAG Engine"""
        QApplication.clipboard().setText(info)
        QMessageBox.information(self, "Kopiowanie", "Informacje systemowe zostały skopiowane do schowka.")
