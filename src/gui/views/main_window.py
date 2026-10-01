"""
Enterprise Commercial Desktop Main Window (IDE / ArcGIS Pro Inspired Architecture).
Features Multi-Dock Panels, Multi-Tab Workspace, Quick Search Command Palette,
SVG Icons, Dynamic Theme Manager, and Full MVVM Event Bindings.
"""

import os
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDockWidget,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QComboBox, QTreeWidget,
    QTreeWidgetItem, QTabWidget, QFileDialog, QMessageBox, QApplication, QSpinBox, QInputDialog,
    QToolButton
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence

from src.gui.viewmodels.main_viewmodel import MainViewModel
from src.gui.styles.theme_manager import ThemeManager
from src.gui.styles.icons import IconManager

from src.visualization.graphics_view import GenealogyGraphicsView
from src.visualization.graph_engine import KinshipGraphEngine
from src.visualization.exporters import DiagramExporter
from src.reports.templates.person_report import PersonReportTemplate

from src.gui.views.help_dialog import HelpDialog
from src.gui.views.about_dialog import AboutDialog
from src.gui.views.settings_dialog import SettingsDialog
from src.gui.views.splash_screen import EnterpriseSplashScreen
from src.gui.views.welcome_screen import WelcomeScreen
from src.gui.views.quick_search_dialog import QuickSearchDialog
from src.gui.views.table_explorer_view import TableExplorerView
from src.gui.views.stats_view import StatsView


class MainWindow(QMainWindow):
    def __init__(self, viewmodel: MainViewModel):
        super().__init__()
        self.vm = viewmodel
        self.is_dark_theme = True
        self.graph_engine = KinshipGraphEngine(self.vm.session)
        self.current_attrs_map: dict = {}

        self.setWindowTitle("GEDCOM Visualizer 2026")
        self.resize(1450, 920)

        self._setup_ui()
        self._bind_viewmodel()

        # Load initial person list
        self.vm.search_persons("")

    def _setup_ui(self):
        # 1. Central Multi-Tab Workspace (occupying ~75% width)
        self.central_tab_widget = QTabWidget()
        
        # Tab 1: Interactive Tree View Canvas
        self.graphics_view = GenealogyGraphicsView(on_person_selected_cb=self.vm.select_person)
        self.central_tab_widget.addTab(
            self.graphics_view,
            IconManager.get_icon("tree_view", color="#89b4fa", size=16),
            "Wizualizacja Drzewa"
        )

        # Tab 2: Welcome / Start Dashboard
        self.welcome_screen = WelcomeScreen()
        self.welcome_screen.open_gedcom_requested.connect(self._on_import_gedcom)
        self.welcome_screen.new_project_requested.connect(self._on_new_project)
        self.welcome_screen.help_requested.connect(self._show_help_dialog)
        self.welcome_screen.settings_requested.connect(self._show_settings_dialog)
        self.welcome_screen.about_requested.connect(self._show_about_dialog)
        self.welcome_screen.open_recent_file_requested.connect(self._open_recent_file)

        self.central_tab_widget.addTab(
            self.welcome_screen,
            IconManager.get_icon("home", color="#89b4fa", size=16),
            "Start"
        )

        # Tab 3: Statistics & Demographics
        self.stats_view = StatsView(session=self.vm.session)
        self.central_tab_widget.addTab(
            self.stats_view,
            IconManager.get_icon("stats", color="#89b4fa", size=16),
            "Statystyki"
        )

        # Tab 4: ArcGIS Pro / Table Explorer
        self.table_view = TableExplorerView()
        self.table_view.person_selected.connect(self.vm.select_person)
        self.table_view.btn_refresh.clicked.connect(self._refresh_table_view)

        self.central_tab_widget.addTab(
            self.table_view,
            IconManager.get_icon("table_view", color="#89b4fa", size=16),
            "Tabela Danych"
        )

        self.setCentralWidget(self.central_tab_widget)

        # 2. Dock Windows
        self._setup_explorer_dock()
        self._setup_editor_dock()
        self._setup_validation_dock()

        # 3. Menus & Toolbars
        self._setup_menus_and_toolbars()

        # 4. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Gotowy — GEDCOM Visualizer Engine Ready")

    def _setup_explorer_dock(self):
        self.dock_explorer = QDockWidget("Eksplorator & Szukaj (FTS5)", self)
        self.dock_explorer.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(120)  # 120ms debounce
        self.search_timer.timeout.connect(self._do_search)

        search_header = QHBoxLayout()
        search_icon = QLabel()
        search_icon.setPixmap(IconManager.get_icon("search", color="#89b4fa", size=18).pixmap(18, 18))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Szukaj osób, nazwisk, miejsc...")
        self.search_input.textChanged.connect(self._on_search_text_changed)

        search_header.addWidget(search_icon)
        search_header.addWidget(self.search_input)

        self.person_count_lbl = QLabel("Baza: 0 osób")
        self.person_count_lbl.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: 600;")

        self.person_list_widget = QListWidget()
        self.person_list_widget.itemSelectionChanged.connect(self._on_person_selected)

        layout.addLayout(search_header)
        layout.addWidget(self.person_count_lbl)
        layout.addWidget(self.person_list_widget)

        self.dock_explorer.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_explorer)

    def _setup_editor_dock(self):
        self.dock_editor = QDockWidget("Szczegóły & Edycja Osoby", self)
        self.dock_editor.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        layout.addWidget(QLabel("<b>Wybierz atrybut do edycji:</b>"))
        self.combo_attr_selector = QComboBox()
        self.combo_attr_selector.currentIndexChanged.connect(self._on_attribute_combo_selected)
        layout.addWidget(self.combo_attr_selector)

        layout.addWidget(QLabel("Wartość wybranego atrybutu:"))
        self.edit_attr_value = QLineEdit()
        layout.addWidget(self.edit_attr_value)

        self.btn_save_attr = QPushButton("Zapisz Zmianę Atrybutu (Undoable)")
        self.btn_save_attr.setIcon(IconManager.get_icon("save", color="#11111b", size=16))
        self.btn_save_attr.clicked.connect(self._on_save_attr_clicked)

        self.btn_add_attr = QPushButton("+ Dodaj Nowy Atrybut GEDCOM...")
        self.btn_add_attr.clicked.connect(self._on_add_attr_clicked)

        self.btn_export_person_pdf = QPushButton("Wygeneruj Kartę Osobową (PDF)")
        self.btn_export_person_pdf.setIcon(IconManager.get_icon("pdf_export", color="#11111b", size=16))
        self.btn_export_person_pdf.clicked.connect(self._on_generate_person_pdf)

        self.lbl_person_stats = QLabel("Brak zaznaczonej osoby")
        self.lbl_person_stats.setStyleSheet("background-color: #181825; padding: 8px; border-radius: 6px; color: #a6adc8; font-size: 11px;")

        layout.addWidget(self.btn_save_attr)
        layout.addWidget(self.btn_add_attr)
        layout.addWidget(self.btn_export_person_pdf)
        layout.addWidget(self.lbl_person_stats)
        layout.addStretch()

        self.dock_editor.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_editor)

    def _setup_validation_dock(self):
        self.dock_validation = QDockWidget("Dziennik Walidacji & Anomalii", self)
        self.dock_validation.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)

        self.tree_validation = QTreeWidget()
        self.tree_validation.setHeaderLabels(["Poziom", "Kategoria", "ID Encji", "Opis Problemu"])

        layout.addWidget(self.tree_validation)
        self.dock_validation.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_validation)

    def _setup_menus_and_toolbars(self):
        menubar = self.menuBar()

        # 1. File Menu
        menu_file = menubar.addMenu("Plik")
        
        act_import = QAction(IconManager.get_icon("folder_open", color="#89b4fa"), "Otwórz / Importuj GEDCOM...", self)
        act_import.setShortcut("Ctrl+O")
        act_import.triggered.connect(self._on_import_gedcom)

        act_export = QAction(IconManager.get_icon("save", color="#89b4fa"), "Zapisz / Eksportuj GEDCOM...", self)
        act_export.setShortcut("Ctrl+S")
        act_export.triggered.connect(self._on_export_gedcom)

        act_tree_pdf = QAction(IconManager.get_icon("pdf_export", color="#89b4fa"), "Eksportuj Drzewo do PDF...", self)
        act_tree_pdf.triggered.connect(self._on_export_tree_pdf)

        act_exit = QAction("Wyjście", self)
        act_exit.triggered.connect(self.close)

        menu_file.addAction(act_import)
        menu_file.addAction(act_export)
        menu_file.addSeparator()
        menu_file.addAction(act_tree_pdf)
        menu_file.addSeparator()
        menu_file.addAction(act_exit)

        # 2. Edit Menu
        menu_edit = menubar.addMenu("Edycja")
        act_undo = QAction(IconManager.get_icon("undo", color="#89b4fa"), "Cofnij (Undo)", self)
        act_undo.setShortcut("Ctrl+Z")
        act_undo.triggered.connect(self.vm.undo)

        act_redo = QAction(IconManager.get_icon("redo", color="#89b4fa"), "Ponów (Redo)", self)
        act_redo.setShortcut("Ctrl+Y")
        act_redo.triggered.connect(self.vm.redo)

        act_quick_search = QAction(IconManager.get_icon("search", color="#89b4fa"), "Szybkie Wyszukiwanie...", self)
        act_quick_search.setShortcut("Ctrl+P")
        act_quick_search.triggered.connect(self._show_quick_search_dialog)

        menu_edit.addAction(act_undo)
        menu_edit.addAction(act_redo)
        menu_edit.addSeparator()
        menu_edit.addAction(act_quick_search)

        # 3. View Menu
        menu_view = menubar.addMenu("Widok")
        
        act_view_tree = QAction(IconManager.get_icon("tree_view", color="#89b4fa"), "Wizualizacja Drzewa", self)
        act_view_tree.triggered.connect(lambda: self.central_tab_widget.setCurrentIndex(0))

        act_view_start = QAction(IconManager.get_icon("home", color="#89b4fa"), "Strona Startowa", self)
        act_view_start.triggered.connect(lambda: self.central_tab_widget.setCurrentIndex(1))

        act_view_stats = QAction(IconManager.get_icon("stats", color="#89b4fa"), "Statystyki", self)
        act_view_stats.triggered.connect(lambda: self.central_tab_widget.setCurrentIndex(2))

        act_view_table = QAction(IconManager.get_icon("table_view", color="#89b4fa"), "Tabela Danych", self)
        act_view_table.triggered.connect(lambda: self.central_tab_widget.setCurrentIndex(3))

        act_theme = QAction(IconManager.get_icon("theme", color="#89b4fa"), "Przełącz Motyw (Dark/Light)", self)
        act_theme.triggered.connect(self._toggle_theme)

        menu_view.addAction(act_view_start)
        menu_view.addAction(act_view_tree)
        menu_view.addAction(act_view_table)
        menu_view.addAction(act_view_stats)
        menu_view.addSeparator()
        menu_view.addAction(act_theme)

        # 4. Tools Menu
        menu_tools = menubar.addMenu("Narzędzia")
        act_validate = QAction(IconManager.get_icon("validate", color="#89b4fa"), "Uruchom Walidację Bazy...", self)
        act_validate.triggered.connect(self.vm.run_validation)

        act_settings = QAction(IconManager.get_icon("settings", color="#89b4fa"), "Ustawienia i Preferencje...", self)
        act_settings.triggered.connect(self._show_settings_dialog)

        menu_tools.addAction(act_validate)
        menu_tools.addSeparator()
        menu_tools.addAction(act_settings)

        # 5. Help Menu
        menu_help = menubar.addMenu("Pomoc")
        act_help = QAction(IconManager.get_icon("help", color="#89b4fa"), "Słownik Tagów i Skrótów GEDCOM... (F1)", self)
        act_help.setShortcut("F1")
        act_help.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_help.triggered.connect(self._show_help_dialog)

        act_about = QAction(IconManager.get_icon("info", color="#89b4fa"), "O Programie...", self)
        act_about.triggered.connect(self._show_about_dialog)

        menu_help.addAction(act_help)
        menu_help.addSeparator()
        menu_help.addAction(act_about)

        # Modern SVG Icon Toolbar
        toolbar = QToolBar("Główny Pasek Narzędzi")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)

        toolbar.addAction(act_import)
        toolbar.addAction(act_export)
        toolbar.addSeparator()

        toolbar.addAction(act_undo)
        toolbar.addAction(act_redo)
        toolbar.addSeparator()

        toolbar.addAction(act_quick_search)
        toolbar.addSeparator()

        # Add Person & Family Quick Buttons
        btn_add_person = QToolButton()
        btn_add_person.setIcon(IconManager.get_icon("person_add", color="#89b4fa", size=20))
        btn_add_person.setToolTip("Dodaj nową osobę do bazy")
        btn_add_person.clicked.connect(self._on_add_person_quick)

        toolbar.addWidget(btn_add_person)

        toolbar.addSeparator()

        # Generation Control SpinBoxes (Przodkowie & Potomkowie)
        toolbar.addWidget(QLabel(" Przodkowie: "))
        self.spin_generations = QSpinBox()
        self.spin_generations.setRange(1, 15)
        self.spin_generations.setValue(4)
        self.spin_generations.setToolTip("Liczba pokoleń przodków do wyświetlenia na drzewie (w górę)")
        self.spin_generations.valueChanged.connect(self._on_generations_changed)
        toolbar.addWidget(self.spin_generations)

        toolbar.addWidget(QLabel(" Potomkowie: "))
        self.spin_descendants = QSpinBox()
        self.spin_descendants.setRange(0, 10)
        self.spin_descendants.setValue(1)
        self.spin_descendants.setToolTip("Liczba pokoleń zstępnych/potomków do wyświetlenia na drzewie (w dół)")
        self.spin_descendants.valueChanged.connect(self._on_generations_changed)
        toolbar.addWidget(self.spin_descendants)

        toolbar.addSeparator()
        toolbar.addAction(act_tree_pdf)
        toolbar.addSeparator()
        toolbar.addAction(act_validate)
        toolbar.addAction(act_theme)
        toolbar.addAction(act_settings)
        toolbar.addSeparator()

        # Dedicated Help & About Buttons
        btn_help_toolbar = QToolButton()
        btn_help_toolbar.setIcon(IconManager.get_icon("help", color="#89b4fa", size=20))
        btn_help_toolbar.setToolTip("Słownik tagów i pomoc (F1)")
        btn_help_toolbar.clicked.connect(self._show_help_dialog)
        toolbar.addWidget(btn_help_toolbar)

        btn_about_toolbar = QToolButton()
        btn_about_toolbar.setIcon(IconManager.get_icon("info", color="#89b4fa", size=20))
        btn_about_toolbar.setToolTip("O programie")
        btn_about_toolbar.clicked.connect(self._show_about_dialog)
        toolbar.addWidget(btn_about_toolbar)

        self.addToolBar(toolbar)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F1:
            self._show_help_dialog()
            event.accept()
            return
        elif event.key() == Qt.Key.Key_F5:
            self.graph_engine.rebuild_graph()
            self._refresh_all_views()
            event.accept()
            return
        super().keyPressEvent(event)

    def _show_help_dialog(self):
        try:
            dialog = HelpDialog(self)
            dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się otworzyć pomocy: {e}")

    def _show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def _show_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def _show_quick_search_dialog(self):
        dialog = QuickSearchDialog(self.vm, self.graph_engine, self)
        dialog.person_selected.connect(self.vm.select_person)
        dialog.exec()

    def _on_new_project(self):
        res = QMessageBox.question(
            self,
            "Nowy Projekt",
            "Czy na pewno chcesz utworzyć czystą bazę danych? Niezapisane zmiany zostaną utracone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            self.vm.db_engine.init_db()
            self.vm._refresh_repositories()
            self.graph_engine.rebuild_graph()
            self._refresh_all_views()
            self.status_bar.showMessage("Utworzono czystą relacyjną bazę genealogiczną.")

    def _open_recent_file(self, file_path: str):
        if os.path.exists(file_path):
            self._on_import_gedcom_path(file_path)

    def _on_add_person_quick(self):
        given, ok1 = QInputDialog.getText(self, "Dodaj Osobę", "Podaj imię / imiona:")
        if ok1 and given:
            surn, ok2 = QInputDialog.getText(self, "Dodaj Osobę", "Podaj nazwisko rodowe:")
            if ok2 and surn:
                from src.core.enums import Sex
                p = self.vm.person_repo.create_person(given_names=given, surname=surn, sex=Sex.UNKNOWN)
                self.vm.session.commit()
                self.graph_engine.rebuild_graph()
                self._refresh_all_views()
                self.vm.select_person(p.id)
                self.status_bar.showMessage(f"Dodano nową osobę: {given} {surn}")

    def _refresh_all_views(self):
        if hasattr(self, "table_view"):
            self.table_view.load_persons(self.graph_engine)
        if hasattr(self, "stats_view"):
            self.stats_view.refresh_stats()
        if hasattr(self, "person_count_lbl"):
            count = len(self.graph_engine.nodes_data) if hasattr(self.graph_engine, "nodes_data") else 0
            self.person_count_lbl.setText(f"Baza: {count} osób")

    def _refresh_table_view(self):
        self.table_view.load_persons(self.graph_engine)
        self.status_bar.showMessage("Zaktualizowano tabelę danych.")

    def _bind_viewmodel(self):
        self.vm.search_results_updated.connect(self._on_search_results_updated)
        self.vm.person_selected.connect(self._on_person_details_updated)
        self.vm.validation_completed.connect(self._on_validation_completed)
        self.vm.status_message.connect(self.status_bar.showMessage)

    def _on_search_text_changed(self, text: str):
        self.search_timer.start()

    def _do_search(self):
        query = self.search_input.text()
        self.vm.search_persons(query, cached_nodes=self.graph_engine.nodes_data)

    def _on_search_results_updated(self, results: list):
        self.person_list_widget.clear()
        for res in results:
            item = QListWidgetItem(f"{res['title']} ({res.get('snippet', '')})")
            item.setData(Qt.ItemDataRole.UserRole, res['entity_id'] if 'entity_id' in res else res['id'])
            self.person_list_widget.addItem(item)

    def _on_person_selected(self):
        items = self.person_list_widget.selectedItems()
        if items:
            person_id = items[0].data(Qt.ItemDataRole.UserRole)
            self.vm.select_person(person_id)

    def _on_person_details_updated(self, person_id: str):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.status_bar.showMessage("Wczytywanie szczegółów i wizualizacji drzewa...")
        QApplication.processEvents()
        try:
            details = self.vm.get_selected_person_details()
            if details:
                self.lbl_person_stats.setText(
                    f"Zdarzenia: {details['events_count']} | Rodzice: {details['parents_count']} | Dzieci: {details['children_count']}"
                )
                # Populate Attribute Selector ComboBox
                self.current_attrs_map = self.vm.get_person_attributes_map(person_id)
                self.combo_attr_selector.blockSignals(True)
                self.combo_attr_selector.clear()

                for label, meta in self.current_attrs_map.items():
                    self.combo_attr_selector.addItem(label, meta)

                self.combo_attr_selector.blockSignals(False)

                if self.combo_attr_selector.count() > 0:
                    self.combo_attr_selector.setCurrentIndex(0)
                    self._on_attribute_combo_selected(0)

                # Render ancestors tree on canvas with selected generation depth (using cached graph)
                if self.graph_engine.graph.number_of_nodes() == 0:
                    self.graph_engine.rebuild_graph()

                gens = self.spin_generations.value()
                desc = self.spin_descendants.value()
                self.graphics_view.render_ancestors_tree(
                    person_id, self.graph_engine, max_generations=gens, max_descendants=desc
                )
                self.status_bar.showMessage("Gotowy")
        finally:
            QApplication.restoreOverrideCursor()

    def _on_attribute_combo_selected(self, idx: int):
        meta = self.combo_attr_selector.currentData()
        if meta:
            self.edit_attr_value.setText(meta.get("val", ""))

    def _on_save_attr_clicked(self):
        meta = self.combo_attr_selector.currentData()
        if meta and self.vm.selected_person_id:
            new_val = self.edit_attr_value.text()
            self.vm.update_person_attribute(self.vm.selected_person_id, meta, new_val)
            self.graph_engine.rebuild_graph()
            self._refresh_all_views()

    def _on_add_attr_clicked(self):
        if not self.vm.selected_person_id:
            QMessageBox.warning(self, "Brak wyboru", "Najpierw wybierz osobę z listy.")
            return

        tag, ok1 = QInputDialog.getText(self, "Nowy Atrybut", "Podaj tag GEDCOM (np. NOTE, OCCU, RESI, TITL):")
        if ok1 and tag:
            val, ok2 = QInputDialog.getText(self, "Nowy Atrybut", f"Podaj wartość dla '{tag}':")
            if ok2 and val:
                self.vm.add_person_custom_attribute(self.vm.selected_person_id, tag, val)
                self.graph_engine.rebuild_graph()
                self._refresh_all_views()

    def _on_generations_changed(self, val: int = 0):
        if self.vm.selected_person_id:
            gens = self.spin_generations.value()
            desc = self.spin_descendants.value()
            self.graphics_view.render_ancestors_tree(
                self.vm.selected_person_id, self.graph_engine, max_generations=gens, max_descendants=desc
            )
            self.status_bar.showMessage(f"Wyświetlanie {gens} pokoleń przodków i {desc} pokoleń potomków.")

    def _on_export_tree_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Eksportuj Drzewo do PDF", "", "Pliki PDF (*.pdf)")
        if file_path:
            DiagramExporter.export_to_pdf(self.graphics_view.scene_obj, file_path)
            self.status_bar.showMessage(f"Wyeksportowano drzewo do pliku PDF: {file_path}")

    def _on_generate_person_pdf(self):
        if not self.vm.selected_person_id:
            QMessageBox.warning(self, "Brak wyboru", "Najpierw wybierz osobę z listy.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Wygeneruj Kartę Osobową (PDF)", "", "Pliki PDF (*.pdf)")
        if file_path:
            template = PersonReportTemplate(self.vm.session)
            template.generate_pdf(self.vm.selected_person_id, file_path)
            self.status_bar.showMessage(f"Wygenerowano kartę osobową PDF: {file_path}")

    def _on_save_person_clicked(self):
        if self.vm.selected_person_id:
            given = self.edit_given_names.text()
            surname = self.edit_surname.text()
            self.vm.update_person_name(self.vm.selected_person_id, given, surname)
            self.graph_engine.rebuild_graph()
            self._refresh_all_views()

    def _on_validation_completed(self, issues: list):
        self.tree_validation.clear()
        for issue in issues:
            item = QTreeWidgetItem([
                issue.severity, issue.category, issue.entity_id, issue.message
            ])
            self.tree_validation.addTopLevelItem(item)

    def _on_import_gedcom(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Otwórz plik GEDCOM", "", "Pliki GEDCOM (*.ged *.gedcom)")
        if file_path:
            self._on_import_gedcom_path(file_path)

    def _on_import_gedcom_path(self, file_path: str):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.status_bar.showMessage("Przetwarzanie i budowanie struktury drzewa...")
        QApplication.processEvents()
        try:
            self.vm.import_gedcom(file_path)
            self.graph_engine.rebuild_graph()
            self._refresh_all_views()
            if hasattr(self, "welcome_screen"):
                self.welcome_screen.add_recent_file(file_path)
            self.status_bar.showMessage("Baza GEDCOM została pomyślnie zaimportowana.")
        finally:
            QApplication.restoreOverrideCursor()

    def _on_export_gedcom(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Zapisz plik GEDCOM", "", "Pliki GEDCOM (*.ged)")
        if file_path:
            self.vm.export_gedcom(file_path)

    def _toggle_theme(self):
        app = QApplication.instance()
        if self.is_dark_theme:
            ThemeManager.apply_light_theme(app)
            self.is_dark_theme = False
        else:
            ThemeManager.apply_dark_theme(app)
            self.is_dark_theme = True
