"""
ReportLab Polish Font Registration Helper.
Registers TrueType fonts (Arial, Segoe UI, Tahoma, DejaVu) to properly render Polish UTF-8 diacritics.
"""

import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

POLISH_FONT_NAME = "PolishFont"
POLISH_FONT_BOLD_NAME = "PolishFont-Bold"


def register_polish_fonts() -> tuple[str, str]:
    """Finds and registers system TrueType fonts supporting Polish UTF-8 diacritics in ReportLab."""
    try:
        pdfmetrics.getFont(POLISH_FONT_NAME)
        return POLISH_FONT_NAME, POLISH_FONT_BOLD_NAME
    except KeyError:
        pass

    candidates = [
        ("C:\\Windows\\Fonts\\arial.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"),
        ("C:\\Windows\\Fonts\\segoeui.ttf", "C:\\Windows\\Fonts\\segoeuib.ttf"),
        ("C:\\Windows\\Fonts\\tahoma.ttf", "C:\\Windows\\Fonts\\tahomabd.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]

    font_regular = None
    font_bold = None

    for reg_path, bold_path in candidates:
        if os.path.exists(reg_path):
            font_regular = reg_path
            font_bold = bold_path if os.path.exists(bold_path) else reg_path
            break

    if font_regular:
        pdfmetrics.registerFont(TTFont(POLISH_FONT_NAME, font_regular))
        pdfmetrics.registerFont(TTFont(POLISH_FONT_BOLD_NAME, font_bold))
        return POLISH_FONT_NAME, POLISH_FONT_BOLD_NAME

    return "Helvetica", "Helvetica-Bold"
