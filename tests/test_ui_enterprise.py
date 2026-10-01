"""
Unit tests for Enterprise UI Components: IconManager, Splash, WelcomeScreen, QuickSearchDialog, AboutDialog, SettingsDialog, TableExplorerView, and StatsView.
"""

import pytest
from PySide6.QtWidgets import QApplication, QLabel
from src.database.engine import DatabaseEngine
from src.gui.viewmodels.main_viewmodel import MainViewModel
from src.gui.styles.icons import IconManager
from src.gui.styles.theme_manager import ThemeManager
from src.gui.views.splash_screen import EnterpriseSplashScreen
from src.gui.views.welcome_screen import WelcomeScreen
from src.gui.views.about_dialog import AboutDialog
from src.gui.views.settings_dialog import SettingsDialog
from src.gui.views.quick_search_dialog import QuickSearchDialog
from src.gui.views.table_explorer_view import TableExplorerView
from src.gui.views.stats_view import StatsView
from src.gui.views.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def db_engine():
    engine = DatabaseEngine(db_path=":memory:")
    engine.init_db()
    return engine


def test_icon_manager(qapp):
    icon = IconManager.get_icon("folder_open", color="#89b4fa", size=24)
    assert not icon.isNull()
    
    icon_cached = IconManager.get_icon("folder_open", color="#89b4fa", size=24)
    assert icon == icon_cached


def test_theme_manager(qapp):
    ThemeManager.apply_dark_theme(qapp)
    assert ThemeManager.current_mode == "dark"

    ThemeManager.apply_light_theme(qapp)
    assert ThemeManager.current_mode == "light"

    ThemeManager.apply_auto_theme(qapp)
    assert ThemeManager.current_mode == "auto"


def test_splash_screen(qapp):
    splash = EnterpriseSplashScreen("v2.5.0")
    splash.set_progress(50, "Testing...")
    assert splash.progress_bar.value() == 50


def test_welcome_screen(qapp):
    ws = WelcomeScreen()
    ws.add_recent_file("C:/test.ged")
    assert ws.recent_list.count() == 1


def test_about_dialog(qapp):
    dialog = AboutDialog()
    assert dialog.windowTitle() != ""


def test_settings_dialog(qapp):
    dialog = SettingsDialog()
    assert dialog.category_list.count() == 4


def test_quick_search_dialog(qapp, db_engine):
    vm = MainViewModel(db_engine)
    dialog = QuickSearchDialog(vm, None)
    assert dialog.windowTitle() != ""


def test_table_explorer_view(qapp, db_engine):
    view = TableExplorerView()
    assert view.table.columnCount() == 5


def test_stats_view(qapp, db_engine):
    session = db_engine.get_session()
    view = StatsView(session=session)
    view.refresh_stats()
    assert view.card_total.findChildren(QLabel)[1].text() == "0"


def test_main_window_enterprise(qapp, db_engine):
    vm = MainViewModel(db_engine)
    window = MainWindow(vm)
    assert window.central_tab_widget.count() == 4
    assert window.dock_explorer is not None
    assert window.dock_editor is not None
    assert window.dock_validation is not None
