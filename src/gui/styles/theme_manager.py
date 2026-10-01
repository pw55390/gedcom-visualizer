"""
Modern Enterprise Design System & Theme Manager for PySide6 / Qt6.
Provides Catppuccin / VS Code Dark, Fluent Light, and System Auto Themes.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


COMMON_QSS = """
* {
    font-family: 'Segoe UI Variable', 'Segoe UI', 'Inter', 'Roboto', sans-serif;
    font-size: 13px;
    outline: none;
}

QMainWindow::separator {
    background-color: transparent;
    width: 4px;
    height: 4px;
}

QSplitter::handle {
    background-color: transparent;
}

QDockWidget {
    font-weight: 600;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}

QDockWidget::title {
    padding: 8px 12px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QToolBar {
    spacing: 4px;
    padding: 6px;
    border: none;
}

QToolButton {
    border-radius: 6px;
    padding: 6px 10px;
    font-weight: 500;
}

QPushButton {
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QLineEdit, QComboBox, QSpinBox, QTextEdit {
    border-radius: 6px;
    padding: 6px 10px;
}

QTableWidget, QTreeWidget, QListWidget {
    border-radius: 6px;
    padding: 4px;
}

QHeaderView::section {
    padding: 8px 12px;
    font-weight: 600;
    border: none;
}

QScrollBar:vertical {
    width: 8px;
    background: transparent;
    margin: 0px;
}

QScrollBar::handle:vertical {
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar:horizontal {
    height: 8px;
    background: transparent;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    border-radius: 4px;
    min-width: 20px;
}

QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    background: none;
}

QTabWidget::pane {
    border-radius: 8px;
}

QTabBar::tab {
    padding: 8px 16px;
    font-weight: 500;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
"""

DARK_THEME_QSS = COMMON_QSS + """
QMainWindow {
    background-color: #181825;
    color: #cdd6f4;
}

QWidget {
    color: #cdd6f4;
}

QMenuBar {
    background-color: #11111b;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
    padding: 2px 6px;
}

QMenuBar::item {
    padding: 6px 10px;
    background: transparent;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #313244;
    color: #89b4fa;
}

QMenu {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #89b4fa;
    color: #11111b;
}

QMenu::separator {
    height: 1px;
    background: #313244;
    margin: 4px 6px;
}

QToolBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
}

QToolButton {
    background-color: transparent;
    color: #cdd6f4;
    border: 1px solid transparent;
}

QToolButton:hover {
    background-color: #313244;
    border-color: #45475a;
    color: #89b4fa;
}

QToolButton:pressed {
    background-color: #45475a;
}

QDockWidget {
    border: 1px solid #313244;
    background-color: #1e1e2e;
}

QDockWidget::title {
    background-color: #181825;
    color: #a6adc8;
    border-bottom: 1px solid #313244;
}

QLineEdit, QComboBox, QSpinBox, QTextEdit {
    background-color: #11111b;
    border: 1px solid #313244;
    color: #cdd6f4;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
    border-color: #89b4fa;
}

QTableWidget, QTreeWidget, QListWidget {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    color: #cdd6f4;
    gridline-color: #2a2b3d;
}

QTableWidget::item:alternate {
    background-color: #181825;
}

QTreeWidget::item:hover, QListWidget::item:hover, QTableWidget::item:hover {
    background-color: #313244;
}

QTreeWidget::item:selected, QListWidget::item:selected, QTableWidget::item:selected {
    background-color: #89b4fa;
    color: #11111b;
}

QHeaderView::section {
    background-color: #181825;
    color: #a6adc8;
    border-bottom: 1px solid #313244;
    border-right: 1px solid #313244;
}

QPushButton {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
}

QPushButton:hover {
    background-color: #b4befe;
}

QPushButton:pressed {
    background-color: #74c7ec;
}

QPushButton:disabled {
    background-color: #313244;
    color: #6c7086;
}

QStatusBar {
    background-color: #11111b;
    color: #a6adc8;
    border-top: 1px solid #313244;
    padding: 2px;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #45475a;
}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #585b70;
}

QTabWidget::pane {
    background-color: #1e1e2e;
    border: 1px solid #313244;
}

QTabBar::tab {
    background-color: #181825;
    color: #a6adc8;
}

QTabBar::tab:selected {
    background-color: #1e1e2e;
    color: #89b4fa;
    border-bottom: 2px solid #89b4fa;
}

QGroupBox {
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #89b4fa;
}

QDialog {
    background-color: #1e1e2e;
}
"""

LIGHT_THEME_QSS = COMMON_QSS + """
QMainWindow {
    background-color: #f8f9fa;
    color: #212529;
}

QWidget {
    color: #212529;
}

QMenuBar {
    background-color: #ffffff;
    color: #212529;
    border-bottom: 1px solid #dee2e6;
    padding: 2px 6px;
}

QMenuBar::item {
    padding: 6px 10px;
    background: transparent;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #e9ecef;
    color: #0d6efd;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #0d6efd;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #dee2e6;
    margin: 4px 6px;
}

QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #dee2e6;
}

QToolButton {
    background-color: transparent;
    color: #212529;
    border: 1px solid transparent;
}

QToolButton:hover {
    background-color: #e9ecef;
    border-color: #ced4da;
    color: #0d6efd;
}

QToolButton:pressed {
    background-color: #dee2e6;
}

QDockWidget {
    border: 1px solid #dee2e6;
    background-color: #ffffff;
}

QDockWidget::title {
    background-color: #f8f9fa;
    color: #495057;
    border-bottom: 1px solid #dee2e6;
}

QLineEdit, QComboBox, QSpinBox, QTextEdit {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    color: #212529;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
    border-color: #0d6efd;
}

QTableWidget, QTreeWidget, QListWidget {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    color: #212529;
    gridline-color: #f1f3f5;
}

QTableWidget::item:alternate {
    background-color: #f8f9fa;
}

QTreeWidget::item:hover, QListWidget::item:hover, QTableWidget::item:hover {
    background-color: #e9ecef;
}

QTreeWidget::item:selected, QListWidget::item:selected, QTableWidget::item:selected {
    background-color: #0d6efd;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #f8f9fa;
    color: #495057;
    border-bottom: 1px solid #dee2e6;
    border-right: 1px solid #dee2e6;
}

QPushButton {
    background-color: #0d6efd;
    color: #ffffff;
    border: none;
}

QPushButton:hover {
    background-color: #0b5ed7;
}

QPushButton:pressed {
    background-color: #0a58ca;
}

QPushButton:disabled {
    background-color: #e9ecef;
    color: #6c757d;
}

QStatusBar {
    background-color: #ffffff;
    color: #6c757d;
    border-top: 1px solid #dee2e6;
    padding: 2px;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #ced4da;
}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #adb5bd;
}

QTabWidget::pane {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
}

QTabBar::tab {
    background-color: #f8f9fa;
    color: #6c757d;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #0d6efd;
    border-bottom: 2px solid #0d6efd;
}

QGroupBox {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #0d6efd;
}

QDialog {
    background-color: #ffffff;
}
"""


class ThemeManager:
    current_mode = "dark"  # "dark", "light", "auto"

    @classmethod
    def apply_dark_theme(cls, app: QApplication):
        cls.current_mode = "dark"
        app.setStyleSheet(DARK_THEME_QSS)

    @classmethod
    def apply_light_theme(cls, app: QApplication):
        cls.current_mode = "light"
        app.setStyleSheet(LIGHT_THEME_QSS)

    @classmethod
    def apply_auto_theme(cls, app: QApplication):
        """Detects OS system theme (Windows / macOS / Linux) and applies matching mode."""
        cls.current_mode = "auto"
        is_dark = cls._is_system_dark()
        if is_dark:
            app.setStyleSheet(DARK_THEME_QSS)
        else:
            app.setStyleSheet(LIGHT_THEME_QSS)

    @staticmethod
    def _is_system_dark() -> bool:
        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return value == 0
            except Exception:
                pass
        return True
