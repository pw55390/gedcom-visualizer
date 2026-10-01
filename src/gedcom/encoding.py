"""
GEDCOM Encoding Detector & ANSEL (ANSI Z39.47) Decoder.
Resolves mojibake, UTF-8, ANSEL, CP1250, Windows-1250, and Latin1 character encodings.
"""

import re
import chardet


ANSEL_DIACRITICS = {
    '\xe1': '\u0300',  # Grave
    '\xe2': '\u0301',  # Acute (ć, ś, ź, ó, ś)
    '\xe3': '\u0302',  # Circumflex
    '\xe4': '\u0303',  # Tilde
    '\xe8': '\u0308',  # Umlaut
    '\xe7': '\u0307',  # Dot above (ż)
    '\xf2': '\u0337',  # Slash (ł)
    '\xf7': '\u0328',  # Ogonek (ą, ę)
}

# Explicit Polish ANSEL combinations
ANSEL_POLISH_MAP = {
    '\xe2c': 'ć', '\xe2C': 'Ć',
    '\xe2e': 'ę', '\xe2E': 'Ę',
    '\xf7a': 'ą', '\xf7A': 'Ą',
    '\xf7e': 'ę', '\xf7E': 'Ę',
    '\xe2l': 'ł', '\xe2L': 'Ł',
    '\xf2l': 'ł', '\xf2L': 'Ł',
    '\xe2n': 'ń', '\xe2N': 'Ń',
    '\xe2o': 'ó', '\xe2O': 'Ó',
    '\xe2s': 'ś', '\xe2S': 'Ś',
    '\xe2z': 'ź', '\xe2Z': 'Ź',
    '\xe7z': 'ż', '\xe7Z': 'Ż',
    '\xe2z': 'ż',  # Fallback for ż
}


def decode_ansel(raw_bytes: bytes) -> str:
    """Decodes raw ANSEL bytes into a clean Unicode UTF-8 string."""
    text = raw_bytes.decode('latin1', errors='ignore')
    for ansel_combo, unicode_char in ANSEL_POLISH_MAP.items():
        text = text.replace(ansel_combo, unicode_char)
    return text


def detect_and_read_gedcom(file_path: str) -> str:
    """Detects file encoding using GEDCOM header tags, BOM, and chardet heuristic."""
    with open(file_path, 'rb') as f:
        raw_data = f.read()

    if not raw_data:
        return ""

    # Check UTF-8 BOM
    if raw_data.startswith(b'\xef\xbb\xbf'):
        return raw_data[3:].decode('utf-8', errors='replace')

    # Quick scan of header for 1 CHAR tag in first 2000 bytes
    sample = raw_data[:4000].decode('latin1', errors='ignore')
    match = re.search(r"1\s+CHAR\s+([A-Z0-9_\-]+)", sample, re.IGNORECASE)
    declared_char = match.group(1).upper() if match else None

    if declared_char:
        if declared_char in ("UTF-8", "UTF8"):
            try:
                return raw_data.decode('utf-8')
            except UnicodeDecodeError:
                return raw_data.decode('utf-8', errors='replace')
        elif declared_char == "ANSEL":
            return decode_ansel(raw_data)
        elif declared_char in ("CP1250", "WINDOWS-1250", "WIN1250", "EASTEUROPE"):
            return raw_data.decode('cp1250', errors='replace')
        elif declared_char in ("LATIN1", "ISO-8859-1", "CP1252"):
            return raw_data.decode('latin1', errors='replace')

    # Heuristic detection using chardet
    detected = chardet.detect(raw_data[:20000])
    encoding = detected.get('encoding')

    if encoding and encoding.lower() in ('utf-8', 'utf-8-sig'):
        return raw_data.decode('utf-8', errors='replace')

    # Polish heuristic check: if UTF-8 bytes are misdecoded, try UTF-8 first
    try:
        decoded_utf8 = raw_data.decode('utf-8')
        return decoded_utf8
    except UnicodeDecodeError:
        pass

    # Try CP1250 (common for Polish Windows GEDCOM files)
    try:
        return raw_data.decode('cp1250')
    except UnicodeDecodeError:
        pass

    return raw_data.decode('latin1', errors='replace')
