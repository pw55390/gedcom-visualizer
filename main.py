"""
Production Entry Point for GEDCOM Visualizer Desktop Application.
Initializes Database, ViewModels, Themes, Splash Screen, and PySide6 Event Loop.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt

from src.database.engine import DatabaseEngine
from src.gui.viewmodels.main_viewmodel import MainViewModel
from src.gui.views.main_window import MainWindow
from src.gui.views.splash_screen import EnterpriseSplashScreen
from src.gui.styles.theme_manager import ThemeManager


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GEDCOM Visualizer 2026")
    app.setOrganizationName("GEDCOM Visualizer Systems")

    # Apply Default Dark Theme
    ThemeManager.apply_dark_theme(app)

    # Show Enterprise Splash Screen
    splash = EnterpriseSplashScreen("2026 Edition v2.5.0")
    splash.show()
    app.processEvents()

    splash.set_progress(20, "Inicjalizacja środowiska relacyjnego...")
    app.processEvents()

    # Initialize SQLite DB Engine & ViewModels
    db_engine = DatabaseEngine("sqlite:///genealogy_database.db")
    db_engine.init_db()

    splash.set_progress(50, "Ładowanie indeksów wyszukiwania FTS5...")
    app.processEvents()

    vm = MainViewModel(db_engine)

    splash.set_progress(80, "Budowanie modułów wizualizacji i architektury MVVM...")
    app.processEvents()

    window = MainWindow(vm)

    splash.set_progress(100, "Uruchamianie interfejsu użytkownika...")
    app.processEvents()

    # Display main window and close splash
    window.show()
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
