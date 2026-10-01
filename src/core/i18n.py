"""
GEDCOM Polish Translation Engine (i18n).
Translates English GEDCOM date modifiers (ABT, BEF, AFT, BET), months (JAN..DEC), and tags into Polish.
"""

import re

GEDCOM_MONTHS_PL = {
    "JAN": "sty", "FEB": "lut", "MAR": "mar", "APR": "kwi",
    "MAY": "maj", "JUN": "cze", "JUL": "lip", "AUG": "sie",
    "SEP": "wrz", "OCT": "paź", "NOV": "lis", "DEC": "gru"
}

GEDCOM_MODIFIERS_PL = {
    "ABT": "ok.",
    "ABOUT": "ok.",
    "BEF": "przed",
    "BEFORE": "przed",
    "AFT": "po",
    "AFTER": "po",
    "BET": "pomiędzy",
    "BETWEEN": "pomiędzy",
    "AND": "a",
    "FROM": "od",
    "TO": "do",
    "EST": "szac.",
    "CAL": "oblicz."
}

GEDCOM_TAGS_PL = {
    "NAME": "Imię i nazwisko",
    "GIVN": "Imię",
    "SURN": "Nazwisko",
    "_MARNM": "Nazwisko po mężu",
    "SEX": "Płeć",
    "BIRT": "Urodzenie",
    "DEAT": "Zgon",
    "BURI": "Pochówek",
    "CHR": "Chrzest",
    "BAPM": "Chrzest",
    "MARR": "Małżeństwo",
    "DIV": "Rozwód",
    "OCCU": "Zawód",
    "RESI": "Zamieszkanie",
    "EMIG": "Emigracja",
    "IMMI": "Imigracja",
    "CENS": "Spis ludności",
    "NOTE": "Notatka",
    "TITL": "Tytuł",
    "EDUC": "Wykształcenie",
    "RELG": "Religia",
    "FACT": "Fakt",
    "_UPD": "Ostatnia aktualizacja",
    "_UID": "Unikalne ID",
    "RIN": "Numer rekordu RIN",
    "SOUR": "Cytowane źródło"
}


def translate_date_to_pl(date_str: str) -> str:
    """Translates GEDCOM English date strings into clean Polish representation."""
    if not date_str:
        return ""

    result = date_str.strip()

    # Translate Month tokens (e.g. JAN -> sty, AUG -> sie)
    for en_m, pl_m in GEDCOM_MONTHS_PL.items():
        result = re.sub(rf"\b{en_m}\b", pl_m, result, flags=re.IGNORECASE)

    # Translate Modifier tokens (e.g. ABT -> ok., BEF -> przed, BET .. AND .. -> pomiędzy .. a ..)
    for en_mod, pl_mod in GEDCOM_MODIFIERS_PL.items():
        result = re.sub(rf"\b{en_mod}\b", pl_mod, result, flags=re.IGNORECASE)

    return result


def translate_tag_to_pl(tag: str) -> str:
    """Translates GEDCOM tag into human-readable Polish attribute name."""
    if not tag:
        return ""
    tag_clean = tag.upper().strip()
    return GEDCOM_TAGS_PL.get(tag_clean, tag)
