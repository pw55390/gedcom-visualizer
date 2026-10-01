"""
ReportLab PDF Document Builder.
Provides page numbering, custom canvas header/footer, UTF-8 Polish fonts, styles, and multi-column tables.
"""

from typing import List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfgen import canvas

from src.reports.fonts import register_polish_fonts, POLISH_FONT_NAME, POLISH_FONT_BOLD_NAME


class NumberedCanvas(canvas.Canvas):
    """Two-pass Canvas to accurately render total page count ('Strona X z Y') and running headers with Polish UTF-8 fonts."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count: int):
        font_regular, font_bold = register_polish_fonts()
        self.saveState()
        self.setFont(font_regular, 9)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (Top)
        self.drawString(54, 800, "GEDCOM Visualizer — Raport Genealogiczny")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 792, 541, 792)

        # Footer (Bottom)
        page_text = f"Strona {self._pageNumber} z {page_count}"
        self.drawRightString(541, 36, page_text)
        self.line(54, 48, 541, 48)
        self.restoreState()


class ReportPdfBuilder:
    def __init__(self, file_path: str):
        self.font_regular, self.font_bold = register_polish_fonts()
        self.file_path = file_path
        self.doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            leftMargin=54,
            rightMargin=54,
            topMargin=64,
            bottomMargin=64
        )
        self.elements: List = []
        self.styles = getSampleStyleSheet()

        # Custom Enterprise Styles with Polish Font Support
        self.title_style = ParagraphStyle(
            "EnterpriseTitle",
            parent=self.styles["Title"],
            fontName=self.font_bold,
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1e293b"),
            alignment=1,  # Center
            spaceAfter=15
        )

        self.heading1_style = ParagraphStyle(
            "EnterpriseH1",
            parent=self.styles["Heading1"],
            fontName=self.font_bold,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=14,
            spaceAfter=8
        )

        self.body_style = ParagraphStyle(
            "EnterpriseBody",
            parent=self.styles["BodyText"],
            fontName=self.font_regular,
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#334155"),
            spaceAfter=5
        )

        self.table_header_style = ParagraphStyle(
            "TableHeader",
            parent=self.styles["Normal"],
            fontName=self.font_bold,
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#ffffff")
        )

        self.table_cell_style = ParagraphStyle(
            "TableCell",
            parent=self.styles["Normal"],
            fontName=self.font_regular,
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#334155")
        )

    def add_title(self, title_text: str):
        self.elements.append(Paragraph(title_text, self.title_style))
        self.elements.append(Spacer(1, 10))

    def add_heading(self, heading_text: str):
        self.elements.append(Paragraph(heading_text, self.heading1_style))

    def add_paragraph(self, text: str):
        self.elements.append(Paragraph(text, self.body_style))

    def add_table(self, data: List[List[str]], col_widths: Optional[List[float]] = None):
        # Convert plain strings in cells to Paragraph objects using Polish font styles
        formatted_data = []
        for row_idx, row in enumerate(data):
            formatted_row = []
            for cell in row:
                style = self.table_header_style if row_idx == 0 else self.table_cell_style
                formatted_row.append(Paragraph(str(cell or "-"), style))
            formatted_data.append(formatted_row)

        t = Table(formatted_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        self.elements.append(t)
        self.elements.append(Spacer(1, 12))

    def add_page_break(self):
        self.elements.append(PageBreak())

    def build(self):
        self.doc.build(self.elements, canvasmaker=NumberedCanvas)
