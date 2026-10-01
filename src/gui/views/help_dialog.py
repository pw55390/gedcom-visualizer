"""
GEDCOM Help & Reference Dialog (Pomoc i Słownik GEDCOM).
Provides searchable documentation for GEDCOM tags, date modifiers, month codes, and genealogy symbols.
"""

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QLabel,
    QPushButton
)
from PySide6.QtCore import Qt


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pomoc i Słownik GEDCOM — GEDCOM Visualizer")
        self.resize(850, 600)

        layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()

        # Tab 1: Tag Dictionary
        self.tab_widget.addTab(self._create_tags_tab(), "Tagi GEDCOM")

        # Tab 2: Date Modifiers
        self.tab_widget.addTab(self._create_dates_tab(), "Skróty Dat i Modyfikatory")

        # Tab 3: Months & Symbols
        self.tab_widget.addTab(self._create_months_tab(), "Miesiące i Symbole")

        layout.addWidget(self.tab_widget)

        # Bottom Close Button
        btn_close = QPushButton("Zamknij Okno Pomocy")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    def _create_tags_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Search Filter Bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Szukaj tagu lub pojęcia:"))
        self.tag_search_input = QLineEdit()
        self.tag_search_input.setPlaceholderText("Wpisz np. OCCU, Notatka, Zawód, RESI...")
        self.tag_search_input.textChanged.connect(self._filter_tags_table)
        search_layout.addWidget(self.tag_search_input)
        layout.addLayout(search_layout)

        # Table of Tags
        self.tags_table = QTableWidget()
        self.tags_table.setColumnCount(4)
        self.tags_table.setHorizontalHeaderLabels(["Tag GEDCOM", "Nazwa Polska", "Opis i Zastosowanie", "Przykład Wartości"])
        self.tags_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tags_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tags_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tags_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tags_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.tags_data = [
            ("NOTE", "Notatka / Opis", "Swobodny tekst notatki genealogicznej lub informacji biograficznej", "Notatka: Mieszkał w posesji nr 9"),
            ("OCCU", "Zawód", "Wykonywany zawód, profesja lub stanowisko", "Karbowy / Profesor / Szewc"),
            ("RESI", "Zamieszkanie", "Miejsce lub okres zamieszkiwania pod wskazanym adresem", "Białobrzegi posesja nr 9"),
            ("EDUC", "Wykształcenie", "Osiągnięty poziom wykształcenia lub ukończona szkoła", "Uniwersytet Jagielloński"),
            ("TITL", "Tytuł / Godność", "Tytuł szlachecki, naukowy lub honorowy", "Hrabia / dr hab."),
            ("RELG", "Religia / Wyznanie", "Przynależność wyznaniowa", "Rzymskokatolickie / Ewangelickie"),
            ("FACT", "Fakt", "Dowolny inny znany fakt z życia osoby", "Odznaczony medalem"),
            ("BIRT", "Urodzenie", "Zdarzenie narodzin osoby", "DATE 20 MAY 1946"),
            ("DEAT", "Zgon", "Zdarzenie śmierci osoby", "DATE 30 DEC 1991"),
            ("CHR", "Chrzest (Chrześcijański)", "Zdarzenie chrztu świętego", "DATE 1862, Parafia Białobrzegi"),
            ("BAPM", "Chrzest", "Zdarzenie chrztu (ogólne)", "kościoł katolicki Trójcy św."),
            ("BURI", "Pochówek / Pogrzeb", "Miejsce i data pochówku lub cmentarza", "Cmentarz Komunalny w Śremie"),
            ("EMIG", "Emigracja", "Wyjazd z kraju na stałe", "Z Polski do USA"),
            ("IMMI", "Imigracja", "Przyjazd i osiedlenie się w nowym kraju", "Przyjazd do Nowego Jorku"),
            ("CENS", "Spis Ludności", "Wpis w oficjalnym spisie ludności", "Spis powszechny z 1921 r."),
            ("IDNO", "Numer Identyfikacyjny", "Oficjalny identyfikator (np. PESEL, NIP, numer dowodu)", "PESEL: 46052000000"),
            ("_MARNM", "Nazwisko po mężu", "Nazwisko przyjęte po zawarciu małżeństwa (MyHeritage/Gramps)", "Gutkiewicz / Walczak"),
            ("NAME", "Imię i Nazwisko", "Pełne imię i nazwisko osoby", "Stanisław Kostka /Gutkiewicz/"),
            ("GIVN", "Imiona", "Imiona nadane osoby", "Stanisław Kostka"),
            ("SURN", "Nazwisko", "Nazwisko rodowe osoby", "Gutkiewicz"),
            ("SEX", "Płeć", "Płeć biologiczna osoby (M = Mężczyzna, F = Kobieta)", "M / F"),
            ("MARR", "Małżeństwo", "Zdarzenie zawarcia związku małżeńskiego", "DATE 1857"),
            ("DIV", "Rozwód", "Zdarzenie rozwiązania małżeństwa", "DATE 1920"),
            ("SOUR", "Cytowane Źródło", "Odnośnik do źródła dokumentującego fakt", "@S500022@ (MyHeritage Trees)"),
            ("PAGE", "Strona Źródła", "Dokładny odnośnik lub URL w źródle", "https://myheritage.pl/profile..."),
            ("QUAY", "Wiarygodność Źródła", "Ocena pewności źródła (0 = niepewne, 3 = bardzo pewne)", "3"),
            ("ADDR", "Adres Zamieszkania", "Strukturalny adres pocztowy/zamieszkania", "posesja nr 9, Białobrzegi"),
            ("_UPD", "Data Aktualizacji", "Stempel czasowy Ostatniej edycji z serwisu genealogicznego", "6 JUL 2026 10:52:56 GMT"),
            ("_UID", "Unikalny GUID", "Globalnie unikalny identyfikator rekordu", "6A4BD02A1C5798D94F60655E614A1D5C"),
            ("RIN", "Numer RIN", "Numer identyfikacyjny rekordu z oprogramowania źródłowego", "MH:I500547")
        ]

        self._populate_tags_table(self.tags_data)
        layout.addWidget(self.tags_table)

        return widget

    def _populate_tags_table(self, rows):
        self.tags_table.setRowCount(len(rows))
        for i, (tag, name, desc, ex) in enumerate(rows):
            self.tags_table.setItem(i, 0, QTableWidgetItem(tag))
            self.tags_table.setItem(i, 1, QTableWidgetItem(name))
            self.tags_table.setItem(i, 2, QTableWidgetItem(desc))
            self.tags_table.setItem(i, 3, QTableWidgetItem(ex))

    def _filter_tags_table(self, text: str):
        query = text.lower().strip()
        filtered = [
            row for row in self.tags_data
            if any(query in item.lower() for item in row)
        ]
        self._populate_tags_table(filtered)

    def _create_dates_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("<b>Skróty Modyfikatorów Dat używane w GEDCOM i ich polskie znaczenie:</b>"))

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Skrót GEDCOM", "Polskie Tłumaczenie", "Znaczenie", "Przykład Zapisu"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        date_modifiers = [
            ("ABT / ABOUT", "ok. (około)", "Data przybliżona, szacowana na podstawie wydarzeń", "ABT 1836  ->  ok. 1836"),
            ("BEF / BEFORE", "przed", "Wydarzenie miało miejsce przed podaną datą", "BEF 1843  ->  przed 1843"),
            ("AFT / AFTER", "po", "Wydarzenie miało miejsce po podanej dacie", "AFT 1900  ->  po 1900"),
            ("BET ... AND ...", "pomiędzy ... a ...", "Wydarzenie zaszło w przedziale czasowym", "BET 1815 AND 1820  ->  pomiędzy 1815 a 1820"),
            ("FROM ... TO ...", "od ... do ...", "Trwanie stanu w przedziale czasowym", "FROM 1815 TO 1820  ->  od 1815 do 1820"),
            ("EST / ESTIMATED", "szac.", "Data obliczona szacunkowo (np. z wieku)", "EST 1750  ->  szac. 1750"),
            ("CAL / CALCULATED", "oblicz.", "Data dokładnie wyliczona (np. data zgonu minus wiek)", "CAL 1820  ->  oblicz. 1820")
        ]

        table.setRowCount(len(date_modifiers))
        for i, (abbr, pl, desc, ex) in enumerate(date_modifiers):
            table.setItem(i, 0, QTableWidgetItem(abbr))
            table.setItem(i, 1, QTableWidgetItem(pl))
            table.setItem(i, 2, QTableWidgetItem(desc))
            table.setItem(i, 3, QTableWidgetItem(ex))

        layout.addWidget(table)
        return widget

    def _create_months_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("<b>Trzyliterowe skróty miesięcy w GEDCOM oraz symbole wizualizacji:</b>"))

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Kod GEDCOM", "Miesiąc po Polsku", "Skrót Wyświetlany"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        months = [
            ("JAN", "Styczeń", "sty"),
            ("FEB", "Luty", "lut"),
            ("MAR", "Marzec", "mar"),
            ("APR", "Kwiecień", "kwi"),
            ("MAY", "Maj", "maj"),
            ("JUN", "Czerwiec", "cze"),
            ("JUL", "Lipiec", "lip"),
            ("AUG", "Sierpień", "sie"),
            ("SEP", "Wrzesień", "wrz"),
            ("OCT", "Październik", "paź"),
            ("NOV", "Listopad", "lis"),
            ("DEC", "Grudzień", "gru")
        ]

        table.setRowCount(len(months))
        for i, (code, full_pl, short_pl) in enumerate(months):
            table.setItem(i, 0, QTableWidgetItem(code))
            table.setItem(i, 1, QTableWidgetItem(full_pl))
            table.setItem(i, 2, QTableWidgetItem(short_pl))

        layout.addWidget(table)

        # Symbols Box
        symbols_box = QLabel(
            "<b>Oznaczenia używane na wizualizacji drzewa:</b><br/>"
            "• <b>*</b>  —  Data / miejsce urodzenia (np. <i>* 15 sty 1900, Białobrzegi</i>)<br/>"
            "• <b>†</b>  —  Data / miejsce zgonu (np. <i>† ok. 1943, Germany</i>)<br/>"
            "• <b>M</b>  —  Płeć męska (Niebieska ramka kafelka)<br/>"
            "• <b>F</b>  —  Płeć żeńska (Różowa ramka kafelka)"
        )
        symbols_box.setStyleSheet("background-color: #1e293b; color: #f8fafc; padding: 10px; border-radius: 6px;")
        layout.addWidget(symbols_box)

        return widget
