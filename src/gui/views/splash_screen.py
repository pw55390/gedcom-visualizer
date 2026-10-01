"""
Enterprise Qt Splash Screen for Application Startup.
"""

from PySide6.QtWidgets import QSplashScreen, QProgressBar, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient


class EnterpriseSplashScreen(QSplashScreen):
    """Modern splash screen displaying application branding, version, and loading status."""

    def __init__(self, version_str: str = "2026 Enterprise Edition v2.5.0"):
        pixmap = QPixmap(520, 300)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw Background Gradient
        gradient = QLinearGradient(0, 0, 520, 300)
        gradient.setColorAt(0.0, QColor("#1e1e2e"))
        gradient.setColorAt(1.0, QColor("#11111b"))

        painter.setBrush(gradient)
        painter.setPen(QColor("#313244"))
        painter.drawRoundedRect(0, 0, 520, 300, 12, 12)

        # App Title & Subtitle
        painter.setPen(QColor("#89b4fa"))
        font_title = QFont("Segoe UI", 20, QFont.Weight.Bold)
        painter.setFont(font_title)
        painter.drawText(40, 70, "GEDCOM Visualizer")

        painter.setPen(QColor("#a6adc8"))
        font_sub = QFont("Segoe UI", 11)
        painter.setFont(font_sub)
        painter.drawText(40, 98, "Professional GIS & Family Tree Engine")

        painter.setPen(QColor("#6c7086"))
        font_ver = QFont("Segoe UI", 9)
        painter.setFont(font_ver)
        painter.drawText(40, 125, version_str)

        # Features Badges
        painter.setPen(QColor("#313244"))
        painter.setBrush(QColor("#181825"))
        painter.drawRoundedRect(40, 150, 440, 60, 6, 6)

        painter.setPen(QColor("#cdd6f4"))
        font_badge = QFont("Segoe UI", 9)
        painter.setFont(font_badge)
        painter.drawText(55, 185, "• NetworkX DAG Topology   • FTS5 Indexed Search   • UTF-8 / ANSEL Engine")

        painter.end()

        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)

        # Loading Message Label inside splash
        self.status_label = QLabel("Inicjalizacja modułów aplikacji...", self)
        self.status_label.setGeometry(40, 230, 440, 20)
        self.status_label.setStyleSheet("color: #a6adc8; font-size: 11px; background: transparent;")

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(40, 255, 440, 6)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #313244;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #89b4fa;
                border-radius: 3px;
            }
        """)

    def set_progress(self, value: int, message: str = ""):
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)
        self.repaint()
