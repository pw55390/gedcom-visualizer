"""
Fuzzy Date Engine for Historical and Genealogical Records.

Handles exact, partial, range, approximate, and fuzzy dates.
Converts calendar dates (Gregorian/Julian) into Julian Day Numbers (JDN)
to allow fast indexing, range queries, and interval overlaps in SQLite.
"""

from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Optional, Tuple

from src.core.enums import DateModifier


MONTH_MAP = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
    "STZ": 1, "LUT": 2, "MARZ": 3, "KWI": 4, "MAJ": 5, "CZE": 6,
    "LIP": 7, "SIER": 8, "WRZ": 9, "PAŹ": 10, "LIS": 11, "GRU": 12
}

MONTH_NAMES_PL = [
    "", "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia"
]


def gregorian_to_jdn(year: int, month: int = 1, day: int = 1) -> int:
    """Converts a Gregorian date into Julian Day Number (JDN)."""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn


def jdn_to_gregorian(jdn: int) -> Tuple[int, int, int]:
    """Converts a Julian Day Number (JDN) back to a Gregorian (year, month, day) tuple."""
    f = jdn + 1401 + (((4 * jdn + 274274) // 146097) * 3) // 4 - 38
    e = 4 * f + 3
    g = (e % 1461) // 4
    h = 5 * g + 2
    day = (h % 153) // 5 + 1
    month = (h // 153 + 2) % 12 + 1
    year = e // 1461 - 4716 + (14 - month) // 12
    return year, month, day


@dataclass
class FuzzyDate:
    modifier: DateModifier = DateModifier.EXACT
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    
    # Second date for range / between bounds
    year_end: Optional[int] = None
    month_end: Optional[int] = None
    day_end: Optional[int] = None

    raw_text: str = ""
    jdn_min: Optional[int] = None
    jdn_max: Optional[int] = None

    def __post_init__(self):
        if self.jdn_min is None or self.jdn_max is None:
            self._compute_jdn_bounds()

    def _compute_jdn_bounds(self) -> None:
        """Calculates min and max JDN bounds based on date modifier and specificity."""
        if self.year is None:
            self.jdn_min = 0
            self.jdn_max = 3652425  # ~ Year 5000
            return

        y1 = self.year
        m1 = self.month if self.month else 1
        d1 = self.day if self.day else 1

        if self.month:
            # Last day of month estimation
            if self.month in [1, 3, 5, 7, 8, 10, 12]:
                d1_max = self.day if self.day else 31
            elif self.month in [4, 6, 9, 11]:
                d1_max = self.day if self.day else 30
            else:
                is_leap = (y1 % 4 == 0 and y1 % 100 != 0) or (y1 % 400 == 0)
                d1_max = self.day if self.day else (29 if is_leap else 28)
            m1_max = self.month
        else:
            m1_max = 12
            d1_max = 31

        jdn1 = gregorian_to_jdn(y1, m1, d1)
        jdn1_end = gregorian_to_jdn(y1, m1_max, d1_max)

        if self.modifier in (DateModifier.EXACT, DateModifier.TEXT_ONLY):
            self.jdn_min = jdn1
            self.jdn_max = jdn1_end
        elif self.modifier in (DateModifier.ABOUT, DateModifier.ESTIMATED, DateModifier.CALCULATED):
            # +/- 5 years tolerance for approximate dates
            self.jdn_min = gregorian_to_jdn(y1 - 5, 1, 1)
            self.jdn_max = gregorian_to_jdn(y1 + 5, 12, 31)
        elif self.modifier == DateModifier.BEFORE:
            self.jdn_min = 0
            self.jdn_max = jdn1
        elif self.modifier == DateModifier.AFTER:
            self.jdn_min = jdn1_end
            self.jdn_max = 3652425
        elif self.modifier in (DateModifier.BETWEEN, DateModifier.FROM_TO):
            self.jdn_min = jdn1
            if self.year_end:
                m2 = self.month_end if self.month_end else 12
                d2 = self.day_end if self.day_end else 31
                self.jdn_max = gregorian_to_jdn(self.year_end, m2, d2)
            else:
                self.jdn_max = jdn1_end

    @classmethod
    def parse(cls, date_str: str) -> "FuzzyDate":
        """Parses GEDCOM date strings or Polish standard date strings into FuzzyDate."""
        if not date_str or not date_str.strip():
            return cls(modifier=DateModifier.TEXT_ONLY, raw_text="")

        clean_str = date_str.strip().upper()

        # Check modifiers
        modifier = DateModifier.EXACT
        if clean_str.startswith("ABT ") or clean_str.startswith("OK. ") or clean_str.startswith("OKOŁO "):
            modifier = DateModifier.ABOUT
            clean_str = re.sub(r"^(ABT|OK\.|OKOŁO)\s+", "", clean_str)
        elif clean_str.startswith("EST "):
            modifier = DateModifier.ESTIMATED
            clean_str = re.sub(r"^EST\s+", "", clean_str)
        elif clean_str.startswith("CAL "):
            modifier = DateModifier.CALCULATED
            clean_str = re.sub(r"^CAL\s+", "", clean_str)
        elif clean_str.startswith("BEF ") or clean_str.startswith("PRZED "):
            modifier = DateModifier.BEFORE
            clean_str = re.sub(r"^(BEF|PRZED)\s+", "", clean_str)
        elif clean_str.startswith("AFT ") or clean_str.startswith("PO "):
            modifier = DateModifier.AFTER
            clean_str = re.sub(r"^(AFT|PO)\s+", "", clean_str)
        elif clean_str.startswith("BET ") or clean_str.startswith("MIĘDZY "):
            modifier = DateModifier.BETWEEN
            m_between = re.match(r"^(?:BET|MIĘDZY)\s+(.*?)\s+(?:AND|A)\s+(.*)$", clean_str)
            if m_between:
                d1 = cls._parse_single(m_between.group(1))
                d2 = cls._parse_single(m_between.group(2))
                return cls(
                    modifier=DateModifier.BETWEEN,
                    year=d1.year, month=d1.month, day=d1.day,
                    year_end=d2.year, month_end=d2.month, day_end=d2.day,
                    raw_text=date_str
                )

        parsed_single = cls._parse_single(clean_str)
        parsed_single.modifier = modifier
        parsed_single.raw_text = date_str
        parsed_single._compute_jdn_bounds()
        return parsed_single

    @classmethod
    def _parse_single(cls, s: str) -> "FuzzyDate":
        # Match "15 JAN 1920" or "15.01.1920" or "JAN 1920" or "1920"
        parts = s.split()
        day, month, year = None, None, None

        # Pattern: DD.MM.YYYY
        dot_match = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", s)
        if dot_match:
            return cls(
                year=int(dot_match.group(3)),
                month=int(dot_match.group(2)),
                day=int(dot_match.group(1))
            )

        for part in parts:
            if part.isdigit():
                val = int(part)
                if val > 31:
                    year = val
                elif day is None:
                    day = val
            elif part in MONTH_MAP:
                month = MONTH_MAP[part]

        return cls(year=year, month=month, day=day)

    def to_display_string(self, lang: str = "PL") -> str:
        """Returns localized human-readable representation of the date."""
        if not self.year and self.raw_text:
            return self.raw_text

        date_part = ""
        if self.day and self.month and self.year:
            if lang == "PL":
                month_name = MONTH_NAMES_PL[self.month] if 1 <= self.month <= 12 else str(self.month)
                date_part = f"{self.day} {month_name} {self.year} r."
            else:
                date_part = f"{self.day}/{self.month}/{self.year}"
        elif self.month and self.year:
            month_name = MONTH_NAMES_PL[self.month] if 1 <= self.month <= 12 else str(self.month)
            date_part = f"{month_name} {self.year} r." if lang == "PL" else f"{self.month}/{self.year}"
        elif self.year:
            date_part = f"{self.year} r." if lang == "PL" else str(self.year)

        prefix_map_pl = {
            DateModifier.ABOUT: "ok. ",
            DateModifier.ESTIMATED: "szac. ",
            DateModifier.CALCULATED: "oblicz. ",
            DateModifier.BEFORE: "przed ",
            DateModifier.AFTER: "po ",
        }

        if self.modifier in prefix_map_pl:
            return f"{prefix_map_pl[self.modifier]}{date_part}"

        if self.modifier == DateModifier.BETWEEN and self.year_end:
            d2 = FuzzyDate(year=self.year_end, month=self.month_end, day=self.day_end).to_display_string(lang)
            return f"między {date_part} a {d2}"

        return date_part

    def calculate_age_at(self, other_date: "FuzzyDate") -> Optional[int]:
        """Calculates age in full years relative to another date (e.g. birth to death)."""
        if not self.year or not other_date.year:
            return None
        age = other_date.year - self.year
        if self.month and other_date.month:
            if (other_date.month, other_date.day or 1) < (self.month, self.day or 1):
                age -= 1
        return max(0, age)
