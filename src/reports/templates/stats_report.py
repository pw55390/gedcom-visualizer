"""
Demographic & Statistical Summary PDF Generator Template.
"""

from sqlalchemy.orm import Session
from src.statistics.stats_engine import DemographicStatsEngine
from src.reports.pdf_builder import ReportPdfBuilder


class StatsReportTemplate:
    def __init__(self, session: Session):
        self.session = session
        self.stats_engine = DemographicStatsEngine(session)

    def generate_pdf(self, output_path: str):
        """Generates a complete Demographic & Statistical PDF Report."""
        builder = ReportPdfBuilder(output_path)
        builder.add_title("Raport Statystyk Demograficznych")

        summary = self.stats_engine.get_summary_statistics()

        builder.add_heading("1. Ogólne Zestawienie Populacji")
        summary_table = [
            ["Wskaźnik", "Wartość"],
            ["Łączna liczba osób w bazie", str(summary["total_persons"])],
            ["Liczba mężczyzn", str(summary["male_count"])],
            ["Liczba kobiet", str(summary["female_count"])],
            ["Procentowy udział mężczyzn", f"{summary['sex_ratio_male_pct']}%"],
            ["Średnia długość życia", f"{summary['avg_lifespan']} lat"]
        ]
        builder.add_table(summary_table, col_widths=[240, 247])

        builder.add_heading("2. Najczęstsze Nazwiska")
        top_surnames = self.stats_engine.get_top_surnames(limit=10)
        if top_surnames:
            surname_table = [["Lp.", "Nazwisko", "Liczba Rekordów"]]
            for idx, item in enumerate(top_surnames, 1):
                surname_table.append([str(idx), item["surname"], str(item["count"])])
            builder.add_table(surname_table, col_widths=[50, 240, 197])
        else:
            builder.add_paragraph("Brak wystarczających danych o nazwiskach.")

        builder.build()
